
from abc import ABC, abstractmethod

class TextToLogicModel(ABC):

    def __init__(self, knowledge_base, model, template_base, *template_file_names):
        self.knowledge_base = knowledge_base
        self.model = model
        self.templates = template_base
        for fn in template_file_names:
            with open(fn, 'r') as f:
                self.templates.add_knowledge(f.read())
        self.rules = self.templates._concept_graph.generate_inference_graphs()
        for rule in self.rules:
            self._reference_expansion(rule.precondition)

    @abstractmethod
    def text_to_graph(self, turns, knowledge_base):
        """
        turns: list of strings representing dialogue turns.
        return: ConceptGraph representation of the text's surface form.
                For example, a graph of the dependency parse of the last turn.
        """
        pass

    def translate(self, turns):
        egraph = self.text_to_graph(turns, self.knowledge_base)
        self._expression_pull(egraph, self.knowledge_base)
        self._unknown_expression_pull(egraph)
        rule_assignments = self._inference(egraph)
        return self._get_mentions(rule_assignments), self._get_merges(rule_assignments)

    def _expression_pull(self, egraph, kgraph):
        """
        Pull expressions from KB into the expression graph.
        """
        egraph.pull(nodes=['"%s"'%span_obj.string for span_node, span_obj in egraph.spans.items()], 
                    kb=kgraph, max_depth=1)

    def _unknown_expression_pull(self, egraph):
        """
        Create "UNK" expression nodes for all nodes with no expr references.
        """
        for span_node, span_object in egraph.spans.items():
            expression = '"%s"' % span_object.string
            references = egraph.object_neighbors(expression, 'expr')
            if len(references) == 0:
                unk_node = egraph.add_node(egraph._get_next_id())
                egraph.add_bipredicate(unk_node, 'unknown', 'type')
                egraph.add_bipredicate(expression, unk_node, 'expr')

    def _reference_expansion(self, pregraph):
        """
        Expand vars in precondition to include expression and reference links.
        """
        for concept in pregraph.concepts():
            if pregraph.type(concept) is None and len(pregraph.monopredicate(concept, 'var')) > 0:
                # found variable entity instance
                found_supertype = False
                for supertype in pregraph.object_neighbors(concept, 'ltype'):
                    found_supertype = True
                    self._expand_references(pregraph, concept, supertype)
                if not found_supertype:
                    self._expand_references(pregraph, concept)

    def _expand_references(self, template_graph, concept, supertype=None):
        expression_var = template_graph._get_next_id()
        exprof = template_graph.add_bipredicate(concept, expression_var, 'exprof')
        concept_var = template_graph._get_next_id()
        expr = template_graph.add_bipredicate(expression_var, concept_var, 'expr')
        new_nodes = [expression_var, exprof, concept_var, expr]
        if supertype is not None:
            concept_type = template_graph.add_bipredicate(concept_var, supertype, 'type')
            template_graph.remove_bipredicate(concept, supertype, 'ltype')
            new_nodes.append(concept_type)
        for n in new_nodes:
            template_graph.add_monopredicate(n, 'var')

    def _inference(self, egraph):
        """
        Apply the specified rules to the current egraph and get the variable assignments of the solutions
        """
        rule_assignments = {}
        for rule in self.rules:
            matches = egraph.infer(rule.precondition)
            var_assignments = self._get_variable_assignments(matches)
            rule_assignments[rule] = var_assignments
        return rule_assignments

    def _get_variable_assignments(self, var_matches):
        var_map, matches = var_matches
        solutions = []
        for match in matches:
            variable_assignments = {}
            for key, value in var_map.items():
                variable_assignments[key] = match[value]
            solutions.append(variable_assignments)
        return solutions

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


