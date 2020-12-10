from typing import List,Dict
from modules.module import Module
from knowledge_base.concept_graph import ConceptGraph

class MentionsByLexicon(Module):

    def __init__(self, name):
        super().__init__(name)

        # todo - just for testing purposes
        i_cg = ConceptGraph(nodes=['user'])
        love_cg = ConceptGraph(nodes=['love'])
        subj_id = '_new_%d'%love_cg._get_next_id()
        love_cg.add_node(subj_id)
        obj_id = '_new_%d'%love_cg._get_next_id()
        love_cg.add_node(obj_id)
        love_pred_inst = love_cg.add_bipredicate(subj_id, obj_id, 'love')
        math_cg = ConceptGraph(nodes=['math'])
        self.map = {
            'i': ('user', i_cg),
            'love': (love_pred_inst, love_cg),
            'math': ('math', math_cg)
        }

    def retrieve(self, text):
        """
        Returns the lexicon entry (focal node, structure graph) for the given text, or None if entry does not exist
        """
        if text in self.map:
            return self.map[text]
        return None,None

    # todo - need the inference procedure to instantiate the argument attachments of predicates???
    # todo - need aliasing for KG creation, where each alias is added to lexicon to be used in this step
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
        new_cg = ConceptGraph()
        mentions_by_hypotheses = []
        for hypo in input:
            mentions = {}
            start_idx = 0
            for token in hypo['tokens']:
                end_idx = start_idx + len(token) + 1
                focal_node, structure = self.retrieve(token)
                if structure is not None:
                    new_cg.merge(structure)
                    mentions[(start_idx, end_idx)] = focal_node
                start_idx = end_idx
            mentions_by_hypotheses.append(mentions)
        return mentions_by_hypotheses