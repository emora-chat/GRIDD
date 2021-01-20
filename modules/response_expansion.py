
class BaseResponseExpansion:

    def run(self, input, working_memory):
        """

        :param input: ordered sequence of predicates from graph
        :param working_memory: updated dialogue graph by merge-and-inference procedure
        :return: ordered sequence of predicate trees
        """
        return input