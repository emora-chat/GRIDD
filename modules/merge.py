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
        if '<bob node>' in graph and '<himself node>' in graph:
            scores[('<bob node>', '<himself node>')] = 1.0
        if '<sally node>' in graph and '<himself node>' in graph:
            scores[('<sally node>', '<himself node>')] = 0.1
        return scores