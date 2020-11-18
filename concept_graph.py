from structpy.graph.directed.labeled.multilabeled_digraph_networkx import LabeledDigraphNX
from structpy.map.bijective.bimap import Bimap
from structpy.map.index.index import Index
from concept_graph_spec import ConceptGraphSpec

class ConceptGraph:

    def __init__(self, bipredicates=None, monopredicates=None):
        self.next_id = 0
        self.bipredicate_graph = LabeledDigraphNX(bipredicates)

        if bipredicates is not None:
            self.bipredicate_map = Bimap(
                {pred: '-'.join(pred) for pred in bipredicates}
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
                {pred: '-'.join(pred) for pred in monopredicates}
            )
        else:
            self.monopredicate_index = Index()
            self.monopredicate_map = Bimap()

    def get_next_id(self):
        to_return = self.next_id
        self.next_id += 1
        return to_return

    def add_node(self, node):
        """
        Add a node.
        """
        if self.bipredicate_graph.has(node):
            raise Exception('node already exists in bipredicates')
        self.bipredicate_graph.add(node)
        if node in self.monopredicate_index:
            raise Exception('node already exists in monopredicates')
        self.monopredicate_index[node] = set()

    def add_bipredicate(self, source, target, label, predicate_id=None):
        """
        Add a bipredicate with optional predicate_id.
        Otherwise, predicate_id is automatically generated.
        :return: predicate_id
        """
        if predicate_id is None:
            predicate_id = '%s-%s-%s' % (source, target, label)
        self.bipredicate_graph.add(source, target, label)
        self.bipredicate_map[(source, target, label)] = predicate_id
        return predicate_id

    def add_monopredicate(self, source, label, predicate_id=None):
        """
        Add a monopredicate with optional predicate_id.
        Otherwise, predicate_id is automatically generated.
        :return: predicate_id
        """
        if predicate_id is None:
            predicate_id = '%s-%s' % (source, label)
        if source not in self.monopredicate_index:
            self.monopredicate_index[source] = set()
        self.monopredicate_index[source].add(label)
        self.monopredicate_map[(source, label)] = predicate_id
        return predicate_id

    def remove_node(self, node):
        """
        Remove node.
        Removing a node removes all connected bipredicates and monopredicates.
        """
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
        """
        Remove bipredicate
        """
        id = self.bipredicate_map[(node, target, label)]
        del self.bipredicate_map[(node, target, label)]
        self.bipredicate_graph.remove(node, target, label)
        self.remove_node(id)

    def remove_monopredicate(self, node, label):
        """
        Remove monopredicate
        """
        id = self.monopredicate_map[(node, label)]
        del self.monopredicate_map[(node, label)]
        self.monopredicate_index[node].remove(label)
        self.remove_node(id)

    def subject(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][0]
        elif predicate_instance in self.monopredicate_map:
            return self.monopredicate_map.reverse()[predicate_instance][0]

    def object(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][1]
        elif predicate_instance in self.monopredicate_map:
            raise Exception('predicate is a monopredicate!')

    def type(self, predicate_instance):
        if predicate_instance in self.bipredicate_map.reverse():
            return self.bipredicate_map.reverse()[predicate_instance][2]
        elif predicate_instance in self.monopredicate_map:
            return self.monopredicate_map.reverse()[predicate_instance][1]

    def predicates(self, node, predicate_type=None):
        """
        Gets all predicates (bi and mono) that involve node

        If predicate_type is specified, then only bipredicates are returned
        """
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
        """
        Gets all predicates (bi and mono) that where node is the subject

        If predicate_type is specified, then only bipredicates are returned
        """
        predicates = self.bipredicates_of_subject(node, predicate_type)
        if predicate_type is None:
            predicates.update(self.monopredicates_of_subject(node))
        return predicates

    def bipredicates_of_subject(self, node, predicate_type=None):
        return self.bipredicate_graph.out_edges(node, predicate_type)

    def monopredicates_of_subject(self, node):
        return self.monopredicates(node)

    def predicates_of_object(self, node, predicate_type=None):
        """
        Gets all predicates where node is object

        * Only bipredicates have objects
        """
        return self.bipredicate_graph.in_edges(node, predicate_type)

    def bipredicate(self, subject, type, object):
        return self.bipredicate_map[(subject, object, type)]

    def monopredicate(self, subject, type):
        return self.monopredicate_map[(subject, type)]

    def neighbors(self, node, predicate_type=None):
        nodes = self.bipredicate_graph.targets(node, predicate_type)
        nodes.update(self.bipredicate_graph.sources(node, predicate_type))
        return nodes

    def subject_neighbors(self, node, predicate_type=None):
        """
        Get all nodes which have a subject relation in a predicate with the object node
        :param node: the object
        :param predicate_type:
        :return:
        """
        return self.bipredicate_graph.sources(node, predicate_type)

    def object_neighbors(self, node, predicate_type=None):
        """
        Get all nodes which have an object relation in a predicate with the subject node
        :param node: the subject
        :param predicate_type:
        :return:
        """
        return self.bipredicate_graph.targets(node, predicate_type)

    def concepts(self):
        """
        Get all nodes (subject, object, predicate type, and predicate instance)
        """
        nodes = set()
        for (source, target, label), predicate_inst in self.bipredicate_map.items():
            nodes.update({source, target, label, predicate_inst})
        nodes.update(set([predicate_inst for _, predicate_inst in self.monopredicate_map.items()]))
        return nodes

    def predicates_between(self, node1, node2):
        return self.bipredicate_graph.edges(node1).intersection(self.bipredicate_graph.edges(node2))

if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))

