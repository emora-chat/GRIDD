
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
        self.auxiliary_state = {'turn_index': 0}

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
        self.elit_dp = ElitDPToLogic(knowledge_base, template_file)

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
        parse_dict = load(response.json()["context_manager"])['elit_results']

        wm = self.dialogue_intcore.working_memory

        exclusions = {'expr', 'def', 'ref',
                      'span', 'expression', 'predicate', 'datetime'}

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
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=True))

        # todo - no acknowledgement predicates found (i bought a house, i love it)

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
        # merge_sets = self.get_merge_sets_from_pairs(node_merges)
        self.dialogue_intcore.merge(node_merges)

        print('\n' + '#'*10)
        print('After Merges')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=True))

        # Knowledge pull
        knowledge_by_source = self.dialogue_intcore.pull_knowledge(limit=100, num_pullers=100, association_limit=10, subtype_limit=10)
        for pred, sources in knowledge_by_source.items():
            self.dialogue_intcore.consider([pred], associations=sources)
        types = self.dialogue_intcore.pull_types()
        self.dialogue_intcore.consider(types)
        self.dialogue_intcore.operate()

        print('\n' + '#'*10)
        print('After Knowledge Pull')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=True))

        # Inferences
        inferences = self.dialogue_intcore.infer()
        self.dialogue_intcore.apply_inferences(inferences)
        self.dialogue_intcore.operate()
        self.dialogue_intcore.gather_all_nlu_references()
        self.dialogue_intcore.gather_all_assertion_links()

        print('\n' + '#'*10)
        print('After Inferences')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=True))

        # Feature update
        self.dialogue_intcore.update_confidence()
        self.dialogue_intcore.update_salience()

        print('\n' + '#'*10)
        print('After Feature Update')
        print('#' * 10)
        for concept, features in self.dialogue_intcore.working_memory.features.items():
            if wm.has(predicate_id=concept) and wm.type(concept) not in {'expr', 'ref', 'def'}:
                sig = wm.predicate(concept)
                if sig[0] not in exclusions and sig[1] not in exclusions and sig[2] not in exclusions:
                    print(f'{sig}: s({features.get(SALIENCE, 0)}) c({features.get(CONFIDENCE, 0)}) cv({features.get(COVER, 0)})')

        # Reference resolution
        reference_pairs = self.dialogue_intcore.resolve() # todo - what if there is more than one matching reference??
        # reference_sets = self.get_merge_sets_from_pairs(reference_pairs)
        self.dialogue_intcore.merge(reference_pairs)

        print('\n' + '#'*10)
        print('After Reference Resolution')
        print('#' * 10)
        print(self.dialogue_intcore.working_memory.pretty_print(exclusions=exclusions, typeinfo=True))
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
                                          subj_emodifiers={'time', 'question', 'mode'}, obj_emodifiers={'possess'})
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
            spoken_predicates.update([main[3]] + [pred[3] for pred in exps])
        self.assign_cover(wm, concepts=spoken_predicates)

        ack_results = self.produce_acknowledgment(aux_state, responses)
        gen_results = self.produce_generic(responses)
        response = self.response_assembler(aux_state, ack_results, gen_results)

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
            self.auxiliary_state['turn_index'] += 1

if __name__ == '__main__':
    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]
    wm = [join('GRIDD', 'resources', 'kg_files', 'wm')]
    ITERATION = 2

    chatbot = Chatbot(*kb, inference_rules=rules, starting_wm=wm)
    chatbot.chat()