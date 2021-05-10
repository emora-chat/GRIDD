from GRIDD.data_structures.score_graph import ScoreGraph
from GRIDD.modules.feature_propogation_spec import FeaturePropogationSpec
from GRIDD.globals import *

class FeaturePropogation:

    def __call__(self, working_memory, iterations):
        """
        Update the features of the nodes in working memory
        """
        # todo
        return working_memory

if __name__ == '__main__':
    print(FeaturePropogationSpec.verify(FeaturePropogation))