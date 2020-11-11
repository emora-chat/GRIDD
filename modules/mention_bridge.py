from typing import List, Dict
from modules.module import Module

class BaseMentionBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: List[Dict], graph):
        """

        :param input: mention output (list of dictionaries of token spans -> DSG element)
        :return: None
        """
        for mentions_dict in input:
            for span, mention in mentions_dict.items():
                graph[mention] = {}
