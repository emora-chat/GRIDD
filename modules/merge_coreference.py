

class MergeCoreference:

    def __call__(self, coref_output, working_memory):
        """
        Output: List of pairs of nodes to merge in working memory based on coref model.
        """
        node_merges = []
