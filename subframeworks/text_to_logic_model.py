
from abc import ABC, abstractmethod


class TextToLogicModel(ABC):

    def __init__(self, knowledge_base, *template_file_names):
        self.knowledge_base = knowledge_base
        self.rules = []
        for fn in template_file_names:
            with open(fn) as f:
                pass

    @abstractmethod
    def text_to_graph(self, turns, knowledge_base):
        """
        turns: list of strings representing dialogue turns.
        return: ConceptGraph represenation of the text's surface form.
                For example, a graph of the dependency parse of the last turn.
        """
        pass

    def translate(self, turns):
        egraph = self.text_to_graph(turns, self.knowledge_base)
        self._expression_pull(egraph, self.knowledge_base)
        self._unknown_expression_pull(egraph)
        for rule in self.rules:
            self._reference_expansion(rule.precondition)
        # inference (??)
        return self._get_mentions(None), self._get_merges(None)

    def _expression_pull(self, egraph, kgraph):
        """
        Pull expressions from KB into the expression graph.
        """
        pass

    def _unknown_expression_pull(self, egraph):
        """
        Create "UNK" expression nodes for all nodes with no expr references.
        """
        pass

    def _reference_expansion(self, pregraph):
        """
        Expand vars in precondition to include expression links.
        """
        pass

    def _get_mentions(self, assignments):
        """
        Produce (mention span, mention graph) pairs.

        assignments: dict<rule: list<assignments>>
        """
        pass

    def _get_merges(self, assignmens):
        """
        Produce (mention span, mention graph) pairs.

        assignments: dict<rule: list<assignments>>
        """
        pass


