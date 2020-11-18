
from structpy import specification

@specification
class ConceptGraphSpec:
    """
    """

    @specification.init
    def CONCEPT_GRAPH(ConceptGraph, edges=None, nodes=None):
        """
        """
        cg = ConceptGraph([
            ('John', 'Mary', 'likes'),
            ('Mary', 'Peter', 'likes'),
            ('Peter', 'John', 'likes'),
            ('Peter', 'Sarah', 'likes')
        ])

        assert cg.bipredicate_map[('John', 'Mary', 'likes')] == 'John-Mary-likes'
        assert cg.bipredicate_map.reverse()['John-Mary-likes'] == ('John', 'Mary', 'likes')
        return cg

    def add_node(cg, node):
        pass

    def add_monopredicate(cg, source, label, predicate_id=None):
        pass

    def add_bipredicate(cg, source, target, label, predicate_id=None):
        """
        """
        pred_id = cg.add_bipredicate('Peter', 'Mary', 'hates', 'new_id')
        assert pred_id == 'new_id'
        assert cg.bipredicate_graph.has('Peter', 'Mary', 'hates')
        assert cg.bipredicate_map[('Peter', 'Mary', 'hates')] == 'new_id'
        assert cg.bipredicate_map.reverse()['new_id'] == ('Peter', 'Mary', 'hates')

        # Adding nested predicate

        in2 = cg.add_bipredicate('John-Mary-likes', 'Mary-Peter-likes', 'because',
                                 predicate_id='nested_pred')
        in3 = cg.add_bipredicate('you', 'nested_pred', 'hate')

        assert cg.subject('nested_pred') == 'John-Mary-likes'
        assert cg.object('nested_pred') == 'Mary-Peter-likes'
        assert cg.type('nested_pred') == 'because'

        # Adding multiple predicates between the same source and target node

        cg.add_bipredicate('i', 'smart', 'am')
        cg.add_bipredicate('i', 'smart', 'value')
        cg.add_bipredicate('i', 'happy', 'am')
        cg.add_bipredicate('i', 'happy', 'want')

        assert cg.bipredicate_graph.has('i', 'happy', 'am')
        assert cg.bipredicate_graph.has('i', 'happy', 'want')

        assert cg.predicates_between('i', 'happy') == {('i', 'happy', 'am'),
                                                       ('i', 'happy', 'want')}

    def remove_node(cg, node):
        cg.remove_node('Mary')
        assert not cg.bipredicate_graph.has('Mary')
        assert cg.bipredicate_graph.has('John')
        assert cg.bipredicate_graph.has('Peter')
        assert not cg.bipredicate_graph.has('John', 'Mary', 'likes')
        assert not cg.bipredicate_graph.has('Mary', 'Peter', 'likes')
        assert not cg.bipredicate_graph.has('Peter', 'Mary', 'hates')
        assert ('John', 'Mary', 'likes') not in cg.bipredicate_map
        assert ('Mary', 'Peter', 'likes') not in cg.bipredicate_map
        assert ('Peter', 'Mary', 'hates') not in cg.bipredicate_map

    def remove_bipredicate(cg, node, target, label):
        cg.remove_bipredicate('Peter', 'John', 'likes')
        assert cg.bipredicate_graph.has('Peter')
        assert cg.bipredicate_graph.has('John')
        assert not cg.bipredicate_graph.has('Peter', 'John', 'likes')
        assert ('Peter', 'John', 'likes') not in cg.bipredicate_map

    def remove_monopredicate(cg, node, label):
        pass

    def predicates(cg, node, predicate_type=None):
        cg.add_bipredicate('John', 'Mary', 'likes')
        cg.add_bipredicate('Mary', 'Peter', 'likes')
        cg.add_bipredicate('Peter', 'John', 'likes')
        cg.add_bipredicate('Peter', 'Sarah', 'likes')
        cg.add_bipredicate('Peter', 'Mary', 'hates')
        assert cg.predicates('Mary') == {('John', 'Mary', 'likes'),
                                         ('Mary', 'Peter', 'likes'),
                                         ('Peter', 'Mary', 'hates')}

        assert cg.predicates('Mary', 'likes') == {('John', 'Mary', 'likes'),
                                                  ('Mary', 'Peter', 'likes')}

    def bipredicates(cg, node, predicate_type=None):
        pass

    def monopredicates(cg, node):
        pass

    def predicates_of_subject(cg, node, predicate_type=None):
        assert cg.predicates_of_subject('Mary', 'likes') == {('Mary', 'Peter', 'likes')}

    def bipredicates_of_subject(cg, node, predicate_type=None):
        pass

    def monopredicates_of_subject(cg, node):
        pass

    def predicates_of_object(cg, node, predicate_type=None):
        assert cg.predicates_of_object('Mary', 'likes') == {('John', 'Mary', 'likes')}

    def bipredicate(cg, subject, type, object):
        pass

    def monopredicate(cg, subject, type):
        pass

    def neighbors(cg, node, predicate_type=None):
        pass

    def subject_neighbors(cg, node, predicate_type=None):
        assert cg.subject_neighbors('Mary') == {'John', 'Peter'}

    def object_neighbors(cg, node, predicate_type=None):
        assert cg.object_neighbors('Mary') == {'Peter'}

    def subject(cg, predicate_instance):
        pass

    def object(cg, predicate_instance):
        pass

    def type(cg, predicate_instance):
        pass

    def concepts(cg):
        pass

    def predicates_between(cg, node1, node2):
        assert cg.predicates_between('Mary', 'Peter') == {('Mary', 'Peter', 'likes'),
                                                          ('Peter', 'Mary', 'hates')}

