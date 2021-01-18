from framework import Framework
from components.aggregator import Aggregator
from modules.mention_identification import BaseMentionIdentification
from modules.merge import BaseNodeMerge
from modules.inference import BaseInference
from modules.response_selection import BaseResponseSelection
from modules.response_expansion import BaseResponseExpansion
from modules.response_generation import BaseResponseGeneration
from modules.mention_bridge import BaseMentionBridge
from modules.merge_bridge import BaseMergeBridge
from modules.inference_bridge import BaseInferenceBridge

from os.path import join

from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory
from data_structures.concept_graph import ConceptGraph

from elit.client import Client
from modules.elit_dp_to_logic_model import ElitDPToLogic, NODES
from modules.mention_identification_dp import MentionsDP
from modules.merge_dp import NodeMergeDP
from modules.inference_prolog import PrologInference

import time
from os.path import join

class First(Aggregator):
    def run(self, input, working_memory):
        outputs = self.branch.run(input, working_memory)
        selection = list(outputs.items())[0]
        return selection[1]

def check_continue(stage, input):
    """
    :param stage: the Framework stage calling this function
    :param input: True or False value indicating whether to continue
    :return:
    """
    return input

def run_twice(stage, input):
    if 'count' not in stage.iteration_vars:
        stage.iteration_vars['count'] = 0
    stage.iteration_vars['count'] += 1
    if stage.iteration_vars['count'] > 2:
        return False
    return True

def build_dm(kb, debug=True):
    if debug:
        print('Building dialogue pipeline...')
    dm = Framework('Emora')

    elit_model = Client('http://0.0.0.0:8000')
    template_starter_predicates = [(n, 'is_type') for n in NODES]
    template_file = join('data_structures', 'kg_files', 'elit_dp_templates.kg')
    elit_dp = ElitDPToLogic("elit dp", kb, elit_model, template_starter_predicates, template_file)
    dm.add_preprocessing_module('dependency parse', elit_dp)

    dm.add_mention_model({'model': MentionsDP('dp mentions')})
    dm.add_merge_model({'model': NodeMergeDP('dp merge')})
    dm.add_inference_model({'model': PrologInference('prolog inference',
                                                     [join('data_structures', 'kg_files', 'test_inferences.kg')])})
    # dm.add_inference_model({'model': BaseInference('base inference')})
    dm.add_selection_model({'model': BaseResponseSelection('base selection')})
    dm.add_expansion_model({'model': BaseResponseExpansion('base expansion')})
    dm.add_generation_model({'model': BaseResponseGeneration('base generation')})

    dm.add_mention_aggregation(First)
    dm.add_merge_aggregation(First)
    dm.add_inference_aggregation(First)

    dm.add_mention_bridge(BaseMentionBridge('mention bridge'))
    dm.add_merge_bridge(BaseMergeBridge('merge bridge',
                                        threshold_score=0.2))
    dm.add_inference_bridge(BaseInferenceBridge('base inference bridge'))

    dm.add_merge_iteration(check_continue)
    dm.add_merge_inference_iteration(run_twice)

    dm.build_framework()

    if debug:
        print('Built!\n')

    return dm

if __name__ == '__main__':
    kb = KnowledgeBase(join('data_structures', 'kg_files', 'framework_test.kg'))
    dm = build_dm(kb)
    working_memory = WorkingMemory(kb)

    asr_hypotheses = [
        {'text': 'i bought a red house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'red', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80, 4: 0.80}
         }
    ]

    s = time.time()
    print('UTTER: ', asr_hypotheses[0]['text'])
    output = dm.run(asr_hypotheses, working_memory)
    elapsed = time.time() - s
    print('[%.6f s] %s'%(elapsed, output))