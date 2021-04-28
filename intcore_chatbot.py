
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
from GRIDD.modules.response_selection_salience import ResponseSelectionSalience
from GRIDD.modules.response_expansion import ResponseExpansion
from GRIDD.modules.responsegen_by_rules import ResponseRules
from GRIDD.modules.responsegen_by_model import ResponseGeneration
from GRIDD.modules.response_assembler import ResponseAssembler

from GRIDD.chatbot_server import load
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component
from GRIDD.utilities import collect
from GRIDD.globals import *

from os.path import join
import json, requests, time
from itertools import chain
from collections import defaultdict

DEBUG = True
EXCL = {'expr', SPAN_REF, SPAN_DEF, USER_AWARE,
        'span', 'expression', 'predicate', 'datetime'}
TYPEINFO = False

class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base, inference_rules, starting_wm=None, device='cpu'):
        self.auxiliary_state = {'turn_index': -1}

        compiler = ConceptCompiler()
        predicates, metalinks, metadatas = compiler.compile(collect(*knowledge_base))
        knowledge_base = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
                                      namespace='kb')
        dialogue_inference = InferenceEngine(collect(*inference_rules))
        working_memory = None
        if starting_wm is not None:
            working_memory = ConceptGraph(collect(*starting_wm), namespace='wm', supports={AND_LINK: False})
        self.dialogue_intcore = IntelligenceCore(knowledge_base=knowledge_base,
                                            working_memory=working_memory,
                                            inference_engine=dialogue_inference)

        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        s = time.time()
        self.elit_dp = ElitDPToLogic(knowledge_base, template_file)
        print('Parse2Logic load: %.2f'%(time.time()-s))

        self.response_selection = ResponseSelectionSalience()
        self.response_expansion = ResponseExpansion(knowledge_base)
        self.produce_acknowledgment = ResponseRules()
        self.produce_generic = ResponseGeneration()
        self.response_assembler = ResponseAssembler()


    def respond(self, user_utterance, debug):
        input_dict = {"text": [user_utterance, None],
                      "aux_state": [self.auxiliary_state, self.auxiliary_state],
                      "conversationId": 'local'}
        response = requests.post('http://cobot-LoadB-2W3OCXJ807QG-1571077302.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        results = load(response.json()["context_manager"])
        parse_dict = results['elit_results']
        self.auxiliary_state = results["aux_state"]
        wm = self.dialogue_intcore.working_memory

        #########################
        ### Dialogue Pipeline ###
        #########################

        # NLU Preprocessing
        mentions, merges = self.elit_dp(parse_dict)

        if debug:
            print()
            for span, graph in mentions.items():
                print(span)
                print('-'*10)
                print(graph.pretty_print())
                print()

            print()
            for merge in merges:
                print(merge)

        # Mentions
        namespace = list(mentions.items())[0][1].id_map() if len(mentions) > 0 else "ment_"
        mega_mention_graph = ConceptGraph(namespace=namespace)
        for span, mention_graph in mentions.items():
            ((focus, t, o, i,),) = list(mention_graph.predicates(predicate_type='focus'))
            center_pred = list(mention_graph.predicates(predicate_type='center'))
            if len(center_pred) > 0: ((center, t, o, i,),) = center_pred
            else: ((center, t, o, i,),) = list(mention_graph.predicates(predicate_type='link'))
            mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus', 'center', 'cover'})
            mega_mention_graph.add(span, 'ref', focus)
            mega_mention_graph.add(span, 'type', 'span')
            if not span.startswith('__linking__'):
                mega_mention_graph.add(span, 'def', center)
        self.assign_cover(mega_mention_graph)
        self.dialogue_intcore.consider(mega_mention_graph)

        if debug:
            print('\n' + '#'*10)
            print('After Mentions')
            print('#' * 10)
            print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))

        # Merges
        node_merges = []
        for (span1, pos1), (span2, pos2) in merges:
            # if no mention for span, no merge possible
            if wm.has(span1) and wm.has(span2):
                (concept1,) = wm.objects(span1, 'ref')
                concept1 = self._follow_path(concept1, pos1, wm)
                (concept2,) = wm.objects(span2, 'ref')
                concept2 = self._follow_path(concept2, pos2, wm)
                node_merges.append((concept1, concept2))
        self.dialogue_intcore.merge(node_merges)

        if debug:
            print('\n' + '#'*10)
            print('After Merges')
            print('#' * 10)
            print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))

        # Knowledge pull
        knowledge_by_source = self.dialogue_intcore.pull_knowledge(limit=100, num_pullers=100, association_limit=10, subtype_limit=10)
        for pred, sources in knowledge_by_source.items():
            if not wm.has(*pred):
                self.dialogue_intcore.consider([pred], namespace=self.dialogue_intcore.knowledge_base._ids, associations=sources)
                self.dialogue_intcore.working_memory.metagraph.update(self.dialogue_intcore.knowledge_base.metagraph,
                                                                      self.dialogue_intcore.knowledge_base.metagraph.features,
                                                                      concepts=[pred[3]])
        types = self.dialogue_intcore.pull_types()
        for type in types:
            if not wm.has(*type):
                self.dialogue_intcore.consider([type], associations=type[0])
        self.dialogue_intcore.operate()

        if debug:
            print('\n' + '#'*10)
            print('After Knowledge Pull')
            print('#' * 10)
            print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))

        print('\n' + '#'*10)
        print('Before Inference')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))
        print()

        for iteration in range(2):
            if debug:
                print('\n<< INFERENCE ITERATION %d >> '%iteration)
            # Inferences
            inferences = self.dialogue_intcore.infer()
            self.dialogue_intcore.apply_inferences(inferences)
            self.dialogue_intcore.operate()
            self.dialogue_intcore.convert_metagraph_span_links(REF_SP, [REF, VAR])
            self.dialogue_intcore.convert_metagraph_span_links(DP_SUB, [ASS_LINK])
            self.dialogue_intcore.convert_metagraph_span_links(GROUP_DEF_SP, [GROUP_DEF, VAR])
            self.dialogue_intcore.convert_metagraph_span_links(GROUP_PROP_SP, [GROUP_PROP, VAR])
            self.dialogue_intcore.learn_generics()

            if debug:
                print('\n' + '#'*10)
                print('After Inferences')
                print('#' * 10)
                print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))

            # Feature update
            self.dialogue_intcore.update_confidence('user')
            self.dialogue_intcore.update_confidence('emora')
            self.dialogue_intcore.update_salience()

            if debug:
                print('\n' + '#'*10 + '\nAfter Feature Update\n' + '#' * 10)
                self.print_features()

            # Reference resolution
            reference_sets = self.dialogue_intcore.resolve()
            reference_pairs = self.identify_reference_merges(reference_sets)
            if len(reference_pairs) > 0:
                self.merge_references(reference_pairs)

            # Fragment Request Resolution:
            #   most salient type-compatible user concept from current turn fills most salient emora request
            emora_requests = [pred for pred in wm.predicates('emora', 'question') if wm.has(pred[3], USER_AWARE)]
            if len(emora_requests) > 0:
                salient_emora_request = max(emora_requests,
                                            key=lambda pred: wm.features.get(pred[3], {}).get(SALIENCE, 0))
                request_focus = salient_emora_request[2]
                fragment_request_merges = []
                current_user_spans = [s for s in wm.subtypes_of("span") if s != "span" and int(wm.features[s]["span_data"].turn) == self.auxiliary_state["turn_index"]]
                current_user_concepts = {o for s in current_user_spans for o in chain(wm.objects(s, SPAN_REF), wm.objects(s, SPAN_DEF))}
                if wm.has(predicate_id=request_focus): # special case - y/n question requires yes/no fragment as answer (or full resolution from earlier in pipeline)
                    indicator_preds = [p[3] for p in list(wm.predicates('user', AFFIRM)) + list(wm.predicates('user', REJECT))]
                    options = set(indicator_preds).intersection(current_user_concepts)
                    if len(indicator_preds) > 0:
                        max_indicator = max(options, key=lambda p: wm.features.get(p[3], {}).get(SALIENCE, 0))
                        fragment_request_merges.append((wm.object(max_indicator), request_focus))
                else:
                    types = wm.types()
                    request_focus_types = types[request_focus] - {request_focus}
                    salient_concepts = sorted(current_user_concepts, key=lambda c: wm.features.get(c, {}).get(SALIENCE, 0), reverse=True)
                    for c in salient_concepts:
                        if c != request_focus and request_focus_types.issubset(types[c] - {c}) and not wm.metagraph.out_edges(c, REF): # if user concept is a reference, dont treat as answer fragment
                            fragment_request_merges.append((c, request_focus))
                            break
                if len(fragment_request_merges) > 0:
                    # set salience of all request predicates to salience of fragment
                    fragment = fragment_request_merges[0][0]
                    ref_links = [e for e in wm.metagraph.out_edges(request_focus) if e[2] == REF and wm.has(predicate_id=e[1])]
                    for s, t, l in ref_links:
                        wm.features.setdefault(t, {})[SALIENCE] = wm.features.setdefault(fragment, {}).get(SALIENCE, 0)
                        # wm.features[t][BASE] = True todo - check if the BASE indication matters here
                self.merge_references(fragment_request_merges)
                self.dialogue_intcore.operate()

            if debug:
                print('\n' + '#'*10)
                print('After Reference Resolution')
                print('#' * 10)
                print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))
                print()

        print('\n' + '#'*10)
        print('After Inference')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=EXCL, typeinfo=TYPEINFO))
        print()

        # End of user turn -> decay salience
        self.dialogue_intcore.decay_salience()

        if debug:
            print('\n' + '#' * 10 + '\nEnd User Turn\n' + '#' * 10)
            self.print_features()

        # Start of emora turn

        # Response selection
        aux_state, selections = self.response_selection(self.auxiliary_state, wm)

        print('\n' + '#'*10)
        print('Response Selections')
        print('#' * 10)
        for selection in selections:
            print(selection)
        print()

        responses, updated_wm = self.response_expansion(selections, wm)

        ack_results = self.produce_acknowledgment(aux_state, responses)

        gen_results = self.produce_generic(responses)
        try: # use remote nlg module
            input_dict = {"expanded_response_predicates": [responses, None],
                          "conversationId":  'local'}
            response = requests.post('http://cobot-LoadB-1L3YPB9TGV71P-1610005595.us-east-1.elb.amazonaws.com',
                                     data=json.dumps(input_dict),
                                     headers={'content-type': 'application/json'},
                                     timeout=3.0)
            response = response.json()
            if "performance" in response:
                del response["performance"]
                del response["error"]
            gen_results = json.loads(response["nlg_responses"])
        except Exception as e:
            print('Failed! %s'%e)

        response = self.response_assembler(aux_state, ack_results, gen_results)

        # end of emora turn -> update salience, then decay and prune
        self.dialogue_intcore.update_salience()
        self.dialogue_intcore.decay_salience()
        self.dialogue_intcore.prune_predicates_of_type({AFFIRM, REJECT})
        self.dialogue_intcore.prune_attended(keep=200)

        if debug:
            print('\n' + '#' * 10 + '\nEnd Emora Turn\n' + '#' * 10)
            self.print_features()

        self.auxiliary_state = aux_state

        return response

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        elif pos == 'type':
            return working_memory.type(concept)
        return concept

    def get_merge_sets_from_pairs(self, pairs):
        merge_sets = {}
        for a, b in pairs:
            existing = {a, b}
            if a in merge_sets:
                existing.update(merge_sets[a])
            if b in merge_sets:
                existing.update(merge_sets[b])
            for n in existing:
                merge_sets[n] = existing
        return merge_sets

    def identify_reference_merges(self, reference_dict):
        pairs_to_merge = []
        for ref_node, compatibilities in reference_dict.items():
            resolution_options = []
            for ref_match, constraint_matches in compatibilities.items():
                if self.dialogue_intcore.working_memory.metagraph.out_edges(ref_match, REF):
                    # found other references that match; merge all
                    pairs_to_merge.extend([(ref_match, ref_node)] + constraint_matches)
                else:
                    # found resolution to reference; merge only one
                    resolution_options.append(ref_match)
            if len(resolution_options) > 0:
                salient_resol = max(resolution_options,
                                    key=lambda x: self.dialogue_intcore.working_memory.features.get(x, {}).get(SALIENCE, 0))
                pairs_to_merge.extend([(salient_resol, ref_node)] + compatibilities[salient_resol])
        return pairs_to_merge

    def merge_references(self, reference_pairs):
        for match_node, ref_node in reference_pairs:
            # identify user answers to emora requests and remove request bipredicate
            if self.dialogue_intcore.working_memory.has('emora', 'question', ref_node) \
                    and not self.dialogue_intcore.working_memory.metagraph.out_edges(match_node, REF):
                self.dialogue_intcore.working_memory.remove('emora', 'question', ref_node)
        self.dialogue_intcore.merge(reference_pairs)

    def identify_request_resolutions(self, spoken_predicates):
        # identify emora answers to user requests and remove request bipredicate
        for s, t, o, i in spoken_predicates:
            if s == 'user' and t == 'question':
                self.dialogue_intcore.working_memory.remove(s, t, o, i)

    def assign_cover(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if not graph.has(predicate_id=concept) or graph.type(concept) not in PRIM:
                graph.add(concept, USER_AWARE)

    def print_features(self):
        wm = self.dialogue_intcore.working_memory
        ls = []
        excl = set(EXCL)
        excl.add('type')
        for concept, features in wm.features.items():
            if wm.has(predicate_id=concept):
                sig = wm.predicate(concept)
                if sig[0] not in excl and sig[1] not in excl and sig[2] not in excl:
                    sa, cf, ucf, cv = features.get(SALIENCE, 0), features.get(CONFIDENCE, 0), features.get(UCONFIDENCE, 0), wm.has(concept, USER_AWARE)
                    if sig[2] is not None:
                        rep = f'{sig[3]}/{sig[1]}({sig[0]},{sig[2]})'
                    else:
                        rep = f'{sig[3]}/{sig[1]}({sig[0]})'
                    ls.append((f'{rep:40}: s({sa:.2f}) c({cf:.2f}) uc({ucf:.2f}) cv({cv:.2f})', sa))
        for pr, sa in sorted(ls, key=lambda x: x[1], reverse=True):
            print(pr)

    def chat(self, debug):
        utterance = input('User: ')
        while utterance != 'q':
            s = time.time()
            response = self.respond(utterance, debug=debug)
            elapsed = time.time() - s
            print('[%.6f s] %s\n' % (elapsed, response))
            utterance = input('User: ')
            # self.auxiliary_state['turn_index'] += 1

if __name__ == '__main__':

    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]
    wm = [join('GRIDD', 'resources', 'kg_files', 'wm')]
    ITERATION = 2

    chatbot = Chatbot(*kb, inference_rules=rules, starting_wm=None)
    chatbot.chat(debug=DEBUG)