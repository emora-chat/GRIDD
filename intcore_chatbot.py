
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic

from GRIDD.chatbot_server import load
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component
from GRIDD.utilities import collect

from os.path import join
import json, requests, time

class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base, inference_rules, starting_wm=None, device='cpu'):
        self.auxiliary_state = {'turn_index': 0}

        knowledge_base = ConceptGraph(collect(*knowledge_base), namespace='kb')
        dialogue_inference = InferenceEngine(collect(*inference_rules))
        working_memory = None
        if starting_wm is not None:
            working_memory = WorkingMemory(starting_wm)
        self.dialogue_intcore = IntelligenceCore(knowledge_base=knowledge_base,
                                            working_memory=working_memory,
                                            inference_engine=dialogue_inference)

        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        self.elit_dp = ElitDPToLogic(knowledge_base, template_file)


    def respond(self, user_utterance):
        input_dict = {"text": [user_utterance, None],
                      "aux_state": [None, None],
                      "conversationId": 'local'}
        response = requests.post('http://cobot-LoadB-2W3OCXJ807QG-1571077302.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        parse_dict = load(response.json()["context_manager"])['elit_results']

        wm = self.dialogue_intcore.working_memory

        mentions, merges  = self.elit_dp(parse_dict)

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

        self.dialogue_intcore.accept(mega_mention_graph)

        node_merges = []
        for (span1, pos1), (span2, pos2) in merges:
            # if no mention for span, no merge possible
            if wm.has(span1) and wm.has(span2):
                (concept1,) = wm.objects(span1, 'ref')
                concept1 = self._follow_path(concept1, pos1, wm)
                (concept2,) = wm.objects(span2, 'ref')
                concept2 = self._follow_path(concept2, pos2, wm)
                node_merges.append((concept1, concept2))

        # gather sets of merging nodes where nodes that merge together are in the same set
        # intcore merge()
        # intcore pull_knowledge() and pull_types()
        # inference
        # salience and confidence propogation
        # response selection
        # response expansion
        # response generation

        return

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        elif pos == 'type':
            return working_memory.type(concept)
        return concept

    def chat(self):
        utterance = input('User: ')
        while utterance != 'q':
            s = time.time()
            response = self.respond(utterance)
            elapsed = time.time() - s
            print('[%.6f s] %s' % (elapsed, response))
            utterance = input('User: ')

if __name__ == '__main__':
    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]
    ITERATION = 2

    chatbot = Chatbot(*kb, inference_rules=rules)
    chatbot.chat()