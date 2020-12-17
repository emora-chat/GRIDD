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

from modules.allenai_dp_to_logic_model import AllenAIToLogic, POS_NODES, NODES
from allennlp.predictors.predictor import Predictor
from os.path import join

from knowledge_base.knowledge_graph import KnowledgeGraph
from knowledge_base.working_memory import WorkingMemory
from knowledge_base.concept_graph import ConceptGraph
from modules.mention_identification_lexicon import MentionsByLexicon
from modules.merge_dp import NodeMergeDP

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

if __name__ == '__main__':
    dm = Framework('Emora')

    kb = KnowledgeGraph(join('knowledge_base', 'kg_files', 'framework_test.kg'))

    template_base = KnowledgeGraph(nodes=POS_NODES + NODES, loading_kb=False)
    for n in POS_NODES + NODES:
        template_base._concept_graph.add_monopredicate(n, 'is_type')
    dependency_parser = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
    template_file = join('knowledge_base', 'kg_files', 'allen_dp_templates.txt')

    dm.add_preprocessing_module('dependency parse',
                                AllenAIToLogic("allen dp", kb, dependency_parser,
                                               template_base, template_file))

    dm.add_mention_model({'model': MentionsByLexicon('lexicon mentions')})
    dm.add_merge_model({'model': NodeMergeDP('dependency parse merge')})
    dm.add_inference_model({'model': BaseInference('base inference')})
    dm.add_selection_model({'model': BaseResponseSelection('base selection')})
    dm.add_expansion_model({'model': BaseResponseExpansion('base expansion')})
    dm.add_generation_model({'model': BaseResponseGeneration('base generation')})

    dm.add_mention_aggregation(First)
    dm.add_merge_aggregation(First)
    dm.add_inference_aggregation(First)

    dm.add_mention_bridge(BaseMentionBridge('base mention bridge'))
    dm.add_merge_bridge(BaseMergeBridge('base merge bridge', threshold_score=0.2))
    dm.add_inference_bridge(BaseInferenceBridge('base inference bridge'))

    dm.add_merge_iteration(check_continue)
    dm.add_merge_inference_iteration(run_twice)

    dm.build_framework()

    wm = ConceptGraph(nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)

    asr_hypotheses = [
        {'text': 'i bought a red house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'red', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80, 4: 0.80}
         }
    ]

    s = time.time()
    output = dm.run(asr_hypotheses, working_memory)
    elapsed = time.time() - s
    print('[%.6f s] %s'%(elapsed, output))