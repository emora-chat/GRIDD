from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.map.map import Map
from structpy.map.index.index import Index
from knowledge_base.concept_graph_spec import ConceptGraphSpec

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

    # todo - for all int ids in other_graph, generate new id and create mapping from other_graph id to new id to use thereafter in merge
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

    ######################
    ## Access Functions ##
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

    def predicates_between(self, node1, node2):
        return self.bipredicate_graph.edges(node1).intersection(self.bipredicate_graph.edges(node2))

    def concepts(self):
        nodes = set()
        for (source, target, label), predicate_insts in self.bipredicate_instance_index.items():
            nodes.update({source, target, label, *predicate_insts})
        nodes.update(self.bipredicate_graph.nodes())
        for (source, label), predicate_insts in self.monopredicate_instance_index.items():
            nodes.update({source, label, *predicate_insts})
        nodes.update(self.monopredicate_map.keys())
        return nodes

    def predicate_instances(self):
        pred_inst = set()
        for tuple, predicate_insts in self.bipredicate_instance_index.items():
            for inst in predicate_insts:
                pred_inst.add((tuple,inst))
        for tuple, predicate_insts in self.monopredicate_instance_index.items():
            for inst in predicate_insts:
                pred_inst.add((tuple,inst))
        return pred_inst

    def bipredicate_instances(self):
        pred_inst = set()
        for tuple, predicate_insts in self.bipredicate_instance_index.items():
            for inst in predicate_insts:
                pred_inst.add((tuple,inst))
        return pred_inst

    def has(self, nodes):
        if isinstance(nodes, str):
            return nodes in self.concepts()
        elif isinstance(nodes, list):
            concepts = self.concepts()
            for n in nodes:
                if n not in concepts:
                    return False
            return True
        else:
            raise Exception(":param 'nodes' must be string or list")


if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))

