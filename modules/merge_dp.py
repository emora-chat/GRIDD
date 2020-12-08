from modules.module import Module

class NodeMergeDP(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        """
        Calculate node merge scores for pairs of nodes

        :param input: binary from mention or inference bridge indicating their status
        :param graph: updated graph after Mention Bridge
        :return: dictionary <tuple pair: float merge score>
        """
        scores = {}

        return scores

if __name__ == '__main__':
    merge = NodeMergeDP('dp merge')
    sentence = "I love math"
    output = merge.run(sentence, {})