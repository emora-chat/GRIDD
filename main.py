from framework import Framework
from aggregator import Aggregator
from modules.mention_identification import BaseMentionIdentification
from modules.node_merging import BaseNodeMerge
from modules.inference import BaseInference
from modules.response_selection import BaseResponseSelection
from modules.response_expansion import BaseResponseExpansion
from modules.response_generation import BaseResponseGeneration

class First(Aggregator):
    def run(self, input):
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
    dm.add_selection_aggregation(First)
    dm.add_expansion_aggregation(First)
    dm.add_generation_aggregation(First)

    dm.build_framework()

    output = dm.run('')
    print(output)