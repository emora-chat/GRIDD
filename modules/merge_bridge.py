
class MergeBridge:

    def __init__(self, threshold_score):
        self.threshold = threshold_score

    def __call__(self, *args, **kwargs):
        """
        Merge the highest scored node pair together in the graph
        args[0] - node merges
        args[1] - working memory
        """
        node_merges, working_memory = args
        for concept1, concept2 in node_merges:
            working_memory.merge(concept1, concept2)

        print("\nWM AFTER MERGES::")
        print(working_memory.pretty_print())
        print()

        return working_memory
