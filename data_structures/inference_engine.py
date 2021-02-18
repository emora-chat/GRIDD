
from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from GRIDD.data_structures.knowledge_parser import logic_parser
from structpy.map import Bimap


class InferenceEngine:

    def __init__(self, *rules):
        self.rules = {rule: logic_parser.to_rules(rule)[0] for rule in rules}
        self.matcher = GraphMatchingEngine()

    def infer(self, facts, *rules):
        facts_concept_graph = logic_parser.to_concept_graph(facts)[0]
        attributes = {}
        types = set()
        for c in facts_concept_graph.concepts():
            attributes[c] = facts_concept_graph.supertypes(c)
        for s, t, o, i in facts_concept_graph.predicates(predicate_type='type'):
            facts_concept_graph.remove(predicate_id=i)
            types.add(o)
        for type in types:
            facts_concept_graph.remove(type)
        facts_concept_graph.remove('type')
        facts_graph = facts_concept_graph.to_graph()
        for node, types in attributes.items():
            facts_graph.data(node)['attributes'] = types

        rules = {**self.rules, **{rule: logic_parser.to_rules(rule)[0] for rule in rules}}
        rules = Bimap(rules)
        converted_rules = Bimap()
        for rid, (pre, post) in rules.items():
            varset = set()
            attributes = {}
            types = set()
            for s, t, o, i in pre.predicates(predicate_type='var'):
                varset.add(s)
                pre.remove(predicate_id=i)
            pre.remove('var')
            for c in pre.concepts():
                attributes[c] = pre.supertypes(c)
            for s, t, o, i in pre.predicates(predicate_type='type'):
                pre.remove(predicate_id=i)
                types.add(o)
            for type in types:
                pre.remove(type)
            pre.remove('type')
            precondition = pre.to_graph()
            for var in varset:
                precondition.data(var)['var'] = True
            for node, types in attributes.items():
                precondition.data(node)['attributes'] = types
            converted_rules[rid] = precondition
        sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        return sols

    def apply(self, facts=None, *rules, solutions=None):
        if facts is not None:
            solutions = self.infer(facts, *rules)
        implications = {}
        for rule, sols in solutions.items():
            for sol in sols:
                # assign vars to vals
                pass
        return implications


if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))