import GRIDD.globals as globals
from itertools import chain

class MergeBridge:

    def __init__(self, threshold_score):
        self.threshold = threshold_score

    def __call__(self, working_memory, *node_merge_pairs):
        """
        Merge the highest scored node pair together in the graph
        args[0] - working memory
        args[1+] - lists of node pairs to merge
        """
        node_merge_pairs = chain(*[ls for ls in node_merge_pairs if ls is not None])
        visited = []
        merge_map = {}

        for concept1, concept2 in node_merge_pairs:
            concept1 = merge_map.get(concept1, concept1)
            concept2 = merge_map.get(concept2, concept2)
            kept = working_memory.merge(concept1, concept2)
            replaced = concept2 if kept == concept1 else concept1
            merge_map[replaced] = kept
            if replaced in merge_map.values(): # If merges are chained, must re-merge previous nodes that receive a later merge
                for v1, v2 in visited:
                    if v1 == replaced:
                        working_memory.merge(v1, kept)
            visited.append((kept, replaced))

        # todo - assess whether this pulling works as we want it to...
        #  how to pull complete information for concepts
        #  like pull emora possess KB1 needs KB1 type movie AND property(KB1, favorite)
        working_memory.pull(1, exclude_on_pull={'type', 'expr'}) #todo - what function does is_type have in dialogue graph???

        if globals.DEBUG:
            print("<< Working Memory after NLU >>")
            print(working_memory.ugly_print(exclusions={'var','object','entity','predicate','span','ref'}))
            print()
        return working_memory
