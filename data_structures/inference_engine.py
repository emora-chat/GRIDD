from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.concept_graph import ConceptGraph


class InferenceEngine:

    def __init__(self, *rules, device='cpu'):
        self.rules = KnowledgeParser.rules(*rules)
        self.preloaded_rules = self._convert_rules(self.rules)
        self.matcher = GraphMatchingEngine(device=device)

    def _convert_rules(self, rules):
        converted_rules = {}
        for rid, (pre, post, vars) in rules.items():
            pre = pre.copy()
            attributes = {}
            types_to_remove = set()
            types_to_preserve = set()
            for c in pre.concepts():
                attributes[c] = pre.supertypes(c)
            for s, t, o, i in pre.predicates(predicate_type='type'):
                if not pre.related(i):
                    pre.remove(predicate_id=i)
                    types_to_remove.add(o)
                else:
                    types_to_preserve.update({s, o})
            for type in types_to_remove - types_to_preserve:
                pre.remove(type)
            pre.remove('type')
            precondition = pre.to_graph()
            for var in vars:
                precondition.data(var)['var'] = True
            for node, types in attributes.items():
                precondition.data(node)['attributes'] = types
            converted_rules[rid] = precondition
        return converted_rules

    def _convert_facts(self, facts):
        attributes = {}
        quantities = set()
        types_to_remove = set()
        types_to_preserve = set()
        for c in facts.concepts():
            attributes[c] = facts.supertypes(c)
            if isinstance(c, int) or isinstance(c, float):
                quantities.add(c)
        for s, t, o, i in facts.predicates(predicate_type='type'):
            if not facts.related(i):
                facts.remove(predicate_id=i)
                types_to_remove.add(o)
            else:
                types_to_preserve.update({s,o})
        for type in types_to_remove - types_to_preserve:
            facts.remove(type)
        facts.remove('type')
        facts_graph = facts.to_graph()
        for node, types in attributes.items():
            facts_graph.data(node)['attributes'] = types
        for node in quantities:
            facts_graph.data(node)['num'] = node
        return facts_graph

    def infer(self, facts, *rules, cached=True):
        # Todo: allow inference using only provided rules (not cached rules)
        facts_concept_graph = KnowledgeParser.from_data(facts, namespace='facts_').copy()
        facts_graph = self._convert_facts(facts_concept_graph)
        dynamic_rules = KnowledgeParser.rules(*rules)
        rules = Bimap({**self.rules, **dynamic_rules})
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        converted_rules = Bimap({**self.preloaded_rules, **dynamic_converted_rules})
        sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        sols = {converted_rules.reverse()[precondition]: sols for precondition, sols in sols.items()}
        sols = {rule_id: (rules[rule_id][0], rules[rule_id][1], sol_ls) for rule_id, sol_ls in sols.items()}
        return sols

    def apply(self, facts=None, *rules, solutions=None):
        # Todo: refactor signature to mimic IntelligenceCore's apply_inferences
        if facts is not None:
            solutions = self.infer(facts, *rules)
        implications = {}
        for rid, (pre, post, sols) in solutions.items():
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
                mapped_features = {new_node: post.features[old_node] for old_node, new_node in id_map.items()}
                for node, features in mapped_features.items():
                    if len(features) > 0:
                        cg.features[node].update(features)
        return implications

    def add(self, rules):
        new_rules = self._convert_rules(rules)
        for rule in new_rules:
            if rule in self.preloaded_rules:
                raise ValueError(f'Rule by name {rule} already exists!')
        self.preloaded_rules.update(new_rules)

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))