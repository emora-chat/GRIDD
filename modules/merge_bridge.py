import GRIDD.globals as globals
from itertools import chain
from GRIDD.data_structures.reference_gatherer import gather

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

        # convert reference spans to reference predicates
        for node, features in working_memory.features.items():
            if 'refl' in features:
                features['refl'] = gather(node, features['refl'], working_memory)

        if globals.DEBUG:
            print("<< Working Memory after NLU >>")
            print(working_memory.ugly_print(exclusions={'var','is_type','object','entity','predicate','span','ref'}))
            print()
        return working_memory
