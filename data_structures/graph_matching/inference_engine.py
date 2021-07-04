
from GRIDD.data_structures.graph_matching.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *
from GRIDD.utilities.utilities import Counter

from GRIDD.utilities.profiler import profiler as p


class InferenceEngine:

    def __init__(self, rules=None, namespace=None, device='cpu'):
        self.rules = {}
        self._preloaded_rules = Bimap()
        self.counter = Counter()
        self._next = lambda x: x + 1
        self.matcher = GraphMatchingEngine(device=device)
        if rules is not None:
            self.add(rules, namespace)
            self.matcher.process_queries()

    def add(self, rules, namespace):
        if namespace is None:
            raise Exception('namespace param cannot be None!')
        if not isinstance(rules, dict):
            rules = ConceptGraph(rules, namespace=namespace)
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
            for s, t, _, i in set(pre.predicates(predicate_type='_category')):
                categories.add(s)
                pre.remove(predicate_id=i)
            if pre.has('_category'):
                pre.remove(predicate_type='_category')
                if pre.has('_category'):
                    pre.remove('_category')
            specifics = set()
            for s, t, _, i in set(pre.predicates(predicate_type='_specific')):
                specifics.add(s)
                pre.remove(predicate_id=i)
            if pre.has('_specific'):
                pre.remove(predicate_type='_specific')
                if pre.has('_specific'):
                    pre.remove('_specific')
            exists = set()
            for s, t, _, i in set(pre.predicates(predicate_type='_exists')):
                exists.add(s)
                pre.remove(predicate_id=i)
            if pre.has('_exists'):
                pre.remove(predicate_type='_exists')
                if pre.has('_exists'):
                    pre.remove('_exists')
            precondition = pre.to_infcompat_graph()
            precondition = self._flatten_types(pre, precondition, for_query=True)
            for node in categories:
                precondition.data(node)['category'] = True
            for node in specifics:
                precondition.data(node)['specific'] = True
            for node in exists:
                precondition.data(node)['exists'] = True
            for var in vars: # vars includes both pre and post vars
                if precondition.has(var):
                    precondition.data(var)['var'] = True
            converted_rules[rid] = precondition
        return converted_rules

    def _convert_facts(self, facts, facts_types):
        """
        If dynamic_rules are passed, they are to be removed from facts graph
        """
        p.start('to digraph')
        facts_graph = facts.to_infcompat_graph()
        p.next(f'flatten types ({len(facts_types)} concepts)')
        facts_graph = self._flatten_types(facts, facts_graph, facts_types)
        p.next('quantities')
        quantities = {c for c in facts.concepts() if isinstance(c, (float, int))}
        for node in quantities: facts_graph.data(node)['num'] = node
        p.stop()
        return facts_graph

    def _flatten_types(self, orig_cg, cg, types=None, for_query=False):
        counter = 0
        if types is None:
            types = orig_cg.types()
        for c in orig_cg.concepts():
            handled = set()
            if not for_query:
                # add self-loop type
                cg.add(c, c, 't')
            if orig_cg.has(predicate_id=c):
                pred_type = orig_cg.type(c)
                if pred_type != TYPE:  # add predicate type as a type, if not type predicate itself
                    handled.add(pred_type)
                    cg.add(c, pred_type, 't') # there would be an explicit type predicate instance for any predicate type instances that are arguments of different predicate, so not handled here
            for s, t, o, i in orig_cg.predicates(c, predicate_type=TYPE):  # an explicit type predicate to o
                if o not in handled:
                    handled.add(o)
                    if for_query:
                        if not list(orig_cg.predicates(subject=i)) and not list(orig_cg.predicates(object=i)):
                            # remove predicate instance, since it is not an argument of anything
                            if i in cg.node_data:
                                del cg.node_data[i]
                            cg.remove(i)
                            # add direct link instead
                            cg.add(s, o, 't')
                    else:
                        # add direct type if creating data graph
                        cg.add(s, o, 't')
            for t in types.get(c, []) - {c}:
                if t != TYPE and t not in handled: # only indirect type links need to be manually added, since they do not exist as predicate instances in the ConceptGraph
                    handled.add(t)
                    new_id = '__virt_%d' % counter
                    counter += 1
                    cg.add(new_id, c, 's')
                    cg.add(new_id, TYPE, 't')
                    cg.add(new_id, t, 'o')
                    if for_query:
                        cg.data(new_id)['var'] = True
                    else: # add direct type to only if creating data graph
                        cg.add(c, t, 't')
        return cg

    def infer(self, facts_concept_graph, aux_state=None, dynamic_rules=None, cached=True):
        """
        facts should have already had all types pulled (aka don't do type pull within inference engine)
        """
        p.start('facts graph types')
        facts_types = facts_concept_graph.types()
        p.next('convert facts graph')
        facts_graph = self._convert_facts(facts_concept_graph, facts_types)
        p.next('process dynamic rules')
        if dynamic_rules is not None and not isinstance(dynamic_rules, dict):
            dynamic_rules = ConceptGraph(dynamic_rules).rules()
        elif dynamic_rules is None:
            dynamic_rules = {}
        dynamic_converted_rules = self._convert_rules(dynamic_rules)
        if cached: #cached rules are already preloaded, cache is only true when there are no dynamic rules
            converted_rules = Bimap({})
            all_rules = self.rules
        else:
            all_rules = dynamic_rules
            converted_rules = Bimap(dynamic_converted_rules)
        # if len(converted_rules) == 0:
        #     return {}
        p.next('match')
        all_sols = self.matcher.match(facts_graph, *list(converted_rules.values()))
        p.next('postprocess solutions')
        solutions = {}
        for precondition, sols in all_sols.items():
            categories = set()
            specifics = set()
            exists = set()
            for node in precondition.nodes():
                if 'category' in precondition.data(node):
                    categories.add(node)
                if 'specific' in precondition.data(node):
                    specifics.add(node)
                if 'exists' in precondition.data(node):
                    exists.add(node)
            if not cached:
                precondition_id = converted_rules.reverse()[precondition]
            else:
                precondition_id = self._preloaded_rules.reverse()[precondition]
            precondition_cg = all_rules[precondition_id][0]
            precondition_types = precondition_cg.types()
            solset = []
            for sol in sols:
                virtual_preds = {}
                for variable, value in sol.items():
                    if value.startswith('__virt_'):
                        s = next(iter(facts_graph.out_edges(value, 's')))[1]
                        t = next(iter(facts_graph.out_edges(value, 't')))[1]
                        o = next(iter(facts_graph.out_edges(value, 'o')))[1]
                        virtual_preds[value] = (s, t, o)
                    # confidence checking
                    if precondition_cg.has(predicate_id=variable):
                        # if `exists` monopredicate, then does not matter what confidence predicate is or is not there so do not need to check
                        if variable not in exists and not precondition_cg.has(variable, 'not') and not precondition_cg.has(variable, 'maybe'):
                            # make sure solution also doesn't have `not` and `maybe` monopredicates
                            if facts_concept_graph.has(value, 'not') or facts_concept_graph.has(value, 'maybe'):
                                break
                    # turn checking
                    turn_check_failed = False
                    for check_turn_type, turn_type in {(ETURN_POS, ETURN), (UTURN_POS, UTURN)}:
                        turn_pos = precondition_cg.features.get(variable, {}).get(check_turn_type, set())
                        if len(turn_pos) > 0:
                            if aux_state is None:
                                print('[WARNING] Found turn checking rule but no aux state was passed to infer()')
                                turn_check_failed = True
                                break
                            current_turn = int(aux_state.get('turn_index', None))
                            if current_turn is not None:
                                relative_turn_checks = {current_turn - t for t in turn_pos}
                                match_turn = facts_concept_graph.features.get(value, {}).get(turn_type, set())
                                if not relative_turn_checks.issubset(match_turn):  # post process filter of turn checking rules
                                    turn_check_failed = True
                                    break
                            else:  # no turn information can be found in aux state so cannot do any turn checking thus invalidating this rule
                                turn_check_failed = True
                                break
                    if turn_check_failed:
                        break
                    if variable in categories:
                        not_category = True
                        value_types = facts_types.get(value, set())
                        if value.startswith(facts_concept_graph.id_map().namespace) or value.startswith(KB):
                            # remove non-specific concepts from their type sets
                            # e.g. an instance of name is removed but the specified name 'sarah' is not
                            value_types -= {value}
                        for t in precondition_types.get(variable, set()) - {variable}:
                            if value_types == facts_types.get(t, set()):
                                not_category = False
                        if not_category:
                            break
                    if variable in specifics:
                        not_specific = False
                        value_types = facts_types.get(value, set())
                        if value.startswith(facts_concept_graph.id_map().namespace) or value.startswith(KB):
                            value_types -= {value}
                        for t in precondition_types.get(variable, set()) - {variable}:
                            if value_types <= facts_types.get(t, set()):
                                not_specific = True
                        if not_specific:
                            break
                else:
                    # postprocess type predicates
                    counter = 1
                    for s,t,o,i in precondition_cg.predicates(predicate_type=TYPE):
                        if i not in sol:
                            # lookup matching type instance based on assignments in sol
                            matched_types = list(precondition_cg.predicates(sol.get(s,s), TYPE, sol.get(o,o)))
                            number_matched_types = len(matched_types)
                            if number_matched_types == 1:
                                # direct type match found
                                sol[i] = matched_types[0][3]
                            elif number_matched_types == 0 :
                                # must be indirect type match
                                sol[i] = '__virt_post_%d'%counter
                                counter += 1
                                virtual_preds[sol[i]] = (sol.get(s,s), TYPE, sol.get(o,o))
                            elif number_matched_types > 1 :
                                print("[WARNING] Solution identified but >1 matching type predicate found in datagraph for a type predicate in precondition!")
                    solset.append((sol, virtual_preds))
            if len(solset) > 0:
                solutions[precondition_id] = solset
        final_sols = {}
        for rule_id, sol_ls in solutions.items():
            if len(all_rules[rule_id]) == 3:
                final_sols[rule_id] = (all_rules[rule_id][0], all_rules[rule_id][1], sol_ls)
            else:
                final_sols[rule_id] = (all_rules[rule_id][0], sol_ls)
        p.stop()
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

    results = engine.infer(facts, rules, cached=False)
    for k,v in results.items():
        print(k, v)

    rules2 = '''
    xsm=view(x=living_thing(), m=movie())
    mta=type(m, action)
    ->
    watch(x, m)
    ;
    '''

    results = engine.infer(facts, rules2, cached=False)
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

    results = engine.infer(facts, rules3, cached=False)
    for k,v in results.items():
        print(k, v)

    engine = InferenceEngine(rules3, 'rules_')
    results = engine.infer(facts)
    for k,v in results.items():
        print(k, v)