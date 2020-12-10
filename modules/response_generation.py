from modules.module import Module

class BaseResponseGeneration(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, working_memory):
        """

        :param input: ordered sequence of predicate trees
        :param working_memory: updated dialogue graph by merge-and-inference procedure
        :return: natural language representation of predicate trees
        """
        return ' & '.join(str(x) for x in input)