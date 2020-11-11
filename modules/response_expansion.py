from modules.module import Module

class BaseResponseExpansion(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """

        :param input: ordered sequence of predicates from graph
        :param graph: updated dialogue graph by merge-and-inference procedure
        :return: ordered sequence of predicate trees
        """
        return input