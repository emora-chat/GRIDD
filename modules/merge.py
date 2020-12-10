from modules.module import Module

class BaseNodeMerge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, working_memory):
        """
        Calculate node merge scores for pairs of nodes

        :param input: binary from mention or inference bridge indicating their status
        :param working_memory: updated graph after Mention Bridge
        :return: dictionary <tuple pair: float merge score>
        """
        scores = {}
        if '<bob node>' in working_memory and '<himself node>' in working_memory:
            scores[('<bob node>', '<himself node>')] = 1.0
        if '<sally node>' in working_memory and '<himself node>' in working_memory:
            scores[('<sally node>', '<himself node>')] = 0.1
        return scores