
class BaseResponseSelection:

    def run(self, input, working_memory):
        """

        :param input: binary indicating status of inference bridge
        :param working_memory: updated dialogue graph by merge-and-inference procedure
        :return: planned response as an ordered sequence of predicates from graph
        """
        response = {'<bob node>': working_memory['<bob node>']}
        return [response]