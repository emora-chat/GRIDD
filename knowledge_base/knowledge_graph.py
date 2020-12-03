from lark import Lark, Transformer
from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_parser import PredicateTransformer
import time, sys, json
from os.path import join
from pyswip import Prolog

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
            name: STRING
            type: STRING 
            types: type ("," type)+
            alias: STRING_WSPACE
            aliases: alias ("," alias)+
            id: STRING
            subject: STRING | bipredicate | monopredicate | instance | ontological
            object: STRING | bipredicate | monopredicate | instance | ontological
            STRING: /[a-z_A-Z0-9]/+
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

    def test_prolog(self):
        prolog = Prolog()
        rules = [rule.replace('.','').strip() for rule in
                 """type(like, like).
                    type(positive, positive).
                    type(love, love).
                    type(movie, movie).
                    type(genre, genre).
                    type(reason, reason).
                    type(property, property).
                    type(like, positive).
                    type(love, like).
                    type(love, positive).
                    type(starwars, movie).
                    type(avengers, movie).
                    type(action, genre).
                    type(comedy, genre).
                    predinst(like(john, starwars), ljs).
                    predinst(genre(starwars, action), gsa).
                    predinst(reason(ljs, gsa), rlg).
                    predinst(love(mary, avengers), lma).
                    predinst(genre(avengers, comedy), gac). 
                    predinst(reason(lma, gac), rlh).""".split('\n')]
        for rule in rules:
            prolog.assertz(rule)
        query = "predinst(A, B), functor(A, C, _), arg(1, A, D), arg(2, A, E), type(C, like), type(E, movie), predinst(F, G), functor(F, H, _), arg(1, F, E), arg(2, F, J), type(J, genre), predinst(K, L), functor(K, M, _), arg(1, K, B), arg(2, K, G), type(M, reason)"
        for soln in prolog.query(query):
            print(json.dumps(soln, indent=4))

    def infer(self, inference_graph):
        prolog = Prolog()
        kg_rules = self.to_kb_prolog()
        inference_rules = inference_graph.to_query_prolog()
        for rule in kg_rules:
            prolog.assertz(rule)
        for query in inference_rules:
            for soln in prolog.query(query):
                print(json.dumps(soln, indent=4))

    def to_kb_prolog(self):
        rules = []
        for tuple, inst_id in self._concept_graph.predicate_instances():
            if len(tuple) == 3:
                subject, object, pred_type = tuple
                if pred_type == 'type':
                    if self._concept_graph.monopredicate(subject, 'is_type'): # ontology
                        rules.append('type(%s,%s)'%(subject,subject))
                    rules.append('type(%s,%s)'%(subject,object)) # do for all type ancestors????
                else:
                    rules.append('predinst(%s(%s,%s),%s)'%(pred_type,subject,object,inst_id))
        return rules

    def to_query_prolog(self):
        rules = []

        return rules

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

    kg.infer(ig)

    test = 1

