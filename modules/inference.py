from modules.module import Module

class BaseInference(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """

        :param input: None object from merge pipeline
        :param graph: dialogue graph updated by merge pipeline
        :return: graph of new inferred additions
        """
        additions = {}
        if '<bob node>' in graph and '<love structure>' in graph and '<sally node>' in graph:
            additions['<bob node>'] = {}
            additions['<bob node>']['<love structure>'] = '<sally node>'
        return additions