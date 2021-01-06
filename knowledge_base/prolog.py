

def to_knowledge_prolog(self):
    self_type = []
    type_rules = []
    rules = []
    for tuple, inst_id in self.predicate_instances():
        if len(tuple) == 3:  # bipredicates
            subject, object, pred_type = tuple
            if pred_type == 'type':
                for t in self.get_all_types(subject, object):
                    type_rules.append('type(%s,%s)' % (subject, t))
            else:
                rules.append('predinst(%s(%s,%s),%s)' % (pred_type, subject, object, inst_id))
        else:
            subject, pred_type = tuple
            if pred_type not in ['var', 'is_type']:
                rules.append('predinst(%s(%s),%s)' % (pred_type, subject, inst_id))

    return self_type + type_rules + rules


def to_query_prolog(self):
    # contains one inference rule
    self.idx, self.seq = 0, 1
    map = Bimap()
    rules = []
    for (subject, object, pred_type), inst_id in self.bipredicate_instances():
        if pred_type == 'type':
            if subject not in map:
                if self.monopredicate(subject, 'var'):
                    map[subject] = self._prolog_var()
                else:
                    map[subject] = subject
            rules.append('type(%s,%s)' % (map[subject], object))
        else:
            pred_var = self._prolog_var()
            str_repr = '%s(%s,%s)' % (pred_type, subject, object)
            map[str_repr] = pred_var
            if pred_type not in map:
                map[pred_type] = self._prolog_var()
            for arg in [inst_id, subject, object]:
                if arg not in map:
                    if self.monopredicate(arg, 'var'):
                        map[arg] = self._prolog_var()
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
    for (subject, pred_type), inst_id in self.monopredicate_instances():
        if pred_type not in ['var', 'is_type']:
            pred_var = self._prolog_var()
            str_repr = '%s(%s)' % (pred_type, subject)
            map[str_repr] = pred_var
            if pred_type not in map:
                map[pred_type] = self._prolog_var()
            for arg in [inst_id, subject]:
                if arg not in map:
                    if self.monopredicate(arg, 'var'):
                        map[arg] = self._prolog_var()
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
            rules.extend([predinst_disj, arg1, arg2])
    return ', '.join(rules), map

# todo - inefficient since it will traverse an ancestor path that it has already travelled if there is intersection
def get_all_types(self, node, parent=None, get_predicates=False):
    types = set()
    if parent is not None:
        if not get_predicates:
            types.add(parent)
        else:
            pred_id = list(self.bipredicate(node, parent, 'type'))[0]
            types.add(((node, parent, 'type'),pred_id))
        node = parent
    for ancestor in self.object_neighbors(node, 'type'):
        if not get_predicates:
            types.add(ancestor)
        else:
            pred_id = list(self.bipredicate(node, ancestor, 'type'))[0]
            types.add(((node, ancestor, 'type'), pred_id))
        types.update(self.get_all_types(ancestor, get_predicates=get_predicates))
    return types

######################
#
## Inference Functions
#
######################

def generate_inference_graph(self):
    inferences = {}
    implications = {}
    infer_pred_inst = defaultdict(set)
    for tuple, inst_id in self.bipredicate_instances():
        situation_node, pre_pred_inst, type = tuple
        if type == 'pre' or type == 'post':
            if type == 'pre':
                if situation_node not in inferences:
                    inferences[situation_node] = ConceptGraph()
                new_graph = inferences[situation_node]
            else:
                if situation_node not in implications:
                    implications[situation_node] = ConceptGraph()
                new_graph = implications[situation_node]
            components = [self.subject(pre_pred_inst),
                          self.object(pre_pred_inst),
                          self.type(pre_pred_inst)]
            missing_args = components.count(None)
            if missing_args < 3:
                for comp in components:
                    if comp is not None and not new_graph.has(comp):
                        new_graph.add_node(comp)
                if components[1] is None:  # monopredicate
                    new_graph.add_monopredicate(components[0], components[2], predicate_id=pre_pred_inst, merging=True)
                    if components[2] == 'var' and type == 'pre':
                        infer_pred_inst[situation_node].add((components[0],pre_pred_inst))
                elif missing_args == 0: # bipredicate
                    new_graph.add_bipredicate(*components, predicate_id=pre_pred_inst, merging=True)
                else:
                    raise Exception('generate_inference_graph is trying to process a predicate with impossible format!')
            else:
                # inst is not a predicate, it is an entity instance
                if not new_graph.has(pre_pred_inst):
                    new_graph.add_node(pre_pred_inst)

    for situation_node, vars in infer_pred_inst.items():
        implication_graph = implications[situation_node]
        if not implication_graph.has('var'):
            implication_graph.add_node('var')
        for subject, pred_inst in vars:
            if implication_graph.has(subject):
                implication_graph.add_monopredicate(subject, 'var', predicate_id=pred_inst, merging=True)

    return inferences, implications

def infer(self, inference_graph):
    class PyswipEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Variable):
                return 'PyswipVariable(%d)'%obj.handle
            elif isinstance(obj, bytes):
                return '"%s"'%obj.decode("utf-8")
            return json.JSONEncoder.default(self, obj)

    kg_rules = self.to_knowledge_prolog()
    inference_query, inference_map = inference_graph.to_query_prolog()
    print(json.dumps(inference_map.reverse(), indent=4))

    prolog = Prolog()
    for rule in kg_rules:
        prolog.assertz(rule)
    strrules = '.\n'.join(kg_rules)
    s = time.time()
    solns = list(prolog.query(inference_query))
    parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
    print('Num solutions: %d'%len(parsed_solns))
    for rule in kg_rules:
        prolog.retract(rule)
    # print('** SOLUTIONS **')
    # for soln in parsed_solns:
    #     print(json.dumps(soln, indent=4))
    print('Ran inferences in %.3f'%(time.time()-s))
    return inference_map, parsed_solns
