
from structpy import specification
from os.path import join


@specification
class KnowledgeBaseSpec:
    """
    Data structure for creating, editing, and querying a Knowledge Graph as part of the
    GRIDD Framework.

    Nodes in the knowledge graph are accessed by a string identifier, which is provided
    by the user upon adding the node (although some nodes are automatically generated and
    assigned a string ID).
    """

    @specification.init
    def KNOWLEDGE_BASE(KnowledgeBase, filenames, namespace='KB'):
        """
        Create a `KnowledgeBase` object.

        Providing `filenames` will load a text file from a previous `data_structures.save` operation.
        """
        knowledge_base = KnowledgeBase()
        return knowledge_base

    def load(knowledge_base, filenames_or_logicstrings):
        """
        Load knowledge from files, folders of .kb files, logic strings, or KnowledgeBase objects.
        """
        knowledge_base.load(join('GRIDD', 'resources', 'kg_files', 'example.kg'))

        assert knowledge_base.has('avengers', 'type', 'movie')
        assert knowledge_base.has('"endgame"', 'expr', 'avengers')
        assert knowledge_base.has('emora', 'like', 'avengers')
        ela = knowledge_base.predicates('emora', 'like', 'avengers')[0][3]
        elc = knowledge_base.predicates('emora', 'like', 'chris_evans')[0][3]
        assert knowledge_base.has(ela, 'reason', elc)
        assert knowledge_base.has(ela, 'time', 'now')
        sn = knowledge_base.predicates('now', 'sad', None)[0][3]
        assert knowledge_base.has('love_triangle', 'post', sn)

    def subtypes(knowledge_base, concept):
        """
        Return the set of all subtypes of the provided concept (by id).
        """
        assert knowledge_base.subtypes('buyable') == {'movie', 'avengers'}

    def supertypes(knowledge_base, concept):
        """
        Return the set of all supertypes of the provided concept (by id).
        """
        assert knowledge_base.supertypes('avengers') == {'movie', 'watchable', 'buyable', 'entity', 'object'}












