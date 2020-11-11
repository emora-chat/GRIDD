from typing import List,Dict
from modules.module import Module
from nltk.stem.wordnet import WordNetLemmatizer

class BaseMentionIdentification(Module):

    def __init__(self, name):
        super().__init__(name)
        self.map = {
            'bob': '<bob node>',
            'sally': '<sally node>',
            'love': '<love structure>',
            'himself': '<himself node>'
        }
        self.lemmatizer = WordNetLemmatizer()

    def run(self, input: List[Dict], graph) -> List:
        """
        Extract known concepts from input

        :param input: List of ASR hypotheses formatted in the following manner:
            asr_hypotheses = [
                {'text': 'bob loves sally',
                 'text_confidence': 0.87,
                 'tokens': ['bob', 'loves', 'sally'],
                 'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80}
                },
                ...
            ]
        :return: List of identified mentions for each hypotheses in the following form:
            mentions = [
                {(0,0): <bob node>,
                 (1,1): <love DSG structure>,
                 (2,2): <sally node>
                },
                ...
            ]
        """
        mentions_by_hypotheses = []
        for hypo in input:
            mentions = {}
            for i, token in enumerate(hypo['tokens']):
                struct = self.map.get(self.lemmatizer.lemmatize(token.lower()), None)
                if struct is not None:
                    mentions[(i,i)] = struct
            mentions_by_hypotheses.append(mentions)
        return mentions_by_hypotheses