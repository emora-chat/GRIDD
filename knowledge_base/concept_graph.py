from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.map.map import Map
from structpy.map.index.index import Index
from knowledge_base.concept_graph_spec import ConceptGraphSpec
import sys,os
from pyswip import Prolog, Variable
from structpy.map.bijective.bimap import Bimap
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
import json, time, copy

class ConceptGraph:

    def __init__(self, bipredicates=None, monopredicates=None, nodes=None):
        self.next_id = 0
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
        return to_return

    def _add_to_bipredicate_index(self, key, value):
        if key not in self.bipredicate_instance_index:
            self.bipredicate_instance_index[key] = set()
        self.bipredicate_instance_index[key].add(value)

    def add_node(self, node):
        if self.bipredicate_graph.has(node):
            raise Exception('node %s already exists in bipredicates'%node)
        self.bipredicate_graph.add(node)
        if node in self.monopredicate_map:
            raise Exception('node %s already exists in monopredicates'%node)
        self.monopredicate_map[node] = set()

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_bipredicate(self, source, target, label, predicate_id=None, merging=False):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif target not in concepts:
            raise Exception(":param 'target' error - node %s does not exist!" % target)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        if predicate_id in concepts and not merging:
            raise Exception("predicate id %s already exists!" % predicate_id)
        if predicate_id is None:
            predicate_id = self._get_next_id()
        self.bipredicate_graph.add(source, target, label, id=predicate_id)
        self._add_to_bipredicate_index((source,target,label),predicate_id)
        return predicate_id

    def add_monopredicate(self, source, label, predicate_id=None, merging=False):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        if predicate_id in concepts and not merging:
            raise Exception("predicate id %s already exists!" % predicate_id)
        if predicate_id is None:
            predicate_id = self._get_next_id()
        if source not in self.monopredicate_map:
            self.monopredicate_map[source] = set()
        self.monopredicate_map[source].add(label)
        self.monopredicate_instance_index[(source, label)].add(predicate_id)
        return predicate_id

    def add_bipredicate_on_label(self, source, target, label):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif target not in concepts:
            raise Exception(":param 'target' error - node %s does not exist!" % target)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        self.bipredicate_graph.add(source, target, label, id=label)
        self._add_to_bipredicate_index((source,target,label),label)
        return label

    def add_monopredicate_on_label(self, source, label):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        self.monopredicate_map[source].add(label)
        self.monopredicate_instance_index[(source, label)].add(label)
        return label

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

    def remove_bipredicate(self, node, target, label):
        ids = list(self.bipredicate_instance_index[(node, target, label)])
        del self.bipredicate_instance_index[(node, target, label)]
        for id in ids:
            self.bipredicate_graph.remove(node, target, label, id=id)
            self.remove_node(id)

    def remove_monopredicate(self, node, label):
        ids = list(self.monopredicate_instance_index[(node, label)])
        del self.monopredicate_instance_index[(node, label)]
        self.monopredicate_map[node].remove(label)
        for id in ids:
            self.remove_node(id)

    def merge(self, other_graph):
        id_map = {}
        for tuple, inst_id in other_graph.predicate_instances():
            for node in tuple:
                if isinstance(node, int):
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
                                     predicate_id=id_map[inst_id], merging=True)
            elif len(tuple) == 2:
                self.add_monopredicate(id_map[tuple[0]], id_map[tuple[1]],
                                       predicate_id=id_map[inst_id], merging=True)

    def copy(self):
        cp = ConceptGraph()
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
        bpi = self.bipredicate_instance_index.items()
        for (source, target, label), predicate_insts in bpi:
            nodes.update({source, target, label, *predicate_insts})
        nodes.update(self.bipredicate_graph.nodes())
        mpi = self.monopredicate_instance_index.items()
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
                    elif missing_args == 0: # bipredicate
                        new_graph.add_bipredicate(*components, predicate_id=pre_pred_inst, merging=True)
                    else:
                        raise Exception('generate_inference_graph is trying to process a predicate with impossible format!')
                else:
                    raise Exception('generate_inference_graph encountered a precondition that is not a predicate!')
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
        s = time.time()
        print('** SOLUTIONS **')
        solns = list(prolog.query(inference_query))
        parsed_solns = [json.loads(json.dumps(soln, cls=PyswipEncoder)) for soln in solns]
        for soln in parsed_solns:
            print(json.dumps(soln, indent=4))
        print('Ran inferences in %.3f'%(time.time()-s))
        return inference_map, parsed_solns

    def to_knowledge_prolog(self):
        self_type = []
        type_rules = []
        rules = []
        for tuple, inst_id in self.predicate_instances():
            if len(tuple) == 3: # bipredicates
                subject, object, pred_type = tuple
                if pred_type == 'type':
                    for t in self.get_all_types(subject, object):
                        type_rules.append('type(%s,%s)'%(subject,t))
                else:
                    rules.append('predinst(%s(%s,%s),%s)'%(pred_type,subject,object,inst_id))
            else:
                subject, pred_type = tuple
                if pred_type not in ['var', 'is_type']:
                    rules.append('predinst(%s(%s),%s)' % (pred_type, subject, inst_id))

        return self_type + type_rules + rules

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

