
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
from GRIDD.modules.response_selection_salience import ResponseSelectionSalience
from GRIDD.modules.response_acknowledgment import ResponseAcknowledgment
from GRIDD.modules.response_generation import ResponseGeneration
from GRIDD.modules.response_assembler import ResponseAssembler

from GRIDD.chatbot_server import load
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component
from GRIDD.utilities import collect
from GRIDD.globals import *

from os.path import join
import json, requests, time
from collections import defaultdict

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
        self.produce_acknowledgment = ResponseAcknowledgment()
        self.produce_generic = ResponseGeneration()
        self.response_assembler = ResponseAssembler()


    def respond(self, user_utterance):
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

        exclusions = {'expr', 'def', 'ref',
                      'span', 'expression', 'predicate', 'datetime'}
        typeinfo = False
        #########################
        ### Dialogue Pipeline ###
        #########################

        # NLU Preprocessing
        mentions, merges = self.elit_dp(parse_dict)

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

        print('\n' + '#'*10)
        print('After Mentions')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=typeinfo))

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

        print('\n' + '#'*10)
        print('After Merges')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=typeinfo))

        # Knowledge pull
        knowledge_by_source = self.dialogue_intcore.pull_knowledge(limit=100, num_pullers=100, association_limit=10, subtype_limit=10)
        for pred, sources in knowledge_by_source.items():
            self.dialogue_intcore.consider([pred], namespace=self.dialogue_intcore.knowledge_base._ids, associations=sources)
        types = self.dialogue_intcore.pull_types()
        for type in types:
            self.dialogue_intcore.consider([type], associations=type[0])
        self.dialogue_intcore.operate()

        print('\n' + '#'*10)
        print('After Knowledge Pull')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=typeinfo))

        # Inferences
        inferences = self.dialogue_intcore.infer()
        self.dialogue_intcore.apply_inferences(inferences)
        self.dialogue_intcore.operate()
        self.dialogue_intcore.gather_all_nlu_references()
        self.dialogue_intcore.gather_all_assertion_links()

        print('\n' + '#'*10)
        print('After Inferences')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=typeinfo))

        # Feature update
        self.dialogue_intcore.update_confidence()
        self.dialogue_intcore.update_salience()

        print('\n' + '#'*10)
        print('After Feature Update')
        print('#' * 10)
        for concept, features in self.dialogue_intcore.working_memory.features.items():
            if wm.has(predicate_id=concept) and wm.type(concept) not in {'expr', 'ref', 'def', 'type'}:
                sig = wm.predicate(concept)
                if sig[0] not in exclusions and sig[1] not in exclusions and sig[2] not in exclusions:
                    print(f'{sig}: s({features.get(SALIENCE, 0)}) c({features.get(CONFIDENCE, 0)}) cv({features.get(COVER, 0)})')

        # Reference resolution
        reference_sets = self.dialogue_intcore.resolve()
        reference_pairs = self.identify_reference_merges(reference_sets)
        if len(reference_pairs) > 0:
            self.merge_references(reference_pairs)

        # Fragment Request Resolution:
        #   most salient type-compatible user concept from current turn fills most salient emora request
        emora_requests = [pred for pred in wm.predicates('emora', 'question') if wm.features.get(pred[3], {}).get(COVER, 0) == 1.0]
        if len(emora_requests) > 0:
            salient_emora_request = max(emora_requests,
                                        key=lambda pred: wm.features.get(pred[3], {}).get(SALIENCE, 0))
            request_focus = salient_emora_request[2]
            fragment_request_merges = []
            special_case_satisfied = False
            current_user_spans = [s for s in wm.subtypes_of("span") if s != "span" and int(wm.features[s]["span_data"].turn) == self.auxiliary_state["turn_index"]]
            current_user_concepts = {o for s in current_user_spans for o in wm.objects(s, "ref")}
            if wm.has(predicate_id=request_focus): # special case - y/n question prioritizes yes/no answer
                indicator_preds = [p[3] for p in list(wm.predicates('user', AFFIRM)) + list(wm.predicates('user', REJECT))]
                options = set(indicator_preds).intersection(current_user_concepts)
                if len(indicator_preds) > 0:
                    max_indicator = max(options, key=lambda p: wm.features.get(p[3], {}).get(SALIENCE, 0))
                    fragment_request_merges.append((wm.object(max_indicator), request_focus))
                    special_case_satisfied = True
            if not special_case_satisfied:
                types = wm.types()
                request_focus_types = types[request_focus] - {request_focus}
                salient_concepts = sorted(current_user_concepts, key=lambda c: wm.features.get(c, {}).get(SALIENCE, 0), reverse=True)
                for c in salient_concepts:
                    if c != request_focus and request_focus_types.issubset(types[c] - {c}):
                        fragment_request_merges.append((c, request_focus))
                        break
            self.merge_references(fragment_request_merges)
            self.dialogue_intcore.operate()

        print('\n' + '#'*10)
        print('After Reference Resolution')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=typeinfo))
        print()

        # Response selection
        aux_state, selections = self.response_selection(self.auxiliary_state, wm)

        print('\n' + '#'*10)
        print('Response Selections')
        print('#' * 10)
        for selection in selections:
            print(selection)
        print()

        responses = []
        for predicate, generation_type in selections:
            if generation_type == 'nlg':
                expansions = wm.structure(predicate[3],
                                          subj_emodifiers={'time', 'mode'}, obj_emodifiers={'possess', 'question'})
                responses.append((predicate, expansions, generation_type))
            elif generation_type in {"ack_conf", "ack_emo"}:
                responses.append((predicate, [], generation_type))
            elif generation_type == "backup":
                cg = ConceptGraph(namespace='bu_', predicates=predicate[1])
                mapped_ids = wm.concatenate(cg)
                main_pred = mapped_ids[predicate[0][3]]
                main_pred_sig = wm.predicate(main_pred)
                exp_preds = [mapped_ids[pred[3]] for pred in predicate[1]]
                exp_pred_sigs = [wm.predicate(pred) for pred in exp_preds if pred != main_pred]
                responses.append((main_pred_sig, exp_pred_sigs, generation_type))
        spoken_predicates = set()
        for main, exps, _ in responses:
            # expansions contains main predicate too
            spoken_predicates.update([pred[3] for pred in exps])
            self.identify_request_resolutions(exps)
        self.assign_cover(wm, concepts=spoken_predicates)

        ack_results = self.produce_acknowledgment(aux_state, responses)
        gen_results = self.produce_generic(responses)
        response = self.response_assembler(aux_state, ack_results, gen_results)

        self.dialogue_intcore.decay_salience()
        self.dialogue_intcore.prune_predicates_of_type({AFFIRM, REJECT})
        self.dialogue_intcore.prune_attended(keep=200)
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
            if graph.has(predicate_id=concept):
                graph.features[concept][COVER] = 1.0

    def chat(self):
        utterance = input('User: ')
        while utterance != 'q':
            s = time.time()
            response = self.respond(utterance)
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

    chatbot = Chatbot(*kb, inference_rules=rules, starting_wm=wm)
    chatbot.chat()