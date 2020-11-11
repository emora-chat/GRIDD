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

class First(Aggregator):
    def run(self, input, graph):
        outputs = self.branch.run(input)
        selection = list(outputs.items())[0]
        return selection[1]

if __name__ == '__main__':
    dm = Framework('Emora')

    dm.add_mention_model({'model': BaseMentionIdentification('base mention')})
    dm.add_merge_model({'model': BaseNodeMerge('base merge')})
    dm.add_inference_model({'model': BaseInference('base inference')})
    dm.add_selection_model({'model': BaseResponseSelection('base selection')})
    dm.add_expansion_model({'model': BaseResponseExpansion('base expansion')})
    dm.add_generation_model({'model': BaseResponseGeneration('base generation')})

    dm.add_mention_aggregation(First)
    dm.add_merge_aggregation(First)
    dm.add_inference_aggregation(First)

    dm.add_mention_bridge(BaseMentionBridge('base mention bridge'))
    dm.add_merge_bridge(BaseMergeBridge('base merge bridge'))
    dm.add_inference_bridge(BaseInferenceBridge('base inference bridge'))

    # todo - debug mention and merge
    # todo - add merge iteration function and merge+inference iteration function
    # todo - implement inference, inference bridge, selection, expansion, generation base models

    dm.build_framework()

    dialogue_graph = {}

    asr_hypotheses = [
        {'text': 'bob loves sally and himself',
         'text_confidence': 0.87,
         'tokens': ['bob', 'loves', 'sally', 'and', 'himself'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.8, 4: 0.80}
         }
    ]

    output = dm.run(asr_hypotheses, dialogue_graph)
    print(output)