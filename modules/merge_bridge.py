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
            span_map = self.framework.nlp_data['dependency parse'][2]
            for (spanobj1, pos1), (spanobj2, pos2) in input:
                span1 = span_map[spanobj1]
                span2 = span_map[spanobj2]
                print('\tConsidering spans (%s,%s)'%(span1,span2))
                (concept1,) = working_memory.objects(span1, 'exprof')
                concept1 = self._follow_path(concept1, pos1, working_memory)
                (concept2,) = working_memory.objects(span2, 'exprof')
                concept2 = self._follow_path(concept2, pos2, working_memory)
                print('\tConsidering concepts (%s,%s)'%(concept1,concept2))
                working_memory.merge(concept1, concept2)
        return False

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        return concept
