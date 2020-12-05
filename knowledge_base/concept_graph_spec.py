
from structpy import specification
import pytest

@specification
class ConceptGraphSpec:
    """
    """

    @specification.init
    def CONCEPT_GRAPH(ConceptGraph, bipredicates=None, monopredicates=None, nodes=None):
        """
        """
        cg = ConceptGraph(bipredicates=[
            ('John', 'Mary', 'likes'), #0
            ('Mary', 'Peter', 'likes'), #1
            ('Peter', 'John', 'likes'), #2
            ('Peter', 'Sarah', 'likes') #3
        ])

        assert cg.bipredicate_instance_index[('John', 'Mary', 'likes')] == {0}
        assert cg.bipredicate_instance_index.reverse()[0] == ('John', 'Mary', 'likes')
        return cg

    def add_node(cg, node):
        """
        Add a node.
        """
        cg.add_node('Rob')
        assert cg.monopredicate_map['Rob'] == set()
        assert cg.bipredicate_graph.has('Rob')

    def add_nodes(cg, nodes):
        """
        Add a node from iterable
        """
        cg.add_nodes(['Stacy', 'happy'])
        assert 'Stacy' in cg.concepts() and 'happy' in cg.concepts()

    def add_monopredicate(cg, source, label, predicate_id=None, merging=False):
        """
        Add a monopredicate with optional predicate_id.
        Otherwise, predicate_id is automatically generated.

        If merging is false, then the predicate_id must be unique. Otherwise, the predicate_id may have
        already been created in the merging process and we are adding the predicate signature afterwards
        due to the merge order.

        :return: predicate_id
        """
        cg.add_monopredicate('Stacy', 'happy') #4
        assert cg.monopredicate_map['Stacy'] == {'happy'}
        assert cg.monopredicate_instance_index[('Stacy', 'happy')] == {4}

        cg.add_node('sad')
        cg.add_monopredicate('Rob', 'sad', predicate_id='sad(Rob)') #sad(Rob)
        assert cg.monopredicate_map['Rob'] == {'sad'}
        assert cg.monopredicate_instance_index[('Rob', 'sad')] == {'sad(Rob)'}

    def add_bipredicate(cg, source, target, label, predicate_id=None, merging=False):
        """
        Add a bipredicate with optional predicate_id.
        Otherwise, predicate_id is automatically generated.

        If merging is false, then the predicate_id must be unique. Otherwise, the predicate_id may have
        already been created in the merging process and we are adding the predicate signature afterwards
        due to the merge order.

        :return: predicate_id
        """
        cg.add_node('hates')
        pred_id = cg.add_bipredicate('Peter', 'Mary', 'hates', predicate_id='new_id') #new_id
        assert pred_id == 'new_id'
        assert cg.bipredicate_graph.has('Peter', 'Mary', 'hates')
        assert cg.bipredicate_instance_index[('Peter', 'Mary', 'hates')] == {'new_id'}
        assert cg.bipredicate_instance_index.reverse()['new_id'] == ('Peter', 'Mary', 'hates')

        # Adding nested predicate
        cg.add_nodes(['because', 'you'])
        in2 = cg.add_bipredicate(0, 1, 'because', predicate_id='nested_pred') #nested_pred
        in3 = cg.add_bipredicate('you', 'nested_pred', 'hates') #5

        assert cg.subject('nested_pred') == 0
        assert cg.object('nested_pred') == 1
        assert cg.type('nested_pred') == 'because'

        # Adding multiple predicates between the same source and target node
        cg.add_nodes(['i','smart','am','value','want'])
        cg.add_bipredicate('i', 'smart', 'am') #6
        cg.add_bipredicate('i', 'smart', 'value') #7
        cg.add_bipredicate('i', 'happy', 'am') #8
        cg.add_bipredicate('i', 'happy', 'want') #9

        assert cg.bipredicate_graph.has('i', 'happy', 'am')
        assert cg.bipredicate_graph.has('i', 'happy', 'want')

        assert cg.predicates_between('i', 'happy') == {('i', 'happy', 'am'),
                                                       ('i', 'happy', 'want')}

    def remove_node(cg, node):
        """
        Remove node.
        Removing a node removes all connected bipredicates and monopredicates.
        """
        cg.remove_node('Mary')
        assert not cg.bipredicate_graph.has('Mary')
        assert cg.bipredicate_graph.has('John')
        assert cg.bipredicate_graph.has('Peter')
        assert not cg.bipredicate_graph.has('John', 'Mary', 'likes')
        assert not cg.bipredicate_graph.has('Mary', 'Peter', 'likes')
        assert not cg.bipredicate_graph.has('Peter', 'Mary', 'hates')
        assert not cg.bipredicate_graph.has(0,1,'because')
        assert ('John', 'Mary', 'likes') not in cg.bipredicate_instance_index
        assert ('Mary', 'Peter', 'likes') not in cg.bipredicate_instance_index
        assert ('Peter', 'Mary', 'hates') not in cg.bipredicate_instance_index

        cg.add_nodes(['liver','eat','reason','think'])
        cg.add_bipredicate('Rob', 'liver', 'eat', predicate_id='eat(Rob,liver)') #eat(Rob,liver)
        cg.add_bipredicate('sad(Rob)', 'eat(Rob,liver)', 'reason', predicate_id='nested_Rob') #nested_Rob
        cg.add_monopredicate('sad(Rob)', 'think') #10
        cg.remove_node('Rob')
        assert 'Rob' not in cg.monopredicate_map
        assert ('Rob', 'sad') not in cg.monopredicate_instance_index
        assert ('sad(Rob)', 'think') not in cg.monopredicate_instance_index
        assert not cg.bipredicate_graph.has('sad(Rob)', 'eat(Rob,liver)', 'reason')
        assert 'nested_Rob' not in cg.bipredicate_instance_index.reverse()

    def remove_bipredicate(cg, node, target, label):
        """
        Remove bipredicate
        """
        cg.remove_bipredicate('Peter', 'John', 'likes')
        assert cg.bipredicate_graph.has('Peter')
        assert cg.bipredicate_graph.has('John')
        assert not cg.bipredicate_graph.has('Peter', 'John', 'likes')
        assert ('Peter', 'John', 'likes') not in cg.bipredicate_instance_index

    def remove_monopredicate(cg, node, label):
        """
        Remove monopredicate
        """
        cg.add_node('Sally')
        cg.add_monopredicate('Sally', 'sad') #11
        assert cg.monopredicate_map['Sally'] == {'sad'}
        assert cg.monopredicate_instance_index[('Sally', 'sad')] == {11}
        cg.remove_monopredicate('Sally', 'sad')
        assert cg.monopredicate_map['Sally'] == set()
        assert ('Sally', 'sad') not in cg.monopredicate_instance_index

    def predicates(cg, node, predicate_type=None):
        """
        Gets all predicates (bi and mono) that involve node

        If predicate_type is specified, then only bipredicates are returned
        """
        cg.add_nodes(['Mary','likes'])
        cg.add_bipredicate('John', 'Mary', 'likes') #12
        cg.add_bipredicate('Mary', 'Peter', 'likes') #13
        cg.add_bipredicate('Peter', 'John', 'likes') #14
        cg.add_bipredicate('Peter', 'Sarah', 'likes') #15
        cg.add_bipredicate('Peter', 'Mary', 'hates') #16
        assert cg.predicates('Mary') == {('John', 'Mary', 'likes'),
                                         ('Mary', 'Peter', 'likes'),
                                         ('Peter', 'Mary', 'hates')}

        assert cg.predicates('Mary', 'likes') == {('John', 'Mary', 'likes'),
                                                  ('Mary', 'Peter', 'likes')}

        cg.add_monopredicate('John', 'sad') #17
        assert cg.predicates('John') == {('John', 'Mary', 'likes'),
                                         ('Peter', 'John', 'likes'),
                                         ('John', 'sad')}
        assert cg.predicates('John', 'likes') == {('John', 'Mary', 'likes'),
                                                  ('Peter', 'John', 'likes')}

    def bipredicates(cg, node, predicate_type=None):
        """
        Gets all bipredicates that involve node
        """
        assert cg.bipredicates('John') == {('John', 'Mary', 'likes'),
                                         ('Peter', 'John', 'likes')}

    def monopredicates(cg, node):
        """
        Gets all monopredicates that involve node
        """
        assert cg.monopredicates('John') == {('John', 'sad')}

    def predicates_of_subject(cg, node, predicate_type=None):
        """
        Gets all predicates (bi and mono) that where node is the subject

        If predicate_type is specified, then only bipredicates are returned
        """
        assert cg.predicates_of_subject('Mary', 'likes') == {('Mary', 'Peter', 'likes')}

        assert cg.predicates_of_subject('John') == {('John', 'Mary', 'likes'),
                                                    ('John', 'sad')}

    def bipredicates_of_subject(cg, node, predicate_type=None):
        """
        Gets all bipredicates that where node is the subject
        """
        assert cg.bipredicates_of_subject('John') == {('John', 'Mary', 'likes')}

    def monopredicates_of_subject(cg, node):
        """
        Gets all monopredicates that where node is the subject
        """
        assert cg.monopredicates_of_subject('John') == {('John', 'sad')}

    def predicates_of_object(cg, node, predicate_type=None):
        """
        Gets all predicates where node is object

        * Only bipredicates have objects
        """
        assert cg.predicates_of_object('Mary', 'likes') == {('John', 'Mary', 'likes')}
        assert cg.predicates_of_object('John') == {('Peter', 'John', 'likes')}

    def bipredicate(cg, subject, object, type):
        """
        Get the bipredicate ids corresponding to the bipredicate defined by subject, object, and type

        Returns a set of ids
        """
        assert cg.bipredicate('John', 'Mary', 'likes') == {12}

    def monopredicate(cg, subject, type):
        """
        Get the monopredicate id corresponding to the monopredicate defined by subject and type
        """
        assert cg.monopredicate('John', 'sad') == {17}

    def neighbors(cg, node, predicate_type=None):
        """
        Get all neighboring nodes of the given node, with optional predicate type by which to filter
        """
        cg.add_node('Beth')
        cg.add_bipredicate('Mary', 'Beth', 'hates') #18
        assert cg.neighbors('Mary') == {'John', 'Peter', 'Beth'}
        assert cg.neighbors('Mary', 'hates') == {'Beth', 'Peter'}

    def subject_neighbors(cg, node, predicate_type=None):
        """
        Get all nodes which have a subject relation in a predicate with the given object node
        """
        assert cg.subject_neighbors('Mary') == {'John', 'Peter'}

    def object_neighbors(cg, node, predicate_type=None):
        """
        Get all nodes which have an object relation in a predicate with the given subject node
        """
        assert cg.object_neighbors('Mary') == {'Peter', 'Beth'}
        assert cg.object_neighbors('John') == {'Mary'}

    def subject(cg, predicate_instance):
        """
        Return the subject of the predicate
        """
        assert cg.subject(18) == 'Mary'
        assert cg.subject(17) == 'John'

    def object(cg, predicate_instance):
        """
        Return the object of the predicate
        """
        assert cg.object(18) == 'Beth'
        assert cg.object(17) is None

    def type(cg, predicate_instance):
        """
        Return the type of the predicate
        """
        assert cg.type(18) == 'hates'
        assert cg.type(17) == 'sad'

    def predicates_between(cg, node1, node2):
        """
        Get all bipredicates between node1 and node2
        """
        assert cg.predicates_between('Mary', 'Peter') == {('Mary', 'Peter', 'likes'),
                                                          ('Peter', 'Mary', 'hates')}

    def concepts(cg):
        """
        Get all nodes (subject, object, predicate type, and predicate instance)
        """
        cg.remove_node('Peter')
        cg.remove_node('i')
        assert cg.concepts() == {'Stacy', 'happy', 4,
                                 'John', 'sad', 17,
                                 'Mary', 'Beth', 'hates', 18,
                                 'likes', 12,
                                  'Sarah', 'because', 'you',
                                  'smart','am','value','want',
                                 'liver','eat','reason','think', 'Sally'}

    def add_bipredicate_on_label(cg, source, target, label):
        """
        Add a bipredicate on the label node (e.g. for specifying predicate_type constraints).
        Does not create an predicate instance for this bipredicate (the label node is the instance
        being directly modified).
        :return: label
        """
        id = cg.add_bipredicate_on_label('Stacy','liver','eat')
        assert cg.bipredicate('Stacy', 'liver', 'eat') == {'eat'}

    def add_monopredicate_on_label(cg, source, label):
        """
        Add a monopredicate on the label node (e.g. for specifying predicate_type constraints).
        Does not create an predicate instance for this monopredicate (the label node is the instance
        being directly modified).
        :return: label
        """
        pass

    def has(cg, nodes):
        """
        Check whether node(s) has been added to the concept graph.

        Nodes can be either string or list.
        """
        assert cg.has('Stacy')
        assert cg.has('eat')
        assert cg.has('liver')
        assert cg.has(['Stacy', 'eat', 'liver'])

        ## OUT OF PLACE - Test of multiple bipredicates with the same signature source,target,label

        cg.add_node('i')
        cg.add_bipredicate('i', 'Stacy', 'hates') #19
        cg.add_bipredicate('i', 'Stacy', 'hates') #20
        assert cg.predicates_of_subject('i', predicate_type='hates') == {('i', 'Stacy', 'hates'),
                                                                         ('i', 'Stacy', 'hates')}
        cg.remove_bipredicate('i', 'Stacy', 'hates')
        assert len(cg.predicates_of_subject('i', predicate_type='hates')) == 0
        assert ('i', 'Stacy', 'hates') not in cg.bipredicate_instance_index

        ## OUT OF PLACE - Test of multiple monopredicates with the same signature source,label
        cg.add_monopredicate('Stacy', 'happy') #21
        assert cg.monopredicates('Stacy') == {('Stacy', 'happy'),
                                              ('Stacy', 'happy')}
        assert cg.predicates_of_subject('Stacy', predicate_type='happy') == {('Stacy', 'happy'),
                                                                             ('Stacy', 'happy')}

        assert cg.subject(4) == 'Stacy'
        assert cg.type(4) == 'happy'
        assert cg.subject(21) == 'Stacy'
        assert cg.type(21) == 'happy'

    def merge(self, other_graph):
        """
        Merge all predicates from another concept graph into this one

        All predicate and entity instances with integer ids from other_graph are mapped to new integer ids
        in current graph to avoid collisions.
        """
        import knowledge_base.concept_graph
        cg2 = knowledge_base.concept_graph.ConceptGraph(nodes=['princess','fluffy','hiss','bark','friend'])
        cg2.add_bipredicate('princess', 'fluffy', 'friend', predicate_id=12)

        next_id = self.next_id

        self.merge(cg2)

        assert self.bipredicate_graph.has('princess', 'fluffy', 'friend')
        assert self.bipredicate_instance_index[('princess', 'fluffy', 'friend')] == {next_id}
        assert self.bipredicate_graph.has('John', 'Mary', 'likes')
        assert self.bipredicate_instance_index[('John', 'Mary', 'likes')] == {12}

        cg2.remove_bipredicate('princess', 'fluffy', 'friend')
        cg2.add_monopredicate('princess', 'hiss', predicate_id=17)
        self.merge(cg2)

        assert 'hiss' in self.monopredicate_map['princess']
        assert self.monopredicate_instance_index[('princess', 'hiss')] == {next_id+1}
        assert 'sad' in self.monopredicate_map['John']
        assert self.monopredicate_instance_index[('John', 'sad')] == {17}

        cg2.remove_monopredicate('princess', 'hiss')
        cg2.add_monopredicate('fluffy', 'bark', predicate_id=10)
        self.merge(cg2)

        assert 'bark' in self.monopredicate_map['fluffy']
        assert self.monopredicate_instance_index[('fluffy', 'bark')] == {next_id+2}

        cg3 = knowledge_base.concept_graph.ConceptGraph(nodes=['daisy','buster','bark','reason','friend'])
        id1 = cg3.add_bipredicate('daisy', 'buster', 'friend')
        id2 = cg3.add_monopredicate('buster', 'bark')
        cg3.add_bipredicate(id1,id2,'reason')
        self.merge(cg3)

        id1 = self.bipredicate('daisy', 'buster', 'friend')
        id2 = self.monopredicate('buster', 'bark')
        assert len(list(id1)) == 1 and len(list(id2)) == 1
        id1 = list(id1)[0]
        id2 = list(id2)[0]
        assert next_id+3 <= id1 and next_id+3 <= id2
        id3 = self.bipredicate(id1,id2,'reason')
        assert id3

    def predicate_instances(self, node=None):
        """
        Returns list of all predicates in the form
        ((s,o,t), id) if bipredicate or ((s,t), id) if monopredicate
        """
        pass

    def bipredicate_instances(self):
        """
        Returns list of all bipredicates in the form ((s,o,t), id)
        """
        pass

    def monopredicate_instances(self):
        """
        Returns list of all monopredicates in the form ((s,t), id)
        """
        pass

    def get_all_types(self, node, parent=None):
        """
        Returns a set of all ancestor types of node.

        If parent is specified, only ancestors coming from the parent type are included.
        """
        import knowledge_base.concept_graph
        cg = knowledge_base.concept_graph.ConceptGraph(nodes=['type', 'sister',
                                                               'sibling', 'family', 'relationship',
                                                               'female', 'person'])
        cg.add_bipredicate('sister', 'sibling', 'type')
        cg.add_bipredicate('sibling', 'family', 'type')
        cg.add_bipredicate('family', 'relationship', 'type')
        cg.add_bipredicate('sister', 'female', 'type')
        cg.add_bipredicate('female', 'person', 'type')

        found_types = cg.get_all_types('sister')
        assert found_types == {'sibling', 'family', 'relationship', 'female', 'person'}

        found_types = cg.get_all_types('sister', 'sibling')
        assert found_types == {'sibling', 'family', 'relationship'}

        found_types = cg.get_all_types('sister', 'female')
        assert found_types == {'female', 'person'}




