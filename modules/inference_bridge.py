from typing import List, Dict
from modules.module import Module

class BaseInferenceBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """

        :param input: inference output (graph of inferred additions)
        :param graph: dialogue graph updated by merge pipeline
        :return: binary indicating whether update was done
        """
        graph.update(input)
        return True