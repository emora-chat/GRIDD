
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic

from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component
from GRIDD.data_structures.span import Span
from GRIDD.utilities import collect

from os.path import join
import json, requests, time

class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base, inference_rules, starting_wm=None, device='cpu'):
        knowledge_base = ConceptGraph(collect(*knowledge_base))
        dialogue_inference = InferenceEngine(collect(*inference_rules))
        working_memory = None
        if starting_wm is not None:
            working_memory = WorkingMemory(starting_wm)
        dialogue_intcore = IntelligenceCore(knowledge_base=knowledge_base,
                                            working_memory=working_memory,
                                            inference_engine=dialogue_inference)

        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        parse_inference = InferenceEngine(template_file)
        parse_intcore = IntelligenceCore(knowledge_base=knowledge_base,
                                         inference_engine=parse_inference)

        elit_dp = c(ElitDPToLogic(parse_intcore))

        self.pipeline = Pipeline(
            ('parse_dict') > elit_dp > ('dp_mentions', 'dp_merges'),
            tags ={},
            outputs=[]
        )

        self.auxiliary_state = {'turn_index': 0}

    def respond(self, user_utterance):
        input_dict = {"text": [user_utterance, None],
                      "conversationId": 'local'}
        response = requests.post('http://cobot-LoadB-2W3OCXJ807QG-1571077302.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        parse_dict = json.loads(response.json()["context_manager"]['elit_results'])

        outputs = self.pipeline(
            parse_dict,
            2
        )

        return outputs

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