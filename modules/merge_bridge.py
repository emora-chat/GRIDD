from collections import defaultdict

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
        merge_map = {}

        for concept1, concept2 in node_merges:
            working_memory.merge(merge_map.get(concept1, concept1),
                                 merge_map.get(concept2, concept2))
            merge_map[concept2] = concept1

        print("<< Working Memory after NLU >>")
        print(working_memory.pretty_print(exclusions={'var','is_type','object','entity','predicate','span'}))
        print()
        # working_memory.display_graph(exclusions={'var','is_type','object','entity','predicate','span','exprof','time'})
        return working_memory
