from lark import Lark, Transformer
from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_parser import PredicateTransformer
import time, sys, json
from os.path import join

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr', 'pre', 'post', 'var'}


class KnowledgeGraph:

    def __init__(self, filename=None, nodes=None):
        if nodes is None:
            nodes = BASE_NODES
        else:
            if isinstance(nodes, list):
                nodes = set(nodes)
            nodes.update(BASE_NODES)
        self._concept_graph = ConceptGraph(nodes=nodes)
        self._grammar = r"""
            start: knowledge+
            knowledge: ((bipredicate | monopredicate | instance | ontological | expression )+ ";") | ((anon_rule | named_rule | inference | implication) ";")
            anon_rule: conditions "=>" conditions
            named_rule: conditions "->" type "->" conditions
            inference: conditions "->" type
            implication: type "->" conditions
            conditions: (bipredicate | monopredicate | instance)+
            bipredicate: ((name "/")|(id "="  ))? type "(" subject "," object ")"
            monopredicate: ((name "/")|(id "="  ))? type "(" subject ")"
            instance: ((name "/")|(id "="))? type "(" ")"
            ontological: id "<" (type | types) ">"
            expression: id "[" (alias | aliases) "]"
            name: string_term
            type: string_term 
            types: type ("," type)+
            alias: string_wspace_term
            aliases: alias ("," alias)+
            id: string_term
            subject: string_term | bipredicate | monopredicate | instance | ontological
            object: string_term | bipredicate | monopredicate | instance | ontological
            string_term: STRING
            STRING: /[a-z_A-Z0-9]/+
            string_wspace_term: STRING_WSPACE
            STRING_WSPACE: /[a-z_A-Z0-9 ]/+
            WHITESPACE: (" " | "\n")+
            %ignore WHITESPACE
        """
        self.parser = Lark(self._grammar, parser="earley")
        self.predicate_transformer = PredicateTransformer(self, BASE_NODES)

        self._concept_graph.merge(self.add_knowledge(open(join('knowledge_base','kg_files','base.kg'), 'r').read())[0])
        self.predicate_transformer._set_kg_concepts()

        if filename is not None:
            self.add_knowledge(open(filename, 'r').read())

    def add_knowledge(self, input):
        if input.endswith('.kg'):
            input = open(input, 'r').read()
        tree = self.parser.parse(input)
        return self.predicate_transformer.transform(tree)

    def merge(self, other_graph):
        self._concept_graph.merge(other_graph)

"""
    def properties(self, concept):
        return self._concept_graph.predicates(concept)

    def types(self, concept):
        return self._concept_graph.predicates_of_subject(concept, predicate_type='type')

    def subtypes(self, concept):
        return self._concept_graph.predicates_of_object(concept, predicate_type='type')

    def instances(self, type_):
        pass

    def implication_rules(self, type_):
        pass

    def save(self, json_filename):
        pass
"""

if __name__ == '__main__':

    # s = time.time()
    # kg = KnowledgeGraph()
    # additions = kg.add_knowledge(join('knowledge_base','kg_files','example.kg'))
    # print('Elapsed: %.2f sec'%(time.time()-s))

    s = time.time()
    kg = KnowledgeGraph()
    additions = kg.add_knowledge(join('knowledge_base', 'kg_files', 'prolog_knowledge.kg'))
    kg.merge(additions[0])
    print('Elapsed: %.2f sec' % (time.time() - s))

    s = time.time()
    ig = KnowledgeGraph(nodes=['movie','is_genre','genre'])
    ig._concept_graph.add_monopredicate('movie', 'is_type')
    ig._concept_graph.add_monopredicate('genre', 'is_type')
    ig._concept_graph.add_monopredicate('is_genre', 'is_type')
    additions = ig.add_knowledge(join('knowledge_base', 'kg_files', 'prolog_inference.kg'))
    for addition in additions:
        ig.merge(addition)
    print('Elapsed: %.2f sec' % (time.time() - s))

    inference_rule_graphs = ig._concept_graph.generate_inference_graph()
    matches = {}
    for situation_node, rule_graph in inference_rule_graphs.items():
        matches[situation_node] = kg._concept_graph.infer(rule_graph)

    test = 1

