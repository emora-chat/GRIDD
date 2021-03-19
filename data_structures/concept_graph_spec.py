
from structpy import specification
import json, time
from os.path import join
import GRIDD.globals
from GRIDD.data_structures.node_features import NodeFeatures
from GRIDD.data_structures.spanning_node import SpanningNode

checkpoints = join('GRIDD', 'resources', 'checkpoints')


@specification
class ConceptGraphSpec:
    """
    Data structure allowing definition of logic predicates, organized in graph form for
    fast and flexible access patterns.

    Predicates take general tuple form (subject, predicate_type, object, predicate_id).
    """

    @specification.init
    def CONCEPT_GRAPH(ConceptGraph, predicates=None, concepts=None, namespace=None,  feature_cls=GRIDD.globals.FEATURE_CLS):
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
        ], namespace='x_', feature_cls=NodeFeatures)
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

    def concepts(concept_graph):
        """
        Get all nodes in the concept graph
        """
        assert set(concept_graph.concepts()) == {'Peter', 'John', 'Sarah', 'Mary', 'Jack',
                                            'likes', 'happy', 'dislikes',
                                            'pjl_1', 'x_0', 'x_1', 'x_2', 'x_3', 'x_4', 'x_5'}

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

    def to_graph(concept_graph):
        """
        Convert the ConceptGraph into a Digraph of s/t/o edges.
        """
        graph = concept_graph.to_graph()
        assert graph.has('pjl_1', 'Peter', 's')
        assert graph.has('pjl_1', 'John', 'o')
        assert graph.has('pjl_1', 'likes', 't')
        assert graph.has('Sarah')

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
        ], namespace='x_')
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

    def merge(concept_graph, concept_a, concept_b, strict_order=False):
        """
        Merge two concepts together in the concept graph.

        If `strict_order` is False,
            `concept_a`'s id represents both concepts after the merge
            unless `concept_a`'s id contains the namespace whereas `concept_b`'s does not.
        Otherwise,
            `concept_a`'s is the maintained id.

        If both concepts are a predicate instance, ValueError is raised.
        """
        concept_graph.features['pjl_1']['cover'] = 0
        concept_graph.features['Sarah']['cover'] = 1
        concept_graph.merge('pjl_1', 'Sarah')
        assert concept_graph.has('Peter', 'likes', 'pjl_1')
        assert concept_graph.has('Peter', 'likes', 'John', 'pjl_1')
        assert concept_graph.features['pjl_1']['cover'] == 1

    @specification.init
    def id_map(ConceptGraph, other):
        """
        Provide a mapping of ids from `ConceptGraph other` to this Concept Graph.
        """
        a = ConceptGraph([
            ('I', 'like', 'ice cream'),
            ('I', 'hate', 'dogs', 'ihd')
        ], namespace='x_')
        b = ConceptGraph([
            ('Something', 'is', 'happening')
        ], namespace='y_')

        idm = b.id_map(a)
        assert idm.get('ihd') == 'ihd'
        assert idm.get('x_0') == 'y_1'
        assert idm['x_0'] == 'y_1'
        assert idm.identify('y_1') == 'x_0'

    @specification.init
    def concatenate(ConceptGraph, conceptgraph, predicate_exclusions=None):
        """
        Concatenate this concept graph with another.
        """
        cg1 = ConceptGraph(concepts=['princess', 'hiss'], namespace='1_')
        cg1.add('princess', 'hiss')
        cg1.features['princess']['salience'] = 0.5
        cg1.features['princess']['cover'] = 0.5

        cg2 = ConceptGraph(concepts=['fluffy', 'bark', 'princess', 'friend'], namespace='2_')
        fb = cg2.add('fluffy', 'bark')
        cg2.add('princess', 'friend', 'fluffy')
        cg2.add(fb, 'volume', 'loud')
        cg2.features['princess']['salience'] = 0.75
        cg2.features['princess']['cover'] = 0.25

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

        assert cg1.features['princess']['salience'] == 0.75
        assert cg1.features['princess']['cover'] == 0.5

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

        namespace_cg = concept_graph.copy(namespace="new_")
        assert namespace_cg.predicates('fluffy', 'bark', None)[0][3].startswith("new")
        assert namespace_cg.predicates('princess' , 'friend', 'fluffy')[0][3].startswith("new")
        assert namespace_cg.predicates('princess', 'hiss', None)[0][3].startswith("new")
        for i in range(4):
            assert not namespace_cg.has(predicate_id='1_%d'%i)
            assert namespace_cg.has(predicate_id='new_%d'%i)
        new_cg_features = new_cg.features.items()
        for item in concept_graph.features.items():
            assert item in new_cg_features

    def save(concept_graph, json_filepath=None):
        path = join(checkpoints, 'save_test.json')
        concept_graph.save(path)

    @specification.init
    def load(ConceptGraph, json_file_str_obj):
        cg1 = ConceptGraph(concepts=['princess', 'hiss'], namespace='1_')
        a = cg1.add('princess', 'hiss')
        cg1.add(a, 'volume', 'loud')
        cg1.features['princess']['salience'] = 0.75
        cg1.features['princess']['cover'] = 0.25
        cg1_file = join(checkpoints, 'load_test_cg1.json')
        cg1.save(cg1_file)

        cg2 = ConceptGraph(concepts=['fluffy', 'bark', 'princess', 'friend'], namespace='2_')
        cg2.add('fluffy', 'bark')
        cg2.add('princess', 'friend', 'fluffy')
        cg2_file = join(checkpoints, 'load_test_cg2.json')
        cg2.save(cg2_file)

        concept_graph = ConceptGraph(namespace='1_')
        concept_graph.load(cg1_file)

        assert concept_graph.has('princess', 'hiss')
        assert concept_graph.predicate(a) == ('princess', 'hiss', None, a)
        assert concept_graph.features['princess']['salience'] == 0.75
        assert concept_graph.features['princess']['cover'] == 0.25

        concept_graph.load(cg2_file)

        assert concept_graph.has('fluffy', 'bark')
        assert concept_graph.has('princess', 'friend', 'fluffy')
        assert concept_graph.predicates('princess', 'friend', 'fluffy')[0][3].startswith('1')
        assert concept_graph.features['princess']['salience'] == 0.75
        assert concept_graph.features['princess']['cover'] == 0.25

        b = concept_graph.add('fluffy', 'friend', 'princess')
        assert b == '1_4'
        return concept_graph

    def pretty_print(concept_graph, predicate_exclusions=None):
        """
        Prints the predicates of concept_graph in a human-readable format,
        defined by the knowledge base text file format.
        """
        concept_graph.add('dog', 'type', 'entity')
        concept_graph.add(concept_graph.id_map().get(), 'type', 'dog')
        concept_graph.add(concept_graph.id_map().get(), 'type', 'dog')
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

        print_collection = set(concept_graph.pretty_print(exclusions={'friend'}).split('\n'))
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

    @specification.init
    def to_spanning_tree(ConceptGraph):
        # cg = ConceptGraph(namespace='x_', predicates=[
        #     ('user', 'type', 'person'),
        #     ('georgia', 'type', 'state'),
        #     ('user', 'go', 'georgia', 'ugg'),
        #     ('ugg', 'time', 'july', 'utj'),
        #     ('july', 'property', 'mid'),
        #     ('utj', 'property', 'last'),
        #     ('ugg', 'mode', 'plane'),
        #     ('person_1', 'type', 'person'),
        #     ('user', 'sister', 'person_1'),
        #     ('user', 'visit', 'person_1', 'uvp'),
        #     ('ugg', 'cause', 'uvp'),
        #     ('house_1', 'type', 'house'),
        #     ('uvp', 'locate', 'house_1'),
        #     ('person_1', 'possess', 'house_1'),
        #     ('house_1', 'property', 'new'),
        #     ('"user"', 'expr', 'user'),
        #     ('"person"', 'expr', 'person'),
        #     ('"georgia"', 'expr', 'georgia'),
        #     ('"state"', 'expr', 'state'),
        #     ('"go"', 'expr', 'go'),
        #     ('"time"', 'expr', 'time'),
        #     ('"july"', 'expr', 'july'),
        #     ('"mode"', 'expr', 'mode'),
        #     ('"plane"', 'expr', 'plane'),
        #     ('"sister"', 'expr', 'sister'),
        #     ('"visit"', 'expr', 'visit'),
        #     ('"cause"', 'expr', 'cause'),
        #     ('"house"', 'expr', 'house'),
        #     ('"locate"', 'expr', 'locate'),
        #     ('"possess"', 'expr', 'possess'),
        #     ('"property"', 'expr', 'property'),
        #     ('"new"', 'expr', 'new'),
        #     ('"last"', 'expr', 'last'),
        #     ('"mid"', 'expr', 'mid')
        # ])

        # cg = KnowledgeParser.from_data('''
        # like(d/dog(),b/bone())
        # aunt(john,a/person())
        # apd/possess(a,d)
        # property(apd,illegal)
        #
        # ''')

        cg = ConceptGraph(predicates=[
            ('d', 'type', 'dog', 'dtd'),
            ('b', 'type', 'bone', 'btb'),
            ('a', 'type', 'person', 'atp'),
            ('sally', 'buy', 'b', 'sbb'),
            ('d', 'like', 'sbb', 'dlb'),
            ('dlb', 'degree', 'really', 'ddr'),
            ('john', 'aunt', 'a', 'jaa'),
            ('a', 'possess', 'd', 'apd'),
            ('apd', 'property', 'illegal', 'api'),
            ('"dog"', 'expr', 'dog'),
            ('"person"', 'expr', 'person'),
            ('"bone"', 'expr', 'bone'),
            ('"buy"', 'expr', 'buy'),
            ('"like"', 'expr', 'like'),
            ('"degree"', 'expr', 'degree'),
            ('"really"', 'expr', 'really'),
            ('"aunt"', 'expr', 'aunt'),
            ('"possess"', 'expr', 'possess'),
            ('"property"', 'expr', 'property'),
            ('"illegal"', 'expr', 'illegal'),
            ('"john"', 'expr', 'john'),
            ('"sally"', 'expr', 'sally'),
            ('dlb', 'assert')
        ])
        root = SpanningNode('__root__')
        like = SpanningNode('dlb', 'like')
        d = SpanningNode('d')
        dog = SpanningNode('dog')
        dtd = SpanningNode('dtd', 'type')
        b = SpanningNode('b')
        bone = SpanningNode('bone')
        btb = SpanningNode('btb', 'type')
        buy = SpanningNode('sbb', 'buy')
        john = SpanningNode('john')
        sally = SpanningNode('sally')
        degree = SpanningNode('ddr', 'degree')
        really = SpanningNode('really')
        rpossess = SpanningNode('apd', 'possess', 'r')
        a = SpanningNode('a')
        person = SpanningNode('person')
        atp = SpanningNode('atp')
        raunt = SpanningNode('jaa', 'aunt', 'r')
        property = SpanningNode('api', 'property')
        illegal = SpanningNode('illegal')

        root.children['link'] = [like]
        like.children['arg0'] = [d]
        like.children['arg1'] = [buy]
        like.children['link'] = [degree]
        d.children['link'] = [rpossess, dtd]
        buy.children['arg0'] = [sally]
        buy.children['arg1'] = [b]
        b.children['link'] = [btb]
        btb.children['arg1'] = [bone]
        degree.children['arg1'] = [really]
        rpossess.children['arg1'] = [a]
        rpossess.children['link'] = [property]
        dtd.children['arg1'] = [dog]
        a.children['link'] = [raunt, atp]
        atp.children['arg1'] = [person]
        raunt.children['arg1'] = [john]
        property.children['arg1'] = [illegal]

        s = time.time()
        span_tree_root = cg.to_spanning_tree()
        print('to spanning tree: %.5f sec'%(time.time()-s))
        assert root.equal(span_tree_root)

        s = time.time()
        cg.print_spanning_tree()
        print('print spanning tree: %.5f sec'%(time.time()-s))

    @specification.init
    def graph_component_siblings(ConceptGraph, source, target):
        """
        Checks whether `source` and `target` nodes are in the same graph component
        """
        cg1 = ConceptGraph(predicates=[
            ('bob', 'like', 'jenny', 'blj'),
            ('jenny', 'like', 'tom', 'jlt'),
            ('jlt', 'property', 'unconditionally', 'jpu')
        ])
        assert cg1.graph_component_siblings('bob', 'jenny')
        assert cg1.graph_component_siblings('jenny', 'bob')
        assert cg1.graph_component_siblings('bob', 'tom')
        assert cg1.graph_component_siblings('tom', 'bob')

        assert cg1.graph_component_siblings('unconditionally', 'jenny')
        assert cg1.graph_component_siblings('unconditionally', 'tom')
        assert cg1.graph_component_siblings('unconditionally', 'bob')
        assert cg1.graph_component_siblings('jpu', 'jlt')
        assert cg1.graph_component_siblings('jpu', 'jenny')
        assert cg1.graph_component_siblings('jpu', 'bob')

        cg1.add('tom', 'like', 'bob', 'tlb')
        assert cg1.graph_component_siblings('bob', 'tom')
        assert cg1.graph_component_siblings('tom', 'bob')













