from structpy.graph.directed.labeled.multilabeled_digraph_networkx import LabeledDigraphNX
from structpy.map.bijective.bimap import Bimap

class ConceptGraph:

    def __init__(self, edges=None, nodes=None):
        self.next_id = 0
        self.graph = LabeledDigraphNX(edges, nodes)
        if edges is not None:
            self.predicate_map = Bimap(
                {edge: '-'.join(edge) for edge in edges}
            )
        else:
            self.predicate_map = Bimap()

    def get_next_id(self):
        to_return = self.next_id
        self.next_id += 1
        return to_return

    def add_node(self, node):
        """
        Add a node.
        """
        self.graph.add(node)

    def add_predicate(self, source, target, label, predicate_id=None):
        """
        Add a predicate with optional predicate_id.
        Otherwise, predicate_id is automatically generated.
        :return: predicate_id
        """
        if predicate_id is None:
            predicate_id = '%s-%s-%s' % (source, target, label)
        self.graph.add(source, target, label)
        self.predicate_map[(source, target, label)] = predicate_id
        return predicate_id

    def remove(self, node, target=None, label=None):
        """
        Remove a node or edge.

        Edge removal can be specified by specifying the `target` and 'label'
        of the out-edge of `node`.

        Removing a node removes all connected in- and out-edges.
        """
        edges = list(self.predicate_map.items())
        if target is None:
            for edge, edge_id in edges:
                if edge[0] == node or edge[1] == node:
                    del self.predicate_map[edge]
            self.graph.remove(node)
        else:
            for edge, edge_id in edges:
                if edge[0] == node and edge[1] == target and edge[2] == label:
                    del self.predicate_map[edge]
            self.graph.remove(node, target, label)

    def subject(self, predicate_instance):
        return self.predicate_map.reverse()[predicate_instance][0]

    def object(self, predicate_instance):
        return self.predicate_map.reverse()[predicate_instance][1]

    def type(self, predicate_instance):
        return self.predicate_map.reverse()[predicate_instance][2]

    def predicates(self, node, predicate_type=None):
        edges = self.graph.out_edges(node, predicate_type)
        edges.update(self.graph.in_edges(node, predicate_type))
        return edges

    def predicates_of_subject(self, node, predicate_type=None):
        return self.graph.out_edges(node, predicate_type)

    def predicates_of_object(self, node, predicate_type=None):
        return self.graph.in_edges(node, predicate_type)

    def predicate(self, subject, type, object):
        return self.predicate_map[(subject, object, type)]

    def neighbors(self, node, predicate_type=None):
        nodes = self.graph.targets(node, predicate_type)
        nodes.update(self.graph.sources(node, predicate_type))
        return nodes

    def subject_neighbors(self, node, predicate_type=None):
        """
        Get all nodes which have a subject relation in a predicate with the object node
        :param node: the object
        :param predicate_type:
        :return:
        """
        return self.graph.sources(node, predicate_type)

    def object_neighbors(self, node, predicate_type=None):
        """
        Get all nodes which have an object relation in a predicate with the subject node
        :param node: the subject
        :param predicate_type:
        :return:
        """
        return self.graph.targets(node, predicate_type)

    def concepts(self):
        """
        Get all nodes (subject, object, predicate type, and predicate instance)
        """
        nodes = set()
        for (source, target, label), predicate_inst in self.predicate_map.items():
            nodes.update({source, target, label, predicate_inst})
        return nodes

    def predicates_between(self, node1, node2):
        return self.graph.edges(node1).intersection(self.graph.edges(node2))

if __name__ == '__main__':
    cg = ConceptGraph([
        ('John', 'Mary', 'likes'),
        ('Mary', 'Peter', 'likes'),
        ('Peter', 'John', 'likes'),
        ('Peter', 'Sarah', 'likes')
        ], ['Rob'])

    assert cg.predicate_map[('John', 'Mary', 'likes')] == 'John-Mary-likes'
    assert cg.predicate_map.reverse()['John-Mary-likes'] == ('John', 'Mary', 'likes')

    pred_id = cg.add_predicate('Peter', 'Mary', 'hates', 'new_id')

    assert pred_id == 'new_id'
    assert cg.graph.has('Peter', 'Mary', 'hates')
    assert cg.predicate_map[('Peter', 'Mary', 'hates')] == 'new_id'
    assert cg.predicate_map.reverse()['new_id'] == ('Peter', 'Mary', 'hates')

    assert cg.predicates('Mary') == {('John', 'Mary', 'likes'),
                                     ('Mary', 'Peter', 'likes'),
                                     ('Peter', 'Mary', 'hates')}

    assert cg.predicates('Mary', 'likes') == {('John', 'Mary', 'likes'),
                                                ('Mary', 'Peter', 'likes')}

    assert cg.predicates_of_subject('Mary', 'likes') == {('Mary', 'Peter', 'likes')}
    assert cg.predicates_of_object('Mary', 'likes') == {('John', 'Mary', 'likes')}

    assert cg.subject_neighbors('Mary') == {'John', 'Peter'}
    assert cg.object_neighbors('Mary') == {'Peter'}

    assert cg.predicates_between('Mary', 'Peter') == {('Mary', 'Peter', 'likes'),
                                                      ('Peter', 'Mary', 'hates')}

    cg.remove('Mary')
    assert not cg.graph.has('Mary')
    assert cg.graph.has('John')
    assert cg.graph.has('Peter')
    assert not cg.graph.has('John', 'Mary', 'likes')
    assert not cg.graph.has('Mary', 'Peter', 'likes')
    assert not cg.graph.has('Peter', 'Mary', 'hates')
    assert ('John', 'Mary', 'likes') not in cg.predicate_map
    assert ('Mary', 'Peter', 'likes') not in cg.predicate_map
    assert ('Peter', 'Mary', 'hates') not in cg.predicate_map

    cg.remove('Peter', 'John', 'likes')
    assert cg.graph.has('Peter')
    assert cg.graph.has('John')
    assert not cg.graph.has('Peter', 'John', 'likes')
    assert ('Peter', 'John', 'likes') not in cg.predicate_map

    test = 1

    cg = ConceptGraph()
    in0 = cg.add_predicate('i', 'movie', 'likes')
    in1 = cg.add_predicate('acting', 'good', 'was')
    assert cg.concepts() == {'i', 'movie', 'likes', 'i-movie-likes',
                             'acting', 'good', 'was', 'acting-good-was'}
    in2 = cg.add_predicate(in0, in1, 'because', 'nested_pred')
    in3 = cg.add_predicate('you', 'nested_pred', 'hate')

    assert cg.subject('nested_pred') == 'i-movie-likes'
    assert cg.object('nested_pred') == 'acting-good-was'
    assert cg.type('nested_pred') == 'because'

    assert cg.predicate('i', 'likes', 'movie') == 'i-movie-likes'

    test = 2

    cg = ConceptGraph()
    cg.add_predicate('i', 'smart', 'am')
    cg.add_predicate('i', 'smart', 'value')
    cg.add_predicate('i', 'happy', 'am')
    cg.add_predicate('i', 'happy', 'want')

    assert cg.graph.has('i', 'happy', 'am')
    assert cg.graph.has('i', 'happy', 'want')

    test = cg.predicates_between('i', 'happy')
    assert cg.predicates_between('i', 'happy') == {('i', 'happy', 'am'),
                                                   ('i', 'happy', 'want')}