
from structpy import specification

from data_structures.concept_graph_spec import ConceptGraphSpec


@specification
class KnowledgeBaseSpec:
    """
    Data structure for creating, editing, and querying a Knowledge Graph as part of the
    GRIDD Framework.

    Nodes in the knowledge graph are accessed by a string identifier, which is provided
    by the user upon adding the node (although some nodes are automatically generated and
    assigned a string ID).
    """

    @specification.satisfies(ConceptGraphSpec.CONCEPT_GRAPH)
    def KNOWLEDGE_BASE(KnowledgeBase, *filenames):
        """
        Create a `KnowledgeBase` object.

        Providing `filenames` will load a text file from a previous `data_structures.save` operation.
        """
        knowledge_base = KnowledgeBase('example.kg')
        return knowledge_base

    def load(knowledge_base, *filenames_or_logicstrings):
        """

        """
        knowledge_base.load('example2.kg')
        knowledge_base.load('')

    def subtypes(knowledge_base, concept):
        """
        Return the set of all subtypes of the provided concept (by id).
        """
        pass

    def supertypes(knowledge_base, concept):
        """
        Return the set of all supertypes of the provided concept (by id).
        """
        pass











