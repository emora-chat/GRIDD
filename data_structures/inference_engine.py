from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.concept_graph import ConceptGraph
import time

class InferenceEngine:

    def __init__(self, *rules, device='cpu'):
        self.rules = KnowledgeParser.rules(*rules)
        st = time.time()
        self.preloaded_rules = self._convert_rules(self.rules)
        print('Static Rule Graphs to NetworkX - Elapsed: %.3f' % (time.time() - st))
        self.matcher = GraphMatchingEngine(device=device)

    def _convert_rules(self, rules):
        converted_rules = {}
        for rid, (pre, post) in rules.items():
            pre = pre.copy()
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
        return converted_rules

    def infer(self, facts, *rules):
        st = time.time()
        facts_concept_graph = KnowledgeParser.from_data(facts, namespace='facts_').copy()
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
        # print('Fact Graph to NetworkX - Elapsed: %.3f'%(time.time()-st))

        st = time.time()
        dynamic_rules = KnowledgeParser.rules(*rules)
        rules = Bimap({**self.rules, **dynamic_rules})
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        converted_rules = Bimap({**self.preloaded_rules, **dynamic_converted_rules})
        # print('Dynamic Rule Graphs to NetworkX - Elapsed: %.3f' % (time.time() - st))

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