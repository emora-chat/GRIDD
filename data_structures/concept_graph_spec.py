
from structpy import specification
import os, json


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
            ('Peter', 'happy'),
            ('Jack', 'happy'),
            ('Peter', 'dislikes', 'Mary')
        ], namespace='x')
        return concept_graph

    def has(concept_graph, concept=None, predicate_type=None, object=None, predicate_id=None):
        """
        Check membership of a concept, predicate instance, or predicate signature.
        """
        assert concept_graph.has('Mary')
        assert not concept_graph.has('Mary', 'likes')
        assert concept_graph.has('Peter', 'happy')
        assert not concept_graph.has('Peter', 'happy', 'John')
        assert concept_graph.has('John', 'likes', 'Mary')
        assert concept_graph.has('Peter', 'likes', 'John', 'pjl_1')
        # assert concept_graph.has(predicate_type='dislikes')
        assert concept_graph.has(predicate_id='pjl_1')
        assert concept_graph.has('Peter', predicate_id='pjl_1')
        assert concept_graph.has('Mary', object='Peter')
        assert concept_graph.has('Jack')

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
            ('Peter', 'happy', None, 'x_3'),
            ('Peter', 'dislikes', 'Mary', 'x_5')
        }
        assert set(concept_graph.predicates('Peter', 'likes')) == {
            ('Peter', 'likes', 'John', 'pjl_1'),
            ('Peter', 'likes', 'Sarah', 'x_2')
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

    def subjects(concept_graph, concept, type=None):
        """
        Return a set of related concepts to `concept`, where each element of the
        iterable appears as the subject in a predicate with `concept`.
        """
        assert concept_graph.subjects('Sarah') == {'Peter'}
        assert concept_graph.subjects('Mary', 'likes') == {'John'}
        assert concept_graph.subjects('Mary', 'dislikes') == {'Peter'}

    def objects(concept_graph, concept, type=None):
        """
        Return a set of related concepts to `concept`, where each element of the
        iterable appears as the object in a predicate with `concept`.
        """
        assert concept_graph.objects('Peter') == {'John', 'Sarah', 'Mary'}
        assert concept_graph.objects('Peter', 'likes') == {'John', 'Sarah'}
        assert concept_graph.objects('Peter', 'dislikes') == {'Mary'}

    def related(concept_graph, concept, type=None):
        """
        Return an iterable of related concepts to `concept`, where each element of the
        iterable appears in a predicate with `concept`.
        """
        assert set(concept_graph.related('Peter')) == {'John', 'Sarah', 'Mary'}

    @specification.init
    def CONCEPT_GRAPH_MUTATORS(ConceptGraph, predicates=None, concepts=None, namespace=None):
        """
        """
        concept_graph = ConceptGraph(predicates=[
            ('John', 'likes', 'Mary'),
            ('Mary', 'dislikes', 'Peter'),
            ('Peter', 'likes', 'John', 'pjl_1'),
            ('Peter', 'likes', 'Sarah'),
            ('Peter', 'happy'),
            ('Jack', 'happy')
        ], namespace='x')
        return concept_graph

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
        assert concept_graph.add('Mark', 'excited') == 'x_5'
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
        both concepts after the merge unless `concept_a`'s id contains the namespace whereas `concept_b`'s does not).

        If both concepts are a predicate instance, ValueError is raised.
        """
        concept_graph.merge('pjl_1', 'Sarah')
        assert concept_graph.has('Peter', 'likes', 'pjl_1')
        assert concept_graph.has('Peter', 'likes', 'John', 'pjl_1')

    @specification.init
    def concatenate(ConceptGraph, conceptgraph, predicate_exclusions=None):
        """
        Concatenate this concept graph with another.
        """
        cg1 = ConceptGraph(concepts=['princess', 'hiss'], namespace='1')
        cg1.add('princess', 'hiss')

        cg2 = ConceptGraph(concepts=['fluffy', 'bark', 'princess', 'friend'], namespace='2')
        fb = cg2.add('fluffy', 'bark')
        cg2.add('princess', 'friend', 'fluffy')
        cg2.add(fb, 'volume', 'loud')

        assert not cg1.has('fluffy')
        assert not cg2.has('hiss')

        cg1.concatenate(cg2)

        assert cg1.has('fluffy', 'bark')
        assert cg1.has('princess' , 'friend', 'fluffy')
        assert cg1.has('princess', 'hiss')
        assert cg1.predicate('1_1') in [('fluffy', 'bark', None, '1_1'),
                                        ('princess' , 'friend', 'fluffy', '1_1')]
        fb_merge = cg1.predicates('fluffy', 'bark', None)[0][3]
        assert cg1.has(fb_merge, 'volume', 'loud')

        return cg1

    def copy(concept_graph, namespace=None):
        """
        Construct a copy of the current concept graph.

        All concept ids are maintained, unless a new namespace is specified.

        If a new namespace is specified, it replaces the original namespace concept ids.
        """
        new_cg = concept_graph.copy()

        assert new_cg.has('fluffy', 'bark')
        assert new_cg.has('princess' , 'friend', 'fluffy')
        assert new_cg.has('princess', 'hiss')
        assert new_cg.predicate('1_0') == concept_graph.predicate('1_0')
        assert new_cg.predicate('1_1') == concept_graph.predicate('1_1')
        assert new_cg.predicate('1_2') == concept_graph.predicate('1_2')
        assert new_cg.predicate('1_3') == concept_graph.predicate('1_3')
        assert new_cg.predicates() == concept_graph.predicates()

        final_pred_subj = concept_graph.predicates('fluffy', 'bark', None)[0][3]
        assert new_cg.has(final_pred_subj, 'volume', 'loud')

        namespace_cg = concept_graph.copy(namespace="new")
        assert namespace_cg.predicates('fluffy', 'bark', None)[0][3].startswith("new")
        assert namespace_cg.predicates('princess' , 'friend', 'fluffy')[0][3].startswith("new")
        assert namespace_cg.predicates('princess', 'hiss', None)[0][3].startswith("new")
        for i in range(4):
            assert not namespace_cg.has(predicate_id='1_%d'%i)
            assert namespace_cg.has(predicate_id='new_%d'%i)

    def save(concept_graph, json_filepath):
        path = os.path.join('data_structures','checkpoints','save_test.json')
        concept_graph.save(path)

        with open(path, 'r') as f:
            d = json.load(f)
        lines = d['predicates']

        assert d['namespace'] == '1'
        assert len(lines) == 4
        assert 'princess,hiss,None,1_0' in lines
        assert 'fluffy,bark,None,1_1' in lines
        assert 'princess,friend,fluffy,1_2' in lines
        assert '1_1,volume,loud,1_3' in lines

    @specification.init
    def load(ConceptGraph, json_filepath):
        cg1 = ConceptGraph(concepts=['princess', 'hiss'], namespace='1')
        a = cg1.add('princess', 'hiss')
        cg1.add(a, 'volume', 'loud')
        cg1_file = os.path.join('data_structures','checkpoints','load_test_cg1.json')
        cg1.save(cg1_file)

        cg2 = ConceptGraph(concepts=['fluffy', 'bark', 'princess', 'friend'], namespace='2')
        cg2.add('fluffy', 'bark')
        cg2.add('princess', 'friend', 'fluffy')
        cg2_file = os.path.join('data_structures', 'checkpoints', 'load_test_cg2.json')
        cg2.save(cg2_file)

        cg3 = ConceptGraph(namespace='1')
        cg3.load(cg1_file)

        assert cg3.has('princess', 'hiss')
        assert cg3.predicate(a) == ('princess', 'hiss', None, a)

        cg3.load(cg2_file)

        assert cg3.has('fluffy', 'bark')
        assert cg3.has('princess', 'friend', 'fluffy')
        assert cg3.predicates('princess', 'friend', 'fluffy')[0][3].startswith("1")

        b = cg3.add('fluffy', 'friend', 'princess')
        assert b == '1_4'
        return cg3

    def concepts(concept_graph):
        """
        Get all nodes in the concept graph
        """
        assert concept_graph.concepts() == {'fluffy','bark','princess','hiss','volume','loud','friend',
                                            '1_0', '1_1', '1_2', '1_3', '1_4'}

    def pretty_print(concept_graph, predicate_exclusions=None):
        """
        Prints the predicates of concept_graph in a human-readable format,
        defined by the knowledge base text file format.
        """
        concept_graph.add('dog', 'type', 'entity')
        concept_graph.add(concept_graph._get_next_id(), 'type', 'dog')
        concept_graph.add(concept_graph._get_next_id(), 'type', 'dog')
        concept_graph.add('polly', 'type', 'dog')

        pi = concept_graph.add('polly','hiss')
        concept_graph.add(pi, 'volume', 'loud')

        print_collection = set(concept_graph.pretty_print().split('\n'))
        assert print_collection == {
            '',
            'ph/hiss(princess)',
            'pvl/volume(ph,loud)',
            'fb/bark(fluffy)',
            'pff/friend(princess,fluffy)',
            'ffp/friend(fluffy,princess)',
            'dte/type(dog,entity)',
            'ptd/type(polly,dog)',
            'dtd/type(dog_1,dog)',
            'dtd_2/type(dog_2,dog)',
            'ph_2/hiss(polly)',
            'pvl_2/volume(ph_2,loud)'
        }

        print_collection = set(concept_graph.pretty_print(predicate_exclusions={'friend'}).split('\n'))
        assert print_collection == {
            '',
            'ph/hiss(princess)',
            'pvl/volume(ph,loud)',
            'fb/bark(fluffy)',
            'dte/type(dog,entity)',
            'ptd/type(polly,dog)',
            'dtd/type(dog_1,dog)',
            'dtd_2/type(dog_2,dog)',
            'ph_2/hiss(polly)',
            'pvl_2/volume(ph_2,loud)'
        }








