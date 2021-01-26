import json, time
from pyswip import Prolog, Variable
from utilities import identification_string, CHARS
from structpy.map.bijective.bimap import Bimap
from data_structures.concept_graph import ConceptGraph
from data_structures.implication_rule import ImplicationRule
import utilities as util

def infer(concept_graph, inference_rules):

    class PyswipEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Variable):
                return 'PyswipVariable(%d)'%obj.handle
            elif isinstance(obj, bytes):
                return '"%s"'%obj.decode("utf-8")
            return json.JSONEncoder.default(self, obj)

    kg_rules = to_knowledge_prolog(concept_graph)
    prolog = Prolog()
    for rule in kg_rules:
        prolog.assertz(rule)

    solutions = {}
    for rule_id, rule in inference_rules.items():
        inference_query, inference_map = to_query_prolog(rule.precondition)
        solns = list(prolog.query(inference_query))
        parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
        solutions[rule] = []
        for match in parsed_solns:
            variable_assignments = {}
            for key, value in inference_map.items():
                variable_assignments[key] = match[value]
            solutions[rule].append(variable_assignments)

    for rule in kg_rules:
        prolog.retract(rule)

    return solutions


def generate_inference_graphs(cg, ordered_rule_ids=None):
    """
    Extracts the inference rules and their corresponding implications in the given
    concept graph `cg`.

    If the list of ordered_rule_ids is given,
    then the rules are formed in the specified order to ensure they are matched in priority order.

    :returns dict<rule_id: ImplicationRule object>
    """
    inferences, implications = {}, {}
    id_maps = {}

    if ordered_rule_ids is not None:
        for situation_node in ordered_rule_ids:
            inferences[situation_node] = ConceptGraph(namespace='pre', concepts=['var'])
            implications[situation_node] = ConceptGraph(namespace='post', concepts=['var'])
            id_maps[situation_node] = {}

    for situation_node, _, constraint, _ in cg.predicates(predicate_type='pre'):
        if situation_node not in inferences:
            inferences[situation_node] = ConceptGraph(namespace='pre', concepts=['var'])
            id_maps[situation_node] = {}
        _transfer_concept(cg, inferences[situation_node], constraint, id_maps[situation_node])

    for situation_node, _, implication, _ in cg.predicates(predicate_type='post'):
        if situation_node not in implications:
            implications[situation_node] = ConceptGraph(namespace='post')
        _transfer_concept(cg, implications[situation_node], implication, id_maps[situation_node])

    rules = {}
    for situation_node in inferences:
        rules[situation_node] = ImplicationRule(inferences[situation_node], implications[situation_node], situation_node)
    return rules


def _transfer_concept(cg, new_graph, concept_id, id_map):
    """
    Adds the concept `concept_id` from `cg` to `new_graph`
    """
    if cg.has(predicate_id=concept_id): # predicate instance
        components = [cg.subject(concept_id), cg.type(concept_id), cg.object(concept_id)]
        mapped_components = []
        for comp in components:
            if comp is not None:
                comp = util.map(new_graph, comp, cg._namespace, id_map)
            mapped_components.append(comp)
        new_graph.add(*mapped_components, predicate_id=util.map(new_graph, concept_id, cg._namespace, id_map))
    else: # entity instance
        util.map(new_graph, concept_id, cg._namespace, id_map)


def to_knowledge_prolog(cg):
    """
    Convert cg to knowledge rules for Prolog.
    """
    type_rules = []
    rules = []

    # Flatten ontology in `tmp` copy of cg
    tmp = ConceptGraph(predicates=cg.predicates())
    for concept in tmp.concepts():
        visited = set()
        stack = [concept]
        while stack:
            s = stack.pop()
            for s, t, o, i in tmp.predicates(s, predicate_type='type'):
                if not tmp.has(concept, t, o):
                    tmp.add(concept, t, o)
                if o not in visited:
                    visited.add(o)
                    stack.append(o)

    one_non_ont_predicate = False
    for s, t, o, i in tmp.predicates():
        if o is not None:   # bipredicate
            if t == 'type':
                type_rules.append('type(%s,%s)' % (s, o))
            else:
                rules.append('predinst(%s(%s,%s),%s)' % (t, s, o, i))
                one_non_ont_predicate = True
        else:               # monopredicate
            if t not in {'var', 'is_type'}:
                rules.append('predinst(%s(%s),%s)' % (t, s, i))
                one_non_ont_predicate = True
    if not one_non_ont_predicate: # if there is no predinst in knowledge prolog, a prolog query using predinst causes error to be thrown (predinst is not defined)
        rules.append('predinst(xtestx(xax, xbx), xnx)')
    return type_rules + rules


