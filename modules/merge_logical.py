
from GRIDD.modules.merge_logical_spec import MergeLogicalSpec
from collections import deque


class MergeLogical:

    def __init__(self, inference_engine):
        self.inference_engine = inference_engine

    def __call__(self, working_memory):
        """
        Check each concept pair for a property-neighborhood match.

        Todo: Should be able to filter pairs to only include new instances.
        """
        all_pairs = []
        types = working_memory.supertypes()                     # node : set<types>
        new = set(working_memory.concepts())
        while new:
            ref = new.pop()
            for target in set(working_memory.concepts()) - {ref}:
                pairs = working_memory.equivalent(ref, target, types)
                all_pairs.extend(pairs)
                new -= {x for x, _ in pairs}
        return all_pairs



if __name__ == '__main__':
    print(MergeLogicalSpec.verify(MergeLogical))













