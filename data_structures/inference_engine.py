from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.concept_graph import ConceptGraph


class InferenceEngine:

    def __init__(self, *rules):
        self.rules = KnowledgeParser.rules(*rules)
        self.matcher = GraphMatchingEngine()

    def infer(self, facts, *rules, return_rules=False):
        facts_concept_graph = KnowledgeParser.from_data(facts, namespace='facts_')
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

        rules = {**self.rules, **KnowledgeParser.rules(*rules)}
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
        if return_rules:
            sols = {(converted_rules.reverse()[precondition], rules[converted_rules.reverse()[precondition]]):
                        sol for precondition, sol in sols.items()}
        else:
            sols = {converted_rules.reverse()[precondition]: sol for precondition, sol in sols.items()}
        return sols

    def apply(self, facts=None, *rules, solutions=None):
        if facts is not None:
            solutions = self.infer(facts, *rules, return_rules=True)
        implications = {}
        for (rid, (pre, post)), sols in solutions.items():
            for sol in sols:
                cg = ConceptGraph(namespace='implied')
                id_map = cg.id_map(post)
                for pred in post.predicates():
                    pred = [sol.get(x, x) for x in pred]
                    pred = [id_map.get(x) if x is not None else None for x in pred]
                    cg.add(*pred)
                for concept in post.concepts():
                    concept = id_map.get(sol.get(concept, concept))
                    cg.add(concept)
                implications.setdefault(rid, []).append(cg)
        return implications

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))