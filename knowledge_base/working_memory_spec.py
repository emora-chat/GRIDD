
from structpy import specification

from knowledge_base.concept_graph_spec import ConceptGraphSpec


@specification
class WorkingMemorySpec:
    """
    Data structure that organizes a small set of predicates to apply inferences and
    interface with a larger `KnowledgeBase`.
    """

    @specification.satisfies(ConceptGraphSpec)
    def WORKING_MEMORY(WorkingMemory, knowledge_base, *filenames_or_logicstrings):
        """

        """
        pass

    def pull_ontology(working_memory):
        """
        Add all concepts from the `.knowledge_base` that are super-types of concepts
        in working memory.
        """
        pass

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
        pass

    def prune(working_memory, remaining=0, score_function=None):
        """
        Remove concepts from working memory one by one, in order of `score_function(concept)`
        until `remaining` or less concepts remain in working memory.

        Calling prune with no arguments will clear the working memory.
        """
        pass

    def load(working_memory, *filenames_or_logicstrings):
        """

        """
        working_memory.load('example2.kg')
        working_memory.load('')

    def rules(working_memory):
        """
        Find all rules in working memory and return as a list of `(type_id_str, ConceptGraph)` tuples.
        """
        pass

    def implications(working_memory, *types_or_rules):
        """
        Check and return all specified implications on predicates in working memory.

        Providing `str` concept ids will use rules from the pre/post conditions of the
        type with that id.

        Providing `str` file names ending with the `.kg` extension will use rules from
        the .kg file of that name.

        Providing `str` representing a logic string will use rule(s) from that logic string.
        """
        pass


































