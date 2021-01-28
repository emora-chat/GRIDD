
from modules.merge_coreference_spec import MergeCoreferenceSpec

from modules.merge_span_to_merge_concept import MergeSpanToMergeConcept
merge_span_to_merge_concept = MergeSpanToMergeConcept()



class MergeCoreference:

    def __call__(self, coref_output, working_memory):
        """
        Output: List of pairs of nodes to merge in working memory based on coref model.
        """
        node_merges = []



if __name__ == '__main__':
    print(MergeCoreferenceSpec.verify(MergeCoreference))