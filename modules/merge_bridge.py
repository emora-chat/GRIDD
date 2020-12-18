from typing import List, Dict
from modules.module import Module

class BaseMergeBridge(Module):

    def __init__(self, name, threshold_score):
        super().__init__(name)
        self.threshold = threshold_score

    def run(self, input: Dict, working_memory):
        """
        Merge the highest scored node pair together in the graph

        :param input: merge output (dictionary of node pairs -> merge scores)
        :return: binary value indicating whether a merge occurred
        """
        print("\nMERGING::")
        if len(input) > 0:
            for (spanobj1, pos1), (spanobj2, pos2) in input:
                span1 = working_memory.span_map[spanobj1]
                span2 = working_memory.span_map[spanobj2]
                print('\tConsidering spans (%s,%s):: '%(span1,span2))
                (concept1,) = working_memory.graph.object_neighbors(span1, 'exprof')
                concept1 = self._follow_path(concept1, pos1, working_memory)
                (concept2,) = working_memory.graph.object_neighbors(span2, 'exprof')
                concept2 = self._follow_path(concept2, pos2, working_memory)
                print('\tConsidering concepts (%s,%s):: '%(concept1,concept2))
                working_memory.graph.merge_node(concept1, concept2)
                test = 1
        return False

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.graph.subject(concept)
        elif pos == 'object':
            return working_memory.graph.object(concept)
        return concept
