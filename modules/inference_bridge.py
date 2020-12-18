from typing import List, Dict
from modules.module import Module

class BaseInferenceBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, working_memory):
        """

        :param input: inference output (graph of inferred additions)
        :param graph: dialogue graph updated by merge pipeline
        :return: binary indicating whether update was done
        """
        # working_memory.update(input)
        # return True
        print('You have reached the end of the implemented Pipeline. It currently only performs NLU and inferences.')
        exit()