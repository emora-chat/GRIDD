from allennlp.predictors.predictor import Predictor
import allennlp_models.structured_prediction

from modules.module import Module

class NodeMergeDP(Module):

    def __init__(self, name):
        super().__init__(name)
        self.dependency_parser = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")

    def run(self, input, graph):
        """
        Calculate node merge scores for pairs of nodes

        :param input: binary from mention or inference bridge indicating their status
        :param graph: updated graph after Mention Bridge
        :return: dictionary <tuple pair: float merge score>
        """
        scores = {}

        parse = self.dependency_parser.predict(
            sentence=input
        )

        return scores

if __name__ == '__main__':
    merge = NodeMergeDP('dp merge')
    sentence = "I love math"
    output = merge.run(sentence, {})