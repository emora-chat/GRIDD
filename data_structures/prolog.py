
import json, time
from collections import defaultdict
from pyswip import Prolog, Variable
from utilities import identification_string, CHARS
from structpy.map.bijective.bimap import Bimap
from data_structures.concept_graph import ConceptGraph


class TransformationRule:
    def __init__(self, pre, post, concept_id):
        self.precondition = pre
        self.postcondition = post
        self.concept_id = concept_id

    def __hash__(self):
        return hash(self.concept_id)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.concept_id == other
        else:
            return self.concept_id == other.concept_id

def generate_inference_graphs(cg):
    """
    Identifies the inference rules and their corresponding implications in the given
    concept graph `cg`.

    Returns
        dict<rule_id: TransformationRule object>
    """
    inferences = {}
    implications = {}
    infer_pred_inst = defaultdict(set)
    for situation_node, type, pre_pred_inst, inst_id in cg.predicates(predicate_type='pre'):
        if situation_node not in inferences:
            inferences[situation_node] = ConceptGraph()
        rule_graph = inferences[situation_node]
        _add_rule_to_graph(cg, rule_graph, pre_pred_inst)
        if cg.has(predicate_id=pre_pred_inst) and cg.type(pre_pred_inst) == 'var':
            infer_pred_inst[situation_node].add((cg.subject(pre_pred_inst), pre_pred_inst))

    for situation_node, type, post_pred_inst, inst_id in cg.predicates(predicate_type='post'):
        if situation_node not in implications:
            implications[situation_node] = ConceptGraph()
        rule_graph = implications[situation_node]
        _add_rule_to_graph(cg, rule_graph, post_pred_inst)

    for situation_node, vars in infer_pred_inst.items():
        implication_graph = implications[situation_node]
        if not implication_graph.has('var'):
            implication_graph.add('var')
        for subject, pred_inst in vars:
            if implication_graph.has(subject):
                implication_graph.add(subject, 'var', predicate_id=pred_inst)

    rules = {}
    for situation_node in inferences:
        rules[situation_node] = TransformationRule(inferences[situation_node], implications[situation_node], situation_node)
    return rules


def _add_rule_to_graph(cg, rule_graph, rule_instance_id):
    """
    Helper function of generate_inference_graphs() that adds rules to the `rule_graph`
    which is either a graph of inferences or a graph of implications for a given rule
    """
    if cg.has(predicate_id=rule_instance_id):
        components = [cg.subject(rule_instance_id),
                      cg.object(rule_instance_id),
                      cg.type(rule_instance_id)]
        for comp in components:
            if comp is not None and not rule_graph.has(comp):
                rule_graph.add(comp)
        if components[1] is None:   # monopredicate
            rule_graph.add(components[0], components[2], predicate_id=rule_instance_id)
        elif components[0] is not None and components[1] is not None and components[2] is not None:     # bipredicate
            rule_graph.add(components[0], components[2], components[1], predicate_id=rule_instance_id)
        else:
            raise Exception('generate_inference_graph is trying to process a predicate with impossible format!')
    else:
        # inst is not a predicate, it is an entity instance
        if not rule_graph.has(rule_instance_id):
            rule_graph.add(rule_instance_id)


def infer(knowledge_graph, inference_rules):
    """
    Get variable assignments of solutions from applying each query graph from the
    `inference rules` dict on the `knowledge_graph`

    Returns dict<rule_id: list of solutions (variable assignments)>
    """
    class PyswipEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Variable):
                return 'PyswipVariable(%d)'%obj.handle
            elif isinstance(obj, bytes):
                return '"%s"'%obj.decode("utf-8")
            return json.JSONEncoder.default(self, obj)

    kg_rules = to_knowledge_prolog(knowledge_graph)
    prolog = Prolog()
    for rule in kg_rules:
        prolog.assertz(rule)
    # strrules = '.\n'.join(kg_rules)

    solutions = {}
    for rule_id, rule in inference_rules.items():
        inference_query, inference_map = to_query_prolog(rule.precondition)
        # print(json.dumps(inference_map.reverse(), indent=4))
        s = time.time()
        solns = list(prolog.query(inference_query))
        parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
        # print('Num solutions: %d'%len(parsed_solns))
        # print('** SOLUTIONS **')
        # for soln in parsed_solns:
        #     print(json.dumps(soln, indent=4))
        solutions[rule] = []
        for match in parsed_solns:
            variable_assignments = {}
            for key, value in inference_map.items():
                variable_assignments[key] = match[value]
            solutions[rule].append(variable_assignments)
        # print('Ran inference (rule %s) in %.3f'%(str(rule_id), time.time()-s))

    for rule in kg_rules:
        prolog.retract(rule)

    return solutions


def to_knowledge_prolog(cg):
    """
    Convert cg to knowledge rules for Prolog.
    """
    type_rules = []
    rules = []
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
            if t not in ['var', 'is_type']:
                rules.append('predinst(%s(%s),%s)' % (t, s, i))
                one_non_ont_predicate = True
    if not one_non_ont_predicate: # if there is no predinst in knowledge prolog, a prolog query using predinst causes error to be thrown (predinst is not defined)
        rules.append('predinst(xtestx(xax, xbx), xnx)')
    return type_rules + rules


def to_query_prolog(cg):
    """
    Convert cg to query rules for Prolog.

    `cg` contains one inference rule specification.
    """
    next = 0
    map = Bimap()
    rules = []
    for subject, pred_type, object, inst_id in cg.predicates():
        if object is not None:              # bipredicate
            if pred_type == 'type':
                if subject not in map:
                    if cg.has(subject, 'var'):
                        map[subject] = identification_string(next, chars=CHARS)
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
                    next += 1
                for arg in [inst_id, subject, object]:
                    if arg not in map:
                        if cg.has(arg, 'var'):
                            map[arg] = identification_string(next, chars=CHARS)
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
                    next += 1
                for arg in [inst_id, subject]:
                    if arg not in map:
                        if cg.has(arg, 'var'):
                            map[arg] = identification_string(next, chars=CHARS)
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
    return ', '.join(rules), map

