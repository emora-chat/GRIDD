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
        for rid, (pre, post) in rules.items():
            pre = pre.copy()
            varset = set()
            attributes = {}
            confidences = {}
            numbers = {}    # {concept: {comparator: threshold}}
            comparators = set()
            thresholds = set()
            types = set()
            for s, t, o, i in pre.predicates(predicate_type='var'):
                varset.add(s)
                pre.remove(predicate_id=i)
            pre.remove('var')
            for cmp in ['gt', 'lt', 'ge', 'le', 'ne', 'eq']:
                for s, t, o, i in pre.predicates(predicate_type=cmp):
                    numbers.setdefault(s, {})[cmp] = t if isinstance(t, int) or isinstance(t, float) else 0
                    comparators.add(i)
                    thresholds.add(t)
            for ci in comparators:
                pre.remove(predicate_id=ci)
            for tc in thresholds:
                pre.remove(tc)
            for p in pre.predicates():
                if 'c' in pre.features[p]:
                    confidence = pre.features[p]['c']
                    confidences[p] = confidence
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
            for node, conf in confidences.items():
                if conf > 0:
                    precondition.data(node)['ge'] = conf
                elif conf < 0:
                    precondition.data(node)['le'] = conf
            for node, threshs in numbers.items():
                for comp, thresh in threshs.items():
                    precondition.data(node)[cmp] = thresh
            converted_rules[rid] = precondition
        return converted_rules

    def infer(self, facts, *rules):
        facts_concept_graph = KnowledgeParser.from_data(facts, namespace='facts_').copy()
        attributes = {}
        confidences = {}
        quantities = set()
        types = set()
        for c in facts_concept_graph.concepts():
            attributes[c] = facts_concept_graph.supertypes(c)
            if isinstance(c, int) or isinstance(c, float):
                quantities.add(c)
        for s, t, o, i in facts_concept_graph.predicates():
            if 'c' in facts_concept_graph.features[i]:
                confidences[i] = facts_concept_graph.features[i]['c']
            else:
                confidences[i] = 0
        for s, t, o, i in facts_concept_graph.predicates(predicate_type='type'):
            facts_concept_graph.remove(predicate_id=i)
            types.add(o)
        for type in types:
            facts_concept_graph.remove(type)
        facts_concept_graph.remove('type')
        facts_graph = facts_concept_graph.to_graph()
        for node, types in attributes.items():
            facts_graph.data(node)['attributes'] = types
        for node, conf in confidences.items():
            facts_graph.data(node)['num'] = conf
        for node in quantities:
            facts_graph.data(node)['num'] = node
        dynamic_rules = KnowledgeParser.rules(*rules)
        rules = Bimap({**self.rules, **dynamic_rules})
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        converted_rules = Bimap({**self.preloaded_rules, **dynamic_converted_rules})
        sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        sols = {converted_rules.reverse()[precondition]: sols for precondition, sols in sols.items()}
        sols = {rule_id: (rules[rule_id][0], rules[rule_id][1], sol_ls) for rule_id, sol_ls in sols.items()}
        return sols

    def apply(self, facts=None, *rules, solutions=None):
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

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))