from modules.module import Module

class MergeSyntax(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, working_memory):
        """
        Calculate node merge scores for pairs of nodes

        :param input: binary from mention or inference bridge indicating their status
        :param graph: updated graph after Mention Bridge
        :return: dictionary <tuple pair: float merge score>
        """
        return self.framework.nlp_data['dependency parse'][1]

if __name__ == '__main__':
    merge = MergeSyntax('dp merge')
    sentence = "I love math"
    output = merge.run(sentence, {})