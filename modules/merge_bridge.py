from typing import List, Dict
from modules.module import Module

class BaseMergeBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: Dict, graph):
        """
        Merge the highest scored node pair together in the graph

        :param input: merge output (dictionary of node pairs -> merge scores)
        :return: None
        """
        keeper, merger = max(input.items(), key=lambda x: x[1])[0]
        graph[keeper].update(graph[merger])
