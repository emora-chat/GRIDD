from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *
from GRIDD.utilities.utilities import Counter


class InferenceEngine:

    def __init__(self, rules=None, namespace=None, device='cpu'):
        self.rules = {}
        self._preloaded_rules = {}
        self.counter = Counter()
        self._next = lambda x: x + 1
        self.matcher = GraphMatchingEngine(device=device)
        if rules is not None:
            self.add(rules, namespace)

    def add(self, rules, namespace):
        if namespace is None:
            raise Exception('namespace param cannot be None!')
        if not isinstance(rules, dict):
            rules = ConceptGraph(rules, namespace='r_')
            assertions(rules)
            rules = rules.rules()
        renamed_rules = {('rule%d'%self._next(self.counter) if k.startswith(namespace) else k): v for k,v in rules.items()}
        for rule in renamed_rules:
            if rule in self.rules:
                raise ValueError(f'Rule by name {rule} already exists!')
        new_rules = self._convert_rules(renamed_rules)
        self.rules.update(renamed_rules)
        self._preloaded_rules.update(new_rules)
        self.matcher.add_queries(*list(new_rules.values()))

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
            precondition = pre.to_infcompat_graph()
            precondition = self._flatten_types(pre, precondition, insert_vars=True)
            for node in categories:
                precondition.data(node)['category'] = True
            for node in specifics:
                precondition.data(node)['specific'] = True
            for var in vars: # vars includes both pre and post vars
                if precondition.has(var):
                    precondition.data(var)['var'] = True
            converted_rules[rid] = precondition
        return converted_rules

    def _convert_facts(self, facts):
        quantities = set()
        for c in facts.concepts():
            if isinstance(c, int) or isinstance(c, float):
                quantities.add(c)
        facts_graph = facts.to_infcompat_graph()
        facts_graph = self._flatten_types(facts, facts_graph)
        for node in quantities:
            facts_graph.data(node)['num'] = node
        return facts_graph

    def _flatten_types(self, orig_cg, cg, insert_vars=False):
        counter = 0
        for c in orig_cg.concepts():
            type_predicates = list(orig_cg.type_predicates(c))
            handled = set()
            if orig_cg.has(predicate_id=c):
                pred_type = orig_cg.type(c)
                if pred_type != TYPE:  # add predicate type as a type predicate, if not type predicate itself
                    handled.add(pred_type)
                    new_id = '__virt_%d' % counter
                    counter += 1
                    cg.add(new_id, c, 's')
                    cg.add(new_id, TYPE, 't')
                    cg.add(new_id, pred_type, 'o')
                    if insert_vars: cg.data(new_id)['var'] = True
                for s, t, o, i in type_predicates:
                    if s == c: handled.add(o) # if there is a direct type predicate to o, do not add any indirect links
                for s, t, o, i in type_predicates:
                    if s != c and o not in handled:  # only indirect type links need to be manually added
                        handled.add(o)
                        new_id = '__virt_%d' % counter
                        counter += 1
                        cg.add(new_id, c, 's')
                        cg.add(new_id, t, 't')
                        cg.add(new_id, o, 'o')
                        if insert_vars: cg.data(new_id)['var'] = True
            else:
                for s, t, o, i in type_predicates:
                    if s != c and o not in handled:
                        handled.add(o)
                        new_id = '__virt_%d' % counter
                        counter += 1
                        cg.add(new_id, c, 's')
                        cg.add(new_id, t, 't')
                        cg.add(new_id, o, 'o')
                        if insert_vars: cg.data(new_id)['var'] = True
        return cg

    def infer(self, facts, dynamic_rules=None, cached=True):
        """
        facts should have already had all types pulled (aka don't do type pull within inference engine)
        """
        print('new inference engine!!!')
        facts_concept_graph = ConceptGraph(facts, namespace=(facts._ids if isinstance(facts, ConceptGraph) else "facts_"))
        facts_types = facts_concept_graph.types()
        facts_graph = self._convert_facts(facts_concept_graph)
        if dynamic_rules is not None and not isinstance(dynamic_rules, dict):
            dynamic_rules = ConceptGraph(dynamic_rules).rules()
        elif dynamic_rules is None:
            dynamic_rules = {}
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        if cached: #cached rules are already preloaded, cache is only true when there are no dynamic rules
            converted_rules = Bimap({})
        else:
            all_rules = dynamic_rules
            converted_rules = Bimap(dynamic_converted_rules)
        if len(converted_rules) == 0:
            return {}
        all_sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        sorted_all_sols = {}
        for k2 in converted_rules:
            for k,v in all_sols.items():
                rule = converted_rules.reverse()[k]
                if rule == k2:
                    sorted_all_sols[k] = v
        solutions = {}
        for precondition, sols in sorted_all_sols.items():
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
                virtual_preds = {}
                for variable, value in sol.items():
                    if value.startswith('__virt_'):
                        s = next(iter(facts_graph.out_edges(value, 's')))[1]
                        t = next(iter(facts_graph.out_edges(value, 't')))[1]
                        o = next(iter(facts_graph.out_edges(value, 'o')))[1]
                        virtual_preds[value] = (s, t, o)
                    if precondition_cg.has(predicate_id=variable):
                        var_conf = precondition_cg.features.get_confidence(variable, None)
                        val_conf = facts_concept_graph.features.get_confidence(value, 1.0)
                        if precondition_cg.type(variable) != TYPE and ((var_conf is None and val_conf <= 0) or \
                           (var_conf is not None and var_conf > 0 and val_conf - var_conf < 0) or \
                           (var_conf is not None and var_conf < 0 and val_conf - var_conf > 0)):
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
                    solset.append((sol, virtual_preds))
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
    # print(InferenceEngineSpec.verify(InferenceEngine))

    engine = InferenceEngine()

    rules = '''
    xsm=see(x=person(), m=movie())
    mta=type(m, action)
    ->
    watch(x, m)
    ;
    '''

    facts = '''
    person=(living_thing)
    jane=person()
    jtw=type(jane, woman)
    avengers=movie()
    ata=type(avengers, action)
    see=(view)
    jsa=see(jane, avengers)
    '''

    rule_cg = engine._convert_rules(ConceptGraph(rules).rules())
    fact_cg = engine._convert_facts(ConceptGraph(facts))
    x = 1

    results = engine.infer(facts, rules)
    for k,v in results.items():
        print(k, v)

    rules2 = '''
    xsm=view(x=living_thing(), m=movie())
    mta=type(m, action)
    ->
    watch(x, m)
    ;
    '''

    results = engine.infer(facts, rules2)
    for k,v in results.items():
        print(k, v)


    rules3 = '''
    econgrat(emora, X/object())
    t/type(X, predicate)
    ->
    like(emora, t)
    '''

    facts = '''
    econgrat(emora, wm2)
    wm2=buy(user,wm5=house())
    user=(person)
    person=(living_thing)
    buy=(predicate)
    predicate=(object)
    '''

    results = engine.infer(facts, rules3)
    for k,v in results.items():
        print(k, v)


    def apply(inferences):
        implications = {}
        for rid, (pre, post, sols) in inferences.items():
            for sol, virtual_preds in sols:
                implied = ConceptGraph(namespace=post._ids)
                for pred in post.predicates():
                    if pred[3] not in sol:
                        # if predicate instance is not in solutions, add to implication; otherwise, it already exists in WM
                        new_pred = []
                        for x in pred:
                            m = sol.get(x, x)
                            if m.startswith('__virt_'):
                                m = implied.add(*virtual_preds[m])
                                sol[x] = m
                            new_pred.append(m)
                        implied.add(*new_pred)
                for concept in post.concepts():
                    concept = sol.get(concept, concept)
                    implied.add(concept)
                for s, t, l in post.metagraph.edges():
                    implied.metagraph.add(sol.get(s, s), sol.get(t, t), l)
                for s in post.metagraph.nodes():
                    implied.metagraph.add(sol.get(s, s))
                features = {sol.get(k, k): v for k, v in post.features.items()}
                implied.features.update(features)
                implications.setdefault(rid, []).append((sol, implied))
        return implications

    imps = apply(results)
    x = 1