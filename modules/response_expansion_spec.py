from structpy import specification
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.knowledge_base import KnowledgeBase

@specification
class ResponseExpansionSpec:
    """

    """

    @specification.init
    def RESPONSEEXPANSION(ResponseExpansion):
        response_expansion = ResponseExpansion()
        return response_expansion

    def __call__(response_expansion, main_predicate, working_memory):
        """
        Get all supporting predicates for selected main predicate response
        """
        pass


