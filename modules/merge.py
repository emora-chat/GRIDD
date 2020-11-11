from modules.module import Module

class BaseNodeMerge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """
        Calculate node merge scores for pairs of nodes

        :param input: None object passed from Mention Bridge
        :param graph: updated graph after Mention Bridge
        :return: dictionary <tuple pair: float merge score>
        """
        scores = {}
        if 'bob' in graph and 'himself' in graph:
            scores[('bob', 'himself')] = 1.0
        if 'sally' in graph and 'himself' in graph:
            scores[('sally', 'himself')] = 0.1
        return scores