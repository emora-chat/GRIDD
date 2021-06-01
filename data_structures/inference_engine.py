from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *


class InferenceEngine:

    def __init__(self, rules=None, device='cpu'):
        self.rules = {}
        self._preloaded_rules = {}
        if rules is not None:
            self.add(rules)
        self.matcher = GraphMatchingEngine(device=device)

    def add(self, rules):
        if not isinstance(rules, dict):
            rules = ConceptGraph(rules, namespace='r_')
            assertions(rules)
            rules = rules.rules()
        for rule in rules:
            if rule in self.rules:
                raise ValueError(f'Rule by name {rule} already exists!')
        new_rules = self._convert_rules(rules)
        self.rules.update(rules)
        self._preloaded_rules.update(new_rules)

    def _convert_rules(self, rules):
        converted_rules = {}
        for rid, structure in rules.items():
            if len(structure) == 3:
                pre, _, vars = structure
            else:
                pre, vars = structure
            pre = pre.copy()
            categories = set()
            for s, t, _, i in set(pre.predicates(predicate_type='category')):
                categories.add(s)
                pre.remove(predicate_id=i)
            if pre.has('category'):
                pre.remove(predicate_type='category')
            if pre.has('category'):
                pre.remove('category')
            specifics = set()
            for s, t, _, i in set(pre.predicates(predicate_type='specific')):
                specifics.add(s)
                pre.remove(predicate_id=i)
            if pre.has('specific'):
                pre.remove(predicate_type='specific')
            if pre.has('specific'):
                pre.remove('specific')
            attributes = {}
            types_to_remove = set()
            types_to_preserve = set()
            for c in pre.concepts():
                attributes[c] = pre.types(c)
            for s, t, o, i in pre.predicates(predicate_type='type'):
                nr = pre.subjects(i)
                nr.update(pre.objects(i))
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
            if 'type' in attributes:
                attributes.pop('type')
            precondition = pre.to_graph()
            for node, types in attributes.items():
                precondition.data(node)['attributes'] = types
            for node in categories:
                precondition.data(node)['category'] = True
            for node in specifics:
                precondition.data(node)['specific'] = True
            edges = set(precondition.edges(label='t'))
            for s,t,l in edges:
                if precondition.has(t):
                    precondition.remove(t)
            for var in vars: # vars includes both pre and post vars
                if precondition.has(var):
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
            nr = facts.subjects(i)
            nr.update(facts.objects(i))
            if not nr:
                facts.remove(predicate_id=i)
                attributes.pop(i)
                types_to_remove.add(o)
            else:
                types_to_preserve.update({s,o})
        for type in types_to_remove - types_to_preserve:
            facts.remove(type)
            attributes.pop(type)
        facts.remove('type')
        if 'type' in attributes:
            attributes.pop('type')
        facts_graph = facts.to_graph()
        for node, types in attributes.items():
            facts_graph.data(node)['attributes'] = types
        edges = set(facts_graph.edges(label='t'))
        for s, t, l in edges:
            if facts_graph.has(t):
                facts_graph.remove(t)
        for node in quantities:
            facts_graph.data(node)['num'] = node
        return facts_graph

    def infer(self, facts, dynamic_rules=None, cached=True):
        facts_concept_graph = ConceptGraph(facts, namespace=(facts._ids if isinstance(facts, ConceptGraph) else "facts_"))
        facts_types = facts_concept_graph.types()
        facts_graph = self._convert_facts(facts_concept_graph)
        if dynamic_rules is not None and not isinstance(dynamic_rules, dict):
            dynamic_rules = ConceptGraph(dynamic_rules).rules()
        elif dynamic_rules is None:
            dynamic_rules = {}
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        if cached:
            all_rules = {**self.rules, **dynamic_rules}
            converted_rules = Bimap({**self._preloaded_rules, **dynamic_converted_rules})
        else:
            all_rules = dynamic_rules
            converted_rules = Bimap(dynamic_converted_rules)
        # print('Nodes, Edges: ', len(facts_graph.nodes()), len(facts_graph.edges()))
        if len(converted_rules) == 0:
            return {}
        all_sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        solutions = {}
        for precondition, sols in all_sols.items():
            categories = set()
            specifics = set()
            for node in precondition.nodes():
                if 'category' in precondition.data(node):
                    categories.add(node)
                if 'specific' in precondition.data(node):
                    specifics.add(node)
            precondition_id = converted_rules.reverse()[precondition]
            precondition_cg = all_rules[precondition_id][0]
            solset = []
            for sol in sols:
                for variable, value in sol.items():
                    if precondition_cg.has(predicate_id=variable):
                        var_conf = precondition_cg.features.get_confidence(variable, None)
                        val_conf = facts_concept_graph.features.get_confidence(value, 1.0)
                        if (var_conf is None and val_conf <= 0) or \
                           (var_conf is not None and var_conf > 0 and val_conf - var_conf < 0) or \
                           (var_conf is not None and var_conf < 0 and val_conf - var_conf > 0):
                            break
                    if variable in categories:
                        not_category = True
                        value_types = facts_types.get(value, set())
                        if value.startswith(facts.id_map().namespace) or value.startswith(KB):
                            # remove non-specific concepts from their type sets
                            # e.g. an instance of name is removed but the specified name 'sarah' is not
                            value_types -= {value}
                        for t in precondition_cg.types(variable) - {variable}:
                            if value_types == facts_types.get(t, set()):
                                not_category = False
                        if not_category:
                            break
                    if variable in specifics:
                        not_specific = False
                        value_types = facts_types.get(value, set())
                        if value.startswith(facts.id_map().namespace) or value.startswith(KB):
                            value_types -= {value}
                        for t in precondition_cg.types(variable) - {variable}:
                            if value_types <= facts_types.get(t, set()):
                                not_specific = True
                        if not_specific:
                            break
                else:
                    solset.append(sol)
            if len(solset) > 0:
                solutions[precondition_id] = solset
        final_sols = {}
        for rule_id, sol_ls in solutions.items():
            if len(all_rules[rule_id]) == 3:
                final_sols[rule_id] = (all_rules[rule_id][0], all_rules[rule_id][1], sol_ls)
            else:
                final_sols[rule_id] = (all_rules[rule_id][0], sol_ls)
        return final_sols

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))