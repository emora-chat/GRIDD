from modules.module import Module

class BaseResponseSelection(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """

        :param input: binary indicating status of inference bridge
        :param graph: updated dialogue graph by merge-and-inference procedure
        :return: planned response as an ordered sequence of predicates from graph
        """
        response = {'<bob node>': graph['<bob node>']}
        return [response]