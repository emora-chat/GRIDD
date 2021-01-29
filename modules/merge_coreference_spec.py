
from structpy import specification


@specification
class MergeCoreferenceSpec:
    """

    """

    @specification.init
    def MERGE_COREFERENCE(MergeCoreference):
        return MergeCoreference()


    def call(merge_coreference):
        """
        Output: List of pairs of nodes to merge in working memory based on coref model.
        """
        pass
