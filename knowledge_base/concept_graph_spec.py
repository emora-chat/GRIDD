
from structpy import specification


@specification
class ConceptGraphSpec:
    """
    Data structure allowing definition of logic predicates, organized in graph form for
    fast and flexible access patterns.

    Predicates take general tuple form (subject, predicate_type, object, predicate_id).
    """

    @specification.init
    def CONCEPT_GRAPH(ConceptGraph, predicates=None, concepts=None, namespace=None):
        """
        """
        concept_graph = ConceptGraph(predicates=[
            ('John', 'likes', 'Mary'),
            ('Mary', 'dislikes', 'Peter'),
            ('Peter', 'likes', 'John', 'pjl_1'),
            ('Peter', 'likes', 'Sarah'),
            ('Peter', 'happy')
        ], namespace='x')
        return concept_graph

    def has(concept_graph, concept=None, predicate_type=None, object=None, predicate_id=None):
        """
        Check membership of a concept, predicate instance, or predicate signature.
        """
        assert concept_graph.has('Mary')
        assert concept_graph.has('Mary', 'likes')
        assert concept_graph.has('Peter', 'happy')
        assert not concept_graph.has('Peter', 'happy', 'John')
        assert concept_graph.has('John', 'likes', 'Mary')
        assert concept_graph.has('Peter', 'likes', 'John', 'pjl_1')
        assert concept_graph.has(predicate_type='dislikes')
        assert concept_graph.has(predicate_id='pjl_1')
        assert concept_graph.has('Peter', predicate_id='pjl_1')
        assert concept_graph.has('Mary', object='Peter')

    def subject(concept_graph, predicate_id):
        """
        Get the subject of a given predicate.
        """
        assert concept_graph.subject('pjl_1') == 'Peter'

    def object(concept_graph, predicate_id):
        """
        Get the object of a given predicate.
        """
        assert concept_graph.object('pjl_1') == 'John'

    def type(concept_graph, predicate_id):
        """
        Get the type of a given predicate.
        """
        assert concept_graph.type('pjl_1') == 'likes'

    def predicate(concept_graph, predicate_id):
        """
        Get a 4-tuple predicate signature from a predicate id.

        Monopredicates are represented with a `None` value in the 3rd (object) position.
        """
        assert concept_graph.predicate('pjl_1') == ('Peter', 'likes', 'John', 'pjl_1')

    def predicates(concept_graph, subject=None, predicate_type=None, object=None):
        """
        Get an iterable of predicates in tuple (subject, predicate_type, object, predicate_instance) form.

        Monopredicates will be represented by `None` in the object position within the 4-tuple.
        """
        assert set(concept_graph.predicates('Peter')) == {
            ('Peter', 'likes', 'John', 'pjl_1'),
            ('Peter', 'likes', 'Sarah', 'x_2'),
            ('Peter', 'happy', None, 'x_3')
        }
        assert set(concept_graph.predicates('Peter', 'likes')) == {
            ('Peter', 'likes', 'Sarah', 'x_2'),
            ('Peter', 'happy', None, 'x_3')
        }
        assert set(concept_graph.predicates('Peter', 'likes', 'Sarah')) == {
            ('Peter', 'likes', 'Sarah', 'x_2')
        }
        assert set(concept_graph.predicates('Peter', object='Sarah')) == {
            ('Peter', 'likes', 'Sarah', 'x_2')
        }
        assert set(concept_graph.predicates(predicate_type='likes')) == {
            ('John', 'likes', 'Mary', 'x_0'),
            ('Peter', 'likes', 'John', 'pjl_1'),
            ('Peter', 'likes', 'Sarah', 'x_2'),
        }
        assert set(concept_graph.predicates(object='Peter')) == {
            ('Mary', 'dislikes', 'Peter', 'x_1')
        }
        assert set(concept_graph.predicates(predicate_type='likes', object='Sarah')) == {
            ('Peter', 'likes', 'Sarah', 'x_2')
        }

    def subjects(concept_graph, concept):
        """
        Return an iterable of related concepts to `concept`, where each element of the
        iterable appears in a predicate with `concept` as the subject.
        """
        assert set(concept_graph.subjects('Sarah')) == {'Peter'}

    def objects(concept_graph, concept):
        """
        Return an iterable of related concepts to `concept`, where each element of the
        iterable appears in a predicate with `concept` as the object.
        """
        assert set(concept_graph.objects('Peter')) == {'John', 'Sarah'}

    def related(concept_graph, concept):
        """
        Return an iterable of related concepts to `concept`, where each element of the
        iterable appears in a predicate with `concept`.
        """
        assert set(concept_graph.objects('Peter')) == {'John', 'Sarah', 'Mary'}

    def add(concept_graph, concept, predicate_type=None, object=None, predicate_id=None):
        """
        Add a concept or predicate to the ConceptGraph.

        If a `predicate_id` is specified and a concept with that id already exists,
        the concept becomes a predicate with the specified signature.

        Predicates added with no specified `predicate_id` will have one auto-generated.

        When adding a predicate, this method returns the added predicate id.

        When adding a concept, this method returns the concept id.
        """
        assert concept_graph.add('Mark') == 'Mark'
        assert concept_graph.has('Mark')
        assert concept_graph.add('Mark', 'excited') == 'x_4'
        assert concept_graph.has('Mark', 'excited')
        concept_graph.add('Mark', 'likes', 'John')
        assert concept_graph.has('Mark', 'likes', 'John')
        concept_graph.add('Mark', 'dislikes', 'Mary', 'mdm_1')
        assert concept_graph.has('Mark', 'dislikes', 'Mary', 'mdm_1')

    def remove(concept_graph, concept=None, predicate_type=None, object=None, predicate_id=None):
        """
        Remove a concept or predicate.

        Removing a concept results in all predicates the concept is involved in being removed also.

        If removing a predicate without specifying `predicate_id`, all predicates matching the
        signature are removed.

        A predicate can be removed by only specifying `predicate_id`.
        """
        concept_graph.remove('Mark', 'excited')
        assert not concept_graph.has('Mark', 'excited')
        concept_graph.remove('Mark', 'likes', 'John')
        assert not concept_graph.has('Mark', 'likes', 'John')
        concept_graph.remove(predicate_id='mdm_1')
        assert not concept_graph.has(predicate_id='mdm_1')
        concept_graph.remove('Mark')
        assert not concept_graph.has('Mark')

    def merge(concept_graph, concept_a, concept_b):
        """
        Merge two concepts together in the concept graph (`concept_a`'s id represents
        both concepts after the merge).

        If both concepts are a predicate instance, ValueError is raised.
        """
        concept_graph.merge('pjl_1', 'Sarah')
        assert concept_graph.has('Peter', 'likes', 'pjl_1')
        assert concept_graph.has('Peter', 'likes', 'John', 'pjl_1')

    def concatenate(concept_graph, conceptgraph):
        """
        Concatenate this concept graph with another.
        """
        pass





