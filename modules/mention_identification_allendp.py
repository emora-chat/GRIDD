from typing import List,Dict
from modules.module import Module
from knowledge_base.concept_graph import ConceptGraph

class MentionsAllenDP(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: List[Dict], working_memory) -> List:
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
        :return: List of dict<character span: concept graph> for each hypothesis in the following form:
            mentions = [
                {(0,4): <bob node>,
                 (4,10): <love DSG structure>,
                 (10,15): <sally node>
                },
                ...
            ]
        """
        mentions = {}
        mention_graphs, _ = self.framework.nlp_data['dependency parse']
        for span, mention_cgs in mention_graphs.items():
            for mention_cg in mention_cgs:
                pass
        return mentions