def to_query_prolog(cg):
    """
    Convert cg to query rules for Prolog, where `cg` contains one inference rule specification.

    :return
        - string prolog query representation of cg
        - dict<cg variable node id: prolog variable string>

    """
    next = 0
    map = Bimap()
    vars = set()
    rules = []
    for subject, pred_type, object, inst_id in cg.predicates():
        if object is not None:              # bipredicate
            if pred_type == 'type':
                if subject not in map:
                    if cg.has(subject, 'var'):
                        map[subject] = identification_string(next, chars=CHARS)
                        vars.add(subject)
                        next += 1
                    else:
                        map[subject] = subject
                rules.append('type(%s,%s)' % (map[subject], object))
            else:
                pred_var = identification_string(next, chars=CHARS)
                next += 1
                str_repr = '%s(%s,%s)' % (pred_type, subject, object)
                map[str_repr] = pred_var
                if pred_type not in map:
                    map[pred_type] = identification_string(next, chars=CHARS)
                    vars.add(pred_type)
                    next += 1
                for arg in [inst_id, subject, object]:
                    if arg not in map:
                        if cg.has(arg, 'var'):
                            map[arg] = identification_string(next, chars=CHARS)
                            vars.add(arg)
                            next += 1
                        else:
                            map[arg] = arg
                predinst = 'predinst(%s,%s)' % (pred_var, map[inst_id])
                functor = 'functor(%s,%s,_)' % (pred_var, map[pred_type])
                t = 'type(%s,%s)' % (map[pred_type], pred_type)
                predinst_unspec = '(%s,%s,%s)' % (predinst, functor, t)
                functor_spec = 'functor(%s,%s,_)' % (pred_var, pred_type)
                predinst_spec = '(%s,%s)' % (predinst, functor_spec)
                predinst_disj = '(%s;%s)' % (predinst_unspec, predinst_spec)
                arg1 = 'arg(1,%s,%s)' % (pred_var, map[subject])
                arg2 = 'arg(2,%s,%s)' % (pred_var, map[object])
                rules.extend([predinst_disj, arg1, arg2])
        else:                               # monopredicate
            if pred_type not in ['var', 'is_type']:
                pred_var = identification_string(next, chars=CHARS)
                next += 1
                str_repr = '%s(%s)' % (pred_type, subject)
                map[str_repr] = pred_var
                if pred_type not in map:
                    map[pred_type] = identification_string(next, chars=CHARS)
                    vars.add(pred_type)
                    next += 1
                for arg in [inst_id, subject]:
                    if arg not in map:
                        if cg.has(arg, 'var'):
                            map[arg] = identification_string(next, chars=CHARS)
                            vars.add(arg)
                            next += 1
                        else:
                            map[arg] = arg
                predinst = 'predinst(%s,%s)' % (pred_var, map[inst_id])
                functor = 'functor(%s,%s,_)' % (pred_var, map[pred_type])
                t = 'type(%s,%s)' % (map[pred_type], pred_type)
                predinst_unspec = '(%s,%s,%s)' % (predinst, functor, t)
                functor_spec = 'functor(%s,%s,_)' % (pred_var, pred_type)
                predinst_spec = '(%s,%s)' % (predinst, functor_spec)
                predinst_disj = '(%s;%s)' % (predinst_unspec, predinst_spec)
                arg1 = 'arg(1,%s,%s)' % (pred_var, map[subject])
                rules.extend([predinst_disj, arg1])
    return ', '.join(rules), {var: map[var] for var in vars}

