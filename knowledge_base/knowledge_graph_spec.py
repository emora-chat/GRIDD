
from structpy import specification

@specification
class KnowledgeGraph:
    """
    Data structure for creating, editing, and querying a Knowledge Graph as part of the
    GRIDD Framework.

    Nodes in the knowledge graph are accessed by a string identifier, which is provided
    by the user upon adding the node (although some nodes are automatically generated and
    assigned an integer ID).
    """

    def KNOWLEDGE_GRAPH(KnowledgeGraph, filename=None, nodes=None):
        """
        Create a `KnowledgeGraph` object.

        Providing a `file_name` will load a text file from a previous `knowledge_base.save` operation.

        Providing a `nodes` list will initialize those nodes.
        """
        knowledge_graph = KnowledgeGraph('example.kg')
        return knowledge_graph

    def properties(kg, concept):
        """

        """
        pass

    def types(kg, concept):
        """

        """
        pass

    def subtypes(kg, concept):
        """

        """
        pass

    def instances(kg, type_):
        """

        """
        pass

    def implication_rules(kg, type_):
        """

        """
        pass

    def save(kg, json_filename):
        """

        """
        pass




