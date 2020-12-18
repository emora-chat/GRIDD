from typing import List, Dict
from modules.module import Module

class BaseMentionBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: Dict, working_memory):
        """
        Merge mention graphs into working_memory and generate span node with span object where span node is connected to focus of mention graph.
        Map span object to span node in WM.span_map.
        :param input: mention output (dictionary of token spans -> [DSG element])
        :return: None
        """
        for span, mention_graphs in input.items():
            for mention_graph in mention_graphs:
                working_memory[mention_graph] = {}
        return True
