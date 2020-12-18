from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.map.map import Map
from structpy.map.index.index import Index
from knowledge_base.concept_graph_spec import ConceptGraphSpec
from pyswip import Prolog, Variable
from structpy.map.bijective.bimap import Bimap
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
from collections import defaultdict
import json, time, copy

class ConceptGraph:

    def __init__(self, prefix='cg_', bipredicates=None, monopredicates=None, nodes=None):
        self.next_id = 0
        self.prefix = prefix
        self.bipredicate_graph = MultiLabeledParallelDigraphNX(nodes=nodes)

        if bipredicates is not None:
            idx = {}
            for pred in bipredicates:
                if pred not in idx:
                    idx[pred] = set()
                id = self._get_next_id()
                idx[pred].add(id)
                self.bipredicate_graph.add(*pred, id=id)
            self.bipredicate_instance_index = Index(idx)
        else:
            self.bipredicate_instance_index = Index()

        if monopredicates is not None:
            mps = {}
            for subject, label in monopredicates:
                if subject not in mps:
                    mps[subject] = set()
                mps[subject].add(label)
            self.monopredicate_map = Map(mps)

            idx = {}
            for pred in monopredicates:
                if pred not in idx:
                    idx[pred] = set()
                id = self._get_next_id()
                idx[pred].add(id)
            self.monopredicate_instance_index = Index(idx)
        else:
            self.monopredicate_map = Map()
            self.monopredicate_instance_index = Index()

        if nodes is not None:
            for node in nodes:
                self.monopredicate_map[node] = set()

    def _get_next_id(self):
        to_return = self.next_id
        self.next_id += 1
        return self.prefix + str(to_return)

    def _add_to_bipredicate_index(self, key, value):
        if key not in self.bipredicate_instance_index:
            self.bipredicate_instance_index[key] = set()
        self.bipredicate_instance_index[key].add(value)

    def add_node(self, node):
        self.bipredicate_graph.add(node)
        self.monopredicate_map[node] = set()
        return node

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_bipredicate(self, source, target, label, predicate_id=None):
        if predicate_id is None:
            predicate_id = self._get_next_id()
        self.bipredicate_graph.add(source, target, label, id=predicate_id)
        self._add_to_bipredicate_index((source,target,label),predicate_id)
        return predicate_id

    def add_monopredicate(self, source, label, predicate_id=None):
        if predicate_id is None:
            predicate_id = self._get_next_id()
        if source not in self.monopredicate_map:
            self.monopredicate_map[source] = set()
        self.monopredicate_map[source].add(label)
        self.monopredicate_instance_index[(source, label)].add(predicate_id)
        return predicate_id

    def remove_node(self, node):
        if self.bipredicate_graph.has(node):
            bipredicates = list(self.bipredicate_instance_index.items())
            for bipredicate, ids in bipredicates:
                if bipredicate[0] == node or bipredicate[1] == node:
                    self.remove_bipredicate(*bipredicate)
            self.bipredicate_graph.remove(node)

        if node in self.monopredicate_map:
            monopredicates = list(self.monopredicate_instance_index.items())
            for monopredicate, ids in monopredicates:
                if monopredicate[0] == node:
                    self.remove_monopredicate(*monopredicate)
            del self.monopredicate_map[node]

    def remove_bipredicate(self, node, target, label, id=None):
        ids = list(self.bipredicate_instance_index[(node, target, label)])
        if id is not None:
            # remove only the specified instance with signature (node, target, label)
            ids = [id]
            if len(self.bipredicate_instance_index[(node, target, label)]) == 1:
                del self.bipredicate_instance_index[(node, target, label)]
        else:
            # remove all instances with signature
            del self.bipredicate_instance_index[(node, target, label)]
        for id in ids:
            self.bipredicate_graph.remove(node, target, label, id=id)
            self.remove_node(id)

    def remove_monopredicate(self, node, label, id=None):
        ids = list(self.monopredicate_instance_index[(node, label)])
        if id is not None:
            ids = [id]
            if len(self.monopredicate_instance_index[(node, label)]) == 1:
                del self.monopredicate_instance_index[(node, label)]
                self.monopredicate_map[node].remove(label)
        else:
            del self.monopredicate_instance_index[(node, label)]
            self.monopredicate_map[node].remove(label)
        for id in ids:
            self.remove_node(id)

    def detach_bipredicate(self, node, target, label, id):
        if len(self.bipredicate_instance_index[(node, target, label)]) == 1:
            del self.bipredicate_instance_index[(node, target, label)]
        else:
            self.bipredicate_instance_index[(node,target,label)].remove(id)
        self.bipredicate_graph.remove(node, target, label, id=id)

    def detach_monopredicate(self, node, label, id=None):
        if len(self.monopredicate_instance_index[(node, label)]) == 1:
            del self.monopredicate_instance_index[(node, label)]
            self.monopredicate_map[node].remove(label)
        else:
            self.monopredicate_instance_index[(node,label)].remove(id)

    def merge(self, other_graph):
        id_map = {}
        for tuple, inst_id in other_graph.predicate_instances():
            for node in tuple:
                if node.startswith(other_graph.prefix):
                    if node not in id_map:
                        id_map[node] = self._get_next_id()
                else:
                    id_map[node] = node
                if id_map[node] not in self.concepts():
                    self.add_node(id_map[node])
            if inst_id not in id_map:
                id_map[inst_id] = self._get_next_id()
            if len(tuple) == 3:
                self.add_bipredicate(id_map[tuple[0]], id_map[tuple[1]], id_map[tuple[2]],
                                     predicate_id=id_map[inst_id])
            elif len(tuple) == 2:
                self.add_monopredicate(id_map[tuple[0]], id_map[tuple[1]],
                                       predicate_id=id_map[inst_id])
        return id_map

    def merge_node(self, keep, merge):
        if keep.startswith(self.prefix):
            temp = keep
            keep = merge
            merge = temp
        print('\tReplacing: %s -> %s' % (merge,keep))
        for tuple, inst in self.predicate_instances(merge):
            if len(tuple) == 3:
                self.detach_bipredicate(*tuple, id=inst)
                if tuple[0] == merge:
                    self.add_bipredicate(keep, tuple[1], tuple[2], predicate_id=inst)
                    print('\t\tReplaced: %s(%s,%s) -> %s(%s,%s)' % (tuple[2],tuple[0],tuple[1],tuple[2],keep,tuple[1]))
                elif tuple[1] == merge:
                    self.add_bipredicate(tuple[0], keep, tuple[2], predicate_id=inst)
                    print('\t\tReplaced: %s(%s,%s) -> %s(%s,%s)' % (tuple[2],tuple[0],tuple[1],tuple[2],tuple[0],keep))
            elif len(tuple) == 2:
                self.detach_monopredicate(*tuple, id=inst)
                self.add_monopredicate(keep, tuple[1], predicate_id=inst)
                print('\t\tReplaced: %s(%s) -> %s(%s)' % (tuple[1], tuple[0], tuple[1], keep))
        self.remove_node(merge)
        print()

    def copy(self):
        cp = ConceptGraph(self.prefix)
        cp.next_id = self.next_id
        cp.bipredicate_graph = copy.deepcopy(self.bipredicate_graph)
        cp.bipredicate_instance_index = copy.deepcopy(self.bipredicate_instance_index)
        cp.monopredicate_instance_index = copy.deepcopy(self.monopredicate_instance_index)
        cp.monopredicate_map = Map(self.monopredicate_map.items())
        return cp

    ######################
    #
    ## Access Functions
    #
    ######################

    def predicates(self, node, predicate_type=None):
        predicates = self.bipredicates(node, predicate_type)
        if predicate_type is None:
            predicates.update(self.monopredicates(node))
        return predicates

    def bipredicates(self, node, predicate_type=None):
        edges = self.bipredicate_graph.out_edges(node, predicate_type)
        edges.update(self.bipredicate_graph.in_edges(node, predicate_type))
        return edges

    def monopredicates(self, node):
        monopreds = set()
        for label in self.monopredicate_map[node]:
            monopreds.update([(node, label)] * len(self.monopredicate_instance_index[(node, label)]))
        return monopreds

    def predicates_of_subject(self, node, predicate_type=None):
        predicates = self.bipredicates_of_subject(node, predicate_type)
        predicates.update(self.monopredicates_of_subject(node))
        return predicates

    def bipredicates_of_subject(self, node, predicate_type=None):
        return self.bipredicate_graph.out_edges(node, predicate_type)

    def monopredicates_of_subject(self, node):
        return self.monopredicates(node)

    def predicates_of_object(self, node, predicate_type=None):
        return self.bipredicate_graph.in_edges(node, predicate_type)

    def bipredicate(self, subject, object, type):
        return self.bipredicate_instance_index[(subject, object, type)]

    def monopredicate(self, subject, type):
        return self.monopredicate_instance_index[(subject, type)]

    def neighbors(self, node, predicate_type=None):
        nodes = self.bipredicate_graph.targets(node, predicate_type)
        nodes.update(self.bipredicate_graph.sources(node, predicate_type))
        return nodes

    def subject_neighbors(self, node, predicate_type=None):
        return self.bipredicate_graph.sources(node, predicate_type)

    def object_neighbors(self, node, predicate_type=None):
        return self.bipredicate_graph.targets(node, predicate_type)

    def subject(self, predicate_instance):
        if predicate_instance in self.bipredicate_instance_index.reverse():
            return self.bipredicate_instance_index.reverse()[predicate_instance][0]
        elif predicate_instance in self.monopredicate_instance_index.reverse():
            return self.monopredicate_instance_index.reverse()[predicate_instance][0]

    def object(self, predicate_instance):
        if predicate_instance in self.bipredicate_instance_index.reverse():
            return self.bipredicate_instance_index.reverse()[predicate_instance][1]

    def type(self, predicate_instance):
        if predicate_instance in self.bipredicate_instance_index.reverse():
            return self.bipredicate_instance_index.reverse()[predicate_instance][2]
        elif predicate_instance in self.monopredicate_instance_index.reverse():
            return self.monopredicate_instance_index.reverse()[predicate_instance][1]

    def signature(self, predicate_instance):
        if predicate_instance in self.bipredicate_instance_index.reverse():
            return self.bipredicate_instance_index.reverse()[predicate_instance]
        elif predicate_instance in self.monopredicate_instance_index.reverse():
            return self.monopredicate_instance_index.reverse()[predicate_instance]

    def predicates_between(self, node1, node2):
        return self.bipredicate_graph.edges(node1).intersection(self.bipredicate_graph.edges(node2))

    def concepts(self):
        nodes = set()
        bpi = [x for x in self.bipredicate_instance_index.items() if x[0] != 'codomain'] # todo - this is just a hot fix for a pycharm debugging error where 'codomain' gets added to the index if the index if expanded while debugging
        for (source, target, label), predicate_insts in bpi:
            nodes.update({source, target, label, *predicate_insts})
        nodes.update(self.bipredicate_graph.nodes())
        mpi = [x for x in self.monopredicate_instance_index.items() if x[0] != 'codomain']
        for (source, label), predicate_insts in mpi:
            nodes.update({source, label, *predicate_insts})
        nodes.update(self.monopredicate_map.keys())
        return nodes

    def predicate_instances(self, node=None):
        pred_inst = set()
        for tuple, predicate_insts in self.bipredicate_instance_index.items():
            for inst in predicate_insts:
                if node is None or (node is not None and node in tuple):
                    pred_inst.add((tuple,inst))
        for tuple, predicate_insts in self.monopredicate_instance_index.items():
            for inst in predicate_insts:
                if node is None or (node is not None and node in tuple):
                    pred_inst.add((tuple,inst))
        return pred_inst

    def bipredicate_instances(self):
        pred_inst = set()
        for tuple, predicate_insts in self.bipredicate_instance_index.items():
            for inst in predicate_insts:
                pred_inst.add((tuple,inst))
        return pred_inst

    def monopredicate_instances(self):
        pred_inst = set()
        for tuple, predicate_insts in self.monopredicate_instance_index.items():
            for inst in predicate_insts:
                pred_inst.add((tuple,inst))
        return pred_inst

    def has(self, nodes):
        if isinstance(nodes, str) or isinstance(nodes, int):
            return nodes in self.concepts()
        elif isinstance(nodes, list):
            concepts = self.concepts()
            for n in nodes:
                if n not in concepts:
                    return False
            return True
        else:
            raise Exception(":param 'nodes' must be int, string or list")

    # todo - inefficient since it will traverse an ancestor path that it has already travelled if there is intersection
    def get_all_types(self, node, parent=None, get_predicates=False):
        types = set()
        if node in self.concepts():
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

    def get_instances_of_type(self, type):
        pred_inst = set()
        is_bipredicate_type=False
        for tuple, predicate_insts in self.bipredicate_instance_index.items():
            for inst in predicate_insts:
                if tuple[2] == type:
                    is_bipredicate_type=True
                    pred_inst.add((tuple,inst))
        if not is_bipredicate_type:
            for tuple, predicate_insts in self.monopredicate_instance_index.items():
                for inst in predicate_insts:
                    if tuple[1] == type:
                        pred_inst.add((tuple,inst))
        return pred_inst

    ######################
    #
    ## Pulling
    #
    ######################

    def pull(self, nodes, kb, max_depth):
        """
        Pull KB predicates into WM for specified nodes

        :param nodes: iterable of nodes to retrieve neighbors for
        :param depth: integer value of retrieved neighborhood depth
        """
        visited = set()
        frontier = [(x, 0) for x in nodes]

        # pull non-type predicates
        while len(frontier) > 0:
            item = frontier.pop(0)
            if item[0] not in visited:
                if len(item) == 2:
                    node, depth = item
                    visited.add(node)
                    self._update_frontier(frontier, [node], kb, depth, max_depth)
                elif len(item) == 3:
                    node, tuple, depth = item
                    visited.add(node)
                    self._add_tuple_nodes(tuple)
                    if len(tuple) == 3 and tuple[2] != 'type':
                        self.add_bipredicate(*tuple, predicate_id=node)
                    elif len(tuple) == 2:
                        self.add_monopredicate(*tuple, predicate_id=node)
                    self._update_frontier(frontier, list(tuple)+[node], kb, depth, max_depth)
                else:
                    raise Exception('Unexpected element %s in frontier of pull()'%str(item))

        # pull type ancestry of all nodes
        self.pull_types(self.concepts(), kb)

    def pull_types(self, nodes, kb):
        # pull type ancestry of nodes
        for node in nodes:
            ancestry = kb._concept_graph.get_all_types(node, get_predicates=True)
            for tuple, pred_id in ancestry:
                self._add_tuple_nodes(tuple)
                if not self.has(pred_id):
                    self.add_bipredicate(*tuple, predicate_id=pred_id)
                    is_type_inst = list(kb._concept_graph.monopredicate(tuple[1], 'is_type'))[0]
                    if not self.has(is_type_inst):
                        self.add_monopredicate(tuple[1], 'is_type', predicate_id=is_type_inst)

    def _update_frontier(self, frontier, nodes, kb, depth, max_depth):
        if depth < max_depth:
            for n in nodes:
                connections = kb._concept_graph.predicate_instances(n)
                frontier.extend([(connection[1], connection[0], depth + 1)
                                 for connection in connections])

    def _add_tuple_nodes(self, tuple):
        for t in tuple:
            if not self.has(t):
                self.add_node(t)

    ######################
    #
    ## Inference Functions
    #
    ######################

    def generate_inference_graphs(self, prefix='def_'):
        class TransformationRule:
            def __init__(self, pre, post):
                self.precondition = pre
                self.postcondition = post

        inferences = {}
        implications = {}
        infer_pred_inst = defaultdict(set)
        for tuple, inst_id in self.bipredicate_instances():
            situation_node, pre_pred_inst, type = tuple
            if type == 'pre' or type == 'post':
                if type == 'pre':
                    if situation_node not in inferences:
                        inferences[situation_node] = ConceptGraph(prefix)
                        inferences[situation_node].next_id = self.next_id
                    new_graph = inferences[situation_node]
                else:
                    if situation_node not in implications:
                        implications[situation_node] = ConceptGraph(prefix)
                        implications[situation_node].next_id = self.next_id
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
                        new_graph.add_monopredicate(components[0], components[2], predicate_id=pre_pred_inst)
                        if components[2] == 'var' and type == 'pre':
                            infer_pred_inst[situation_node].add((components[0],pre_pred_inst))
                    elif missing_args == 0: # bipredicate
                        new_graph.add_bipredicate(*components, predicate_id=pre_pred_inst)
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
                    implication_graph.add_monopredicate(subject, 'var', predicate_id=pred_inst)

        rules = []
        for situation_node in inferences:
            rules.append(TransformationRule(inferences[situation_node], implications[situation_node]))
        return rules

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
        # print(json.dumps(inference_map.reverse(), indent=4))

        prolog = Prolog()
        for rule in kg_rules:
            prolog.assertz(rule)
        strrules = '.\n'.join(kg_rules)
        s = time.time()
        solns = list(prolog.query(inference_query))
        parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
        # print('Num solutions: %d'%len(parsed_solns))
        for rule in kg_rules:
            prolog.retract(rule)
        # print('** SOLUTIONS **')
        # for soln in parsed_solns:
        #     print(json.dumps(soln, indent=4))
        # print('Ran inferences in %.3f'%(time.time()-s))
        return inference_map, parsed_solns

    def to_knowledge_prolog(self):
        type_rules = set()
        rules = set()
        for tuple, inst_id in self.predicate_instances():
            if len(tuple) == 3: # bipredicates
                subject, object, pred_type = tuple
                if pred_type == 'type':
                    for t in self.get_all_types(subject, object):
                        type_rules.add('type(%s,%s)'%(subject,t))
                else:
                    rules.add('predinst(%s(%s,%s),%s)'%(pred_type,subject,object,inst_id))
            else:
                subject, pred_type = tuple
                if pred_type not in ['var', 'is_type']:
                    rules.add('predinst(%s(%s),%s)' % (pred_type, subject, inst_id))
        return type_rules.union(rules)

    def to_query_prolog(self):
        # contains one inference rule
        self.idx,self.seq = 0,1
        map = Bimap()
        rules = []
        for (subject, object, pred_type), inst_id in self.bipredicate_instances():
            if pred_type == 'type':
                if subject not in map:
                    if self.monopredicate(subject, 'var'):
                        map[subject] = self._prolog_var()
                    else:
                        map[subject] = subject
                rules.append('type(%s,%s)'%(map[subject],object))
            else:
                pred_var = self._prolog_var()
                str_repr = '%s(%s,%s)'%(pred_type,subject,object)
                map[str_repr]=pred_var
                if pred_type not in map:
                    map[pred_type] = self._prolog_var()
                for arg in [inst_id, subject, object]:
                    if arg not in map:
                        if self.monopredicate(arg, 'var'):
                            map[arg]=self._prolog_var()
                        else:
                            map[arg]=arg
                predinst = 'predinst(%s,%s)'%(pred_var,map[inst_id])
                functor = 'functor(%s,%s,_)'%(pred_var,map[pred_type])
                t = 'type(%s,%s)' % (map[pred_type], pred_type)
                predinst_unspec = '(%s,%s,%s)'%(predinst,functor,t)
                functor_spec = 'functor(%s,%s,_)' % (pred_var, pred_type)
                predinst_spec = '(%s,%s)'%(predinst,functor_spec)
                predinst_disj = '(%s;%s)'%(predinst_unspec,predinst_spec)
                arg1 = 'arg(1,%s,%s)'%(pred_var,map[subject])
                arg2 = 'arg(2,%s,%s)'%(pred_var,map[object])
                rules.extend([predinst_disj,arg1,arg2])
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

    def _prolog_var(self):
        var = CHARS[self.idx]*self.seq
        self.idx += 1
        if self.idx == 26:
            self.seq += 1
            self.idx = 0
        return var


if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))

