
from structpy import specification

from data_structures.concept_graph_spec import ConceptGraphSpec
from data_structures.knowledge_base import KnowledgeBase


@specification
class WorkingMemorySpec:
    """
    Data structure that organizes a small set of predicates to apply inferences and
    interface with a larger `KnowledgeBase`.
    """

    @specification.satisfies(ConceptGraphSpec)
    def WORKING_MEMORY(WorkingMemory, knowledge_base, filenames_or_logicstrings):
        """

        """
        kb = '''
        animal<entity>
        dog<animal>
        chase<predicate>
        bark<predicate>
        fido=dog()
        victor=animal()
        chase(victor, fido)
        ;
        '''
        KB = KnowledgeBase(kb)
        return WorkingMemory(KB)

    def load(working_memory, filenames_or_logicstrings):
        """

        """
        wm = '''       
        fluffy=dog()
        chase(fido,fluffy)
        ;
        '''
        working_memory.load(wm)
        assert working_memory.has('fido')
        assert working_memory.has('fido','chase','fluffy')

    def pull_ontology(working_memory):
        """
        Add all concepts from the `.knowledge_base` that are super-types of concepts
        in working memory.
        """
        working_memory.pull_ontology()
        assert working_memory.has('fido', 'type', 'dog')
        assert working_memory.has('dog', 'type', 'animal')
        assert working_memory.has('animal', 'type', 'entity')

    def pull_rules(working_memory):
        """
        Add all concepts from the `.knowledge_base` that are part of some implication
        rule that may be satisfied by the predicates currently in working memory.
        """
        pass

    def pull(working_memory, order=1, concepts=None):
        """
        Gather and concatenate neighborhoods of concepts from the knowledge base into
        working memory.

        `order` specifies the neighborhood breadth, e.g. `order=2` would pull all concepts
        related to some concept in working memory by a predicate chain of length 2 or less.

        If `concepts` is specified, KB neighborhoods of each element of `concepts` is pulled
        into working memory. If `concepts` is `None`, the neighborhoods of each concept
        in working memory are pulled.
        """
        assert not working_memory.has('victor', 'chase', 'fido')
        working_memory.pull()
        assert working_memory.has('victor', 'chase', 'fido')

    def inferences(working_memory, types_or_rules):
        """
        Check and return all specified implications on predicates in working memory.

        Providing `str` concept ids will use rules from the pre/post conditions of the
        type with that id.

        Providing `str` file names ending with the `.kg` extension will use rules from
        the .kg file of that name.

        Providing `str` representing a logic string will use rule(s) from that logic string.
        """
        all_dogs_bark = '''
        x/dog()
        -> all_dogs_bark ->
        bark(x)
        ;
        '''
        solutions = working_memory.inferences(all_dogs_bark)
        assert len(solutions) == 1
        solution_value = solutions['all_dogs_bark'][0].values()
        assert len(solution_value) == 1
        assert 'fluffy' in solution_value

    def implications(working_memory, types_or_rules):
        all_dogs_bark = '''
        x/dog()
        -> all_dogs_bark ->
        bark(x)
        ;
        '''
        implications = working_memory.implications(all_dogs_bark)
        assert len(implications) == 2

    #todo - prune function of WorkingMemory
    def prune(working_memory, remaining=0, score_function=None):
        """
        Remove concepts from working memory one by one, in order of `score_function(concept)`
        until `remaining` or less concepts remain in working memory.

        Calling prune with no arguments will clear the working memory.
        """
        pass

    def rules(working_memory):
        """
        Find all rules in working memory and return as a dict of type_node_id to ImplicationRule object.
        """
        rule = '''       
        test_dog=dog()
        -> all_dogs_bark ->
        bark(test_dog)
        ;
        '''
        working_memory.load(rule)
        rules = working_memory.rules()
        assert len(rules) == 1
        assert 'all_dogs_bark' in rules
        assert rules['all_dogs_bark'].precondition.has('test_dog', 'type', 'dog')
        assert rules['all_dogs_bark'].postcondition.has('test_dog', 'bark')
