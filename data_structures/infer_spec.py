from structpy import specification
from data_structures.knowledge_base import KnowledgeBase
from data_structures.infer import ImplicationRule

@specification
class InferSpec:

    @specification.init
    def INFER(infer, knowledge_graph, inference_rules):
        """
        Get variable assignments of solutions from applying each query graph value from the
        `inference rules` dict on the `knowledge_graph`
        :returns dict<rule_id: list of solutions (variable assignments as dictionary)>
        """
        pass
