from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph


class InferenceEngine:

    def __init__(self, rules=None, device='cpu'):
        self.rules = {}
        self._preloaded_rules = {}
        if rules is not None:
            self.add(rules)
        self.matcher = GraphMatchingEngine(device=device)

    def add(self, rules):
        if not isinstance(rules, dict):
            rules = ConceptGraph(rules).rules()
        for rule in rules:
            if rule in self.rules:
                raise ValueError(f'Rule by name {rule} already exists!')
        new_rules = self._convert_rules(rules)
        self.rules.update(rules)
        self._preloaded_rules.update(new_rules)

    def _convert_rules(self, rules):
        converted_rules = {}
        for rid, (pre, post, vars) in rules.items():
            pre = pre.copy()
            attributes = {}
            types_to_remove = set()
            types_to_preserve = set()
            for c in pre.concepts():
                attributes[c] = pre.types(c)
            for s, t, o, i in pre.predicates(predicate_type='type'):
                nr = pre.related(i)
                if not nr:
                    pre.remove(predicate_id=i)
                    attributes.pop(i)
                    vars.discard(i)
                    types_to_remove.add(o)
                else:
                    types_to_preserve.update({s, o})
            for type in types_to_remove - types_to_preserve:
                pre.remove(type)
                attributes.pop(type)
                vars.discard(type)
            pre.remove('type')
            attributes.pop('type')
            precondition = pre.to_graph()
            for node, types in attributes.items():
                precondition.data(node)['attributes'] = types
            for var in vars:
                precondition.data(var)['var'] = True
                precondition.data(var)['attributes'].discard(var)
            converted_rules[rid] = precondition
        return converted_rules

    def _convert_facts(self, facts):
        attributes = {}
        quantities = set()
        types_to_remove = set()
        types_to_preserve = set()
        for c in facts.concepts():
            attributes[c] = facts.types(c)
            if isinstance(c, int) or isinstance(c, float):
                quantities.add(c)
        for s, t, o, i in facts.predicates(predicate_type='type'):
            if not facts.related(i):
                facts.remove(predicate_id=i)
                attributes.pop(i)
                types_to_remove.add(o)
            else:
                types_to_preserve.update({s,o})
        for type in types_to_remove - types_to_preserve:
            facts.remove(type)
            attributes.pop(type)
        facts.remove('type')
        attributes.pop('type')
        facts_graph = facts.to_graph()
        for node, types in attributes.items():
            facts_graph.data(node)['attributes'] = types
        for node in quantities:
            facts_graph.data(node)['num'] = node
        return facts_graph

    def infer(self, facts, dynamic_rules=None, cached=True):
        # Todo: allow inference using only provided rules (not cached rules)
        facts_concept_graph = ConceptGraph(facts, namespace=(facts._ids if isinstance(facts, ConceptGraph) else "facts_"))
        facts_graph = self._convert_facts(facts_concept_graph)
        if dynamic_rules is not None and not isinstance(dynamic_rules, dict):
            dynamic_rules = ConceptGraph(dynamic_rules).rules()
        elif dynamic_rules is None:
            dynamic_rules = {}
        all_rules = {**self.rules, **dynamic_rules}
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        converted_rules = Bimap({**self._preloaded_rules, **dynamic_converted_rules})
        sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        sols = {converted_rules.reverse()[precondition]: sols for precondition, sols in sols.items()}
        sols = {rule_id: (all_rules[rule_id][0], all_rules[rule_id][1], sol_ls) for rule_id, sol_ls in sols.items()}
        return sols

    def apply(self, inferences):
        implications = {}
        for rid, (pre, post, sols) in inferences.items():
            for sol in sols:
                solution_swap = ConceptGraph(namespace=post._ids)
                final_implication = ConceptGraph(namespace='implied')
                for pred in post.predicates():
                    pred = [sol.get(x, x) for x in pred]
                    solution_swap.add(*pred)
                for concept in post.concepts():
                    concept = sol.get(concept, concept)
                    solution_swap.add(concept)
                final_implication.concatenate(solution_swap)
                implications.setdefault(rid, []).append((sol, final_implication))
        return implications

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))