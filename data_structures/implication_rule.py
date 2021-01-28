from GRIDD.data_structures.concept_graph import ConceptGraph

class ImplicationRule:
    """
    Data structure for packaging precondition and postcondition ConceptGraphs
    to represent an implication rule.
    """

    def __init__(self, pre, post=None, concept_id=None):
        self.precondition = pre
        if post is None:
            post = ConceptGraph()
        self.postcondition = post
        if concept_id is None:
            concept_id = id(self)
        self.concept_id = concept_id

    def __hash__(self):
        return hash(self.concept_id)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.concept_id == other
        else:
            return self.concept_id == other.concept_id

    def __str__(self):
        return self.concept_id

    def __repr__(self):
        return str(self)