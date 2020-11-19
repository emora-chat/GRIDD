from structpy.graph.directed.labeled.multilabeled_digraph_networkx import LabeledDigraphNX
from structpy.map.bijective.bimap import Bimap
from structpy.map.index.index import Index
from concept_graph_spec import ConceptGraphSpec

class ConceptGraph:

    def __init__(self, bipredicates=None, monopredicates=None, nodes=None):
        self.next_id = 0
        self.bipredicate_graph = LabeledDigraphNX(bipredicates, nodes)

        if bipredicates is not None:
            self.bipredicate_map = Bimap(
                {pred: self.get_next_id() for pred in bipredicates}
            )
        else:
            self.bipredicate_map = Bimap()

        if monopredicates is not None:
            mps = {}
            for subject, label in monopredicates:
                if subject not in mps:
                    mps[subject] = set()
                mps[subject].add(label)
            self.monopredicate_index = Index(mps)

            self.monopredicate_map = Bimap(
                {pred: self.get_next_id() for pred in monopredicates}
            )
        else:
            self.monopredicate_index = Index()
            self.monopredicate_map = Bimap()

        if nodes is not None:
            for node in nodes:
                self.monopredicate_index[node] = set()

    def get_next_id(self):
        to_return = self.next_id
        self.next_id += 1
        return to_return

    def add_node(self, node):
        if self.bipredicate_graph.has(node):
            raise Exception('node %s already exists in bipredicates'%node)
        self.bipredicate_graph.add(node)
        if node in self.monopredicate_index:
            raise Exception('node %s already exists in monopredicates'%node)
        self.monopredicate_index[node] = set()

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_bipredicate(self, source, target, label, predicate_id=None):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif target not in concepts:
            raise Exception(":param 'target' error - node %s does not exist!" % target)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        if predicate_id is None:
            predicate_id = self.get_next_id()
        self.bipredicate_graph.add(source, target, label)
        self.bipredicate_map[(source, target, label)] = predicate_id
        return predicate_id

    def add_monopredicate(self, source, label, predicate_id=None):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        if predicate_id is None:
            predicate_id = self.get_next_id()
        if source not in self.monopredicate_index:
            self.monopredicate_index[source] = set()
        self.monopredicate_index[source].add(label)
        self.monopredicate_map[(source, label)] = predicate_id
        return predicate_id

    def add_bipredicate_on_label(self, source, target, label):
        concepts = self.concepts()
        if source not in concepts:
            raise Exception(":param 'source' error - node %s does not exist!" % source)
        elif target not in concepts:
            raise Exception(":param 'target' error - node %s does not exist!" % target)
        elif label not in concepts:
            raise Exception(":param 'label' error - node %s does not exist!" % label)
        self.bipredicate_graph.add(source, target, label)
        self.bipredicate_map[(source, target, label)] = label
        return label

    def remove_node(self, node):
        if self.bipredicate_graph.has(node):
            bipredicates = list(self.bipredicate_map.items())
            for bipredicate, id in bipredicates:
                if bipredicate[0] == node or bipredicate[1] == node:
                    self.remove_bipredicate(*bipredicate)
            self.bipredicate_graph.remove(node)

        if node in self.monopredicate_index:
            monopredicates = list(self.monopredicate_map.items())
            for monopredicate, id in monopredicates:
                if monopredicate[0] == node:
                    self.remove_monopredicate(*monopredicate)
            del self.monopredicate_index[node]

    def remove_bipredicate(self, node, target, label):
        id = self.bipredicate_map[(node, target, label)]
        del self.bipredicate_map[(node, target, label)]
        self.bipredicate_graph.remove(node, target, label)
        self.remove_node(id)

    def remove_monopredicate(self, node, label):
        id = self.monopredicate_map[(node, label)]
        del self.monopredicate_map[(node, label)]
        self.monopredicate_index[node].remove(label)
        self.remove_node(id)

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
        return set([(node, label) for label in self.monopredicate_index[node]])

    def predicates_of_subject(self, node, predicate_type=None):
        predicates = self.bipredicates_of_subject(node, predicate_type)
        if predicate_type is None:
            predicates.update(self.monopredicates_of_subject(node))
        return predicates

    def bipredicates_of_subject(self, node, predicate_type=None):
        return self.bipredicate_graph.out_edges(node, predicate_type)

    def monopredicates_of_subject(self, node):
        return self.monopredicates(node)

    def predicates_of_object(self, node, predicate_type=None):
        return self.bipredicate_graph.in_edges(node, predicate_type)

    def bipredicate(self, subject, object, type):
        return self.bipredicate_map[(subject, object, type)]

    def monopredicate(self, subject, type):
        return self.monopredicate_map[(subject, type)]

    def neighbors(self, node, predicate_type=None):
        nodes = self.bipredicate_graph.targets(node, predicate_type)
        nodes.update(self.bipredicate_graph.sources(node, predicate_type))
        return nodes

    def subject_neighbors(self, node, predicate_type=None):
        return self.bipredicate_graph.sources(node, predicate_type)

    def object_neighbors(self, node, predicate_type=None):
        return self.bipredicate_graph.targets(node, predicate_type)

    def subject(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][0]
        elif predicate_instance in self.monopredicate_map.reverse():
            return self.monopredicate_map.reverse()[predicate_instance][0]

    def object(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][1]
        elif predicate_instance in self.monopredicate_map.reverse():
            raise Exception('Cannot get object of a monopredicate!')

    def type(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][2]
        elif predicate_instance in self.monopredicate_map.reverse():
            return self.monopredicate_map.reverse()[predicate_instance][1]

    def predicates_between(self, node1, node2):
        return self.bipredicate_graph.edges(node1).intersection(self.bipredicate_graph.edges(node2))

    def concepts(self):
        nodes = set()
        for (source, target, label), predicate_inst in self.bipredicate_map.items():
            nodes.update({source, target, label, predicate_inst})
        nodes.update(self.bipredicate_graph.nodes())
        for (source, label), predicate_inst in self.monopredicate_map.items():
            nodes.update({source, label, predicate_inst})
        nodes.update(self.monopredicate_index.keys())
        return nodes

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

