from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec

from GRIDD.data_structures.graph_matching.graph_matching_engine import GraphMatchingEngine
from structpy.map import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *
from GRIDD.utilities.utilities import Counter

from GRIDD.utilities.profiler import profiler as p
import time

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
            precondition = self._flatten_types(pre, precondition, for_query=True)
            for node in categories:
                precondition.data(node)['category'] = True
            for node in specifics:
                precondition.data(node)['specific'] = True
            for var in vars: # vars includes both pre and post vars
                if precondition.has(var):
                    precondition.data(var)['var'] = True
            converted_rules[rid] = precondition
        return converted_rules

    def _convert_facts(self, facts, facts_types):
        # p.start('to digraph')
        facts_graph = facts.to_infcompat_graph()
        # p.next(f'flatten types ({len(facts_types)} concepts)')
        facts_graph = self._flatten_types(facts, facts_graph, facts_types)
        # p.next('quantities')
        quantities = {c for c in facts.concepts() if isinstance(c, (float, int))}
        for node in quantities: facts_graph.data(node)['num'] = node
        # p.stop()
        return facts_graph

    def _flatten_types(self, orig_cg, cg, types=None, for_query=False):
        counter = 0
        if types is None:
            types = orig_cg.types()
        for c in orig_cg.concepts():
            handled = set()
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
                            cg.data(i)['var'] = False
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
        # p.start('facts graph copy')
        # facts_concept_graph = ConceptGraph(facts, namespace=(facts._ids if isinstance(facts, ConceptGraph) else "facts_"))
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
            for node in precondition.nodes():
                if 'category' in precondition.data(node):
                    categories.add(node)
                if 'specific' in precondition.data(node):
                    specifics.add(node)
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
                    if precondition_cg.has(predicate_id=variable):
                        var_conf = precondition_cg.features.get_confidence(variable, None)
                        val_conf = facts_concept_graph.features.get_confidence(value, 1.0)
                        if precondition_cg.type(variable) != TYPE and ((var_conf is None and val_conf <= 0) or \
                           (var_conf is not None and var_conf > 0 and val_conf - var_conf < 0) or \
                           (var_conf is not None and var_conf < 0 and val_conf - var_conf > 0)):
                            break
                    else:
                        turn_pos = precondition_cg.features[variable].get(TURN_POS, None)
                        if turn_pos is not None:
                            if aux_state is None:
                                print('[WARNING] Found turn checking rule but no aux state was passed to infer()')
                                break
                            current_turn = aux_state.get('turn_index', None)
                            if current_turn is not None:
                                relative_turn_check = int(current_turn) - int(turn_pos)
                                if str(relative_turn_check) != value:  # post process filter of turn checking rules
                                    break
                            else:  # no turn information can be found in aux state so cannot do any turn checking
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