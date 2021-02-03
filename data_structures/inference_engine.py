import json, time
from pyswip import Prolog, Variable
from GRIDD.utilities import identification_string, CHARS
from structpy.map.bijective.bimap import Bimap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine_spec import InferenceEngineSpec
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
import GRIDD.utilities as util


class InferenceEngine:

    def __init__(self):
        self.logic_parser = KnowledgeParser(None, None, ensure_kb_compatible=False)

    def run(self, concept_graph, *inference_rules, ordered_rule_ids=None):

        kg_statements, non_string_node_mapping = to_knowledge_prolog(concept_graph,
                                                                     predicate_exclusions={'pre', 'post'})

        non_string_node_mapping = {v: k for k, v in non_string_node_mapping.items()}

        prolog = Prolog()

        # s = time.time()
        for statement in kg_statements:
            prolog.assertz(statement)
        # print('Asserts: %.2f'%(time.time()-s))

        if len(inference_rules) == 0:
            all_rules = self.generate_rules_from_graph(concept_graph, with_names=True)
        else:
            concept_graph_rules = None
            all_rules = []
            for rule in inference_rules:
                if isinstance(rule, tuple): # tuple of concept graphs
                    all_rules.append(rule)
                elif concept_graph.has(rule): # rule concept id
                    if concept_graph_rules is None:
                        concept_graph_rules = {rule_tuple[2]: rule_tuple
                                               for rule_tuple in self.generate_rules_from_graph(concept_graph,
                                                                                          with_names=True)}
                    all_rules.append(concept_graph_rules[rule])
                elif isinstance(rule, str): # logic string of SINGLE rule
                    rule_tuple = self.generate_rules_from_graph(self.load(rule), with_names=True)
                    assert len(rule_tuple) == 1
                    all_rules.append(rule_tuple[0])

        if ordered_rule_ids is not None:
            assert all([True if len(rule) == 3 else False for rule in all_rules])
            all_rules = [rule for rule_id in ordered_rule_ids for rule in all_rules if rule[2] == rule_id]

        solutions = {}
        # times = []
        for rule in all_rules:
            inference_query, inference_map = to_query_prolog(rule[0])
            # s = time.time()
            solns = list(prolog.query(inference_query))
            # times.append(time.time() - s)
            # print('Rule %s: %.2f' % (rule[2], time.time() - s))
            parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
            solutions[rule] = []
            for match in parsed_solns:
                variable_assignments = {}
                for key, value in inference_map.items():
                    solution_node = non_string_node_mapping.get(match[value], match[value])
                    variable_assignments[key] = solution_node
                solutions[rule].append(variable_assignments)
        # print('Rule sum: %.2f'%(sum(times)))

        # s = time.time()
        for statement in kg_statements:
            prolog.retract(statement)
        # print('Asserts retracted: %.2f'%(time.time()-s))

        return solutions

    def generate_rules_from_graph(self, concept_graph, with_names=False):
        inferences, implications = {}, {}
        id_maps = {}

        for situation_node, _, constraint, _ in concept_graph.predicates(predicate_type='pre'):
            if situation_node not in inferences:
                inferences[situation_node] = ConceptGraph(namespace='pre', concepts=['var'])
                id_maps[situation_node] = {}
            self._transfer_concept(concept_graph, inferences[situation_node], constraint, id_maps[situation_node])

        for situation_node, _, implication, _ in concept_graph.predicates(predicate_type='post'):
            if situation_node not in implications:
                implications[situation_node] = ConceptGraph(namespace='post')
            self._transfer_concept(concept_graph, implications[situation_node], implication, id_maps[situation_node])

        rules = [(inferences[situation_node], implications[situation_node]) if not with_names else
                 (inferences[situation_node], implications[situation_node], situation_node)
                 for situation_node in inferences]

        return rules

    def _transfer_concept(self, cg, new_graph, concept_id, id_map):
        """
        Adds the concept `concept_id` from `cg` to `new_graph`
        """
        if cg.has(predicate_id=concept_id):  # predicate instance
            components = [cg.subject(concept_id), cg.type(concept_id), cg.object(concept_id)]
            mapped_components = []
            for comp in components:
                if comp is not None:
                    comp = util.map(new_graph, comp, cg._namespace, id_map)
                mapped_components.append(comp)
            new_graph.add(*mapped_components, predicate_id=util.map(new_graph, concept_id, cg._namespace, id_map))
        else:  # entity instance
            util.map(new_graph, concept_id, cg._namespace, id_map)

    def load(self, logic_string):
        if len(logic_string.strip()) > 0:
            cg = ConceptGraph()
            tree = self.logic_parser.parse(logic_string)
            additions = self.logic_parser.transform(tree)
            for addition in additions:
                cg.concatenate(addition)
            return cg
        return None

class PyswipEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Variable):
            return 'PyswipVariable(%d)' % obj.handle
        elif isinstance(obj, bytes):
            return '"%s"' % obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)

def to_knowledge_prolog(cg, predicate_exclusions=None):
    """
    Convert cg to knowledge rules for Prolog.
    """
    type_rules = []
    rules = []
    non_string_node_mapping = {}

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
    ignore = set()

    if predicate_exclusions is not None:
        for t in predicate_exclusions:
            for s, t, o, i in tmp.predicates(predicate_type=t):
                ignore.update({s,o,i})

    for item in tmp.predicates():
        if item[0] not in ignore and item[2] not in ignore and item[3] not in ignore:
            s, t, o, i = _non_string_map(item, non_string_node_mapping)
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
    return type_rules + rules, non_string_node_mapping

def _non_string_map(item, non_string_node_mapping):
    for e in item:
        if e not in non_string_node_mapping:
            if not isinstance(e, str):
                e_id = identification_string(len(non_string_node_mapping), chars=CHARS.lower())
                non_string_node_mapping[e] = e_id
                yield e_id
            else:
                yield e
        else:
            yield non_string_node_mapping[e]

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

if __name__ == '__main__':
    print(InferenceEngineSpec.verify(InferenceEngine))