from typing import List, Dict
from modules.module import Module

class BaseMergeBridge(Module):

    def __init__(self, name, threshold_score):
        super().__init__(name)
        self.threshold = threshold_score

    def run(self, input: Dict, graph):
        """
        Merge the highest scored node pair together in the graph

        :param input: merge output (dictionary of node pairs -> merge scores)
        :return: binary value indicating whether a merge occurred
        """
        if len(input) > 0:
            (keeper, merger), merge_score = max(input.items(), key=lambda x: x[1])
            if merge_score > self.threshold:
                graph[keeper].update(graph[merger])
                del graph[merger]
                return True
        return False
