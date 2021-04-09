
from structpy import specification

from GRIDD.data_structures.concept_graph_spec import ConceptGraphSpec
from GRIDD.data_structures.knowledge_base import KnowledgeBase


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

    def pull_ontology(working_memory, concepts=None):
        """
        Add all concepts from the `.knowledge_base` that are super-types of concepts
        in working memory.
        """
        working_memory.add('fido')
        working_memory.pull_ontology()
        assert working_memory.has('fido', 'type', 'dog')
        assert working_memory.has('dog', 'type', 'animal')
        assert working_memory.has('animal', 'type', 'entity')

    # todo
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

    #todo - prune function of WorkingMemory
    def prune(working_memory, remaining=0, score_function=None):
        """
        Remove concepts from working memory one by one, in order of `score_function(concept)`
        until `remaining` or less concepts remain in working memory.

        Calling prune with no arguments will clear the working memory.
        """
        pass

    def supertypes(working_memory):
        """
        # todo
        """
        pass
