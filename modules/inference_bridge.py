from typing import List, Dict
from modules.module import Module

class BaseInferenceBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: List[Dict], graph):
        """

        :param input: inference output
        :return:
        """
        pass