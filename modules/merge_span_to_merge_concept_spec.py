
from structpy import specification

from GRIDD.data_structures.concept_graph import ConceptGraph


@specification
class MergeSpanToMergeConceptSpec:

    @specification.init
    def MERGE_SPAN_TO_MERGE_CONCEPT(MergeSpanToMergeConcept):
        return MergeSpanToMergeConcept()

    def call(mstmc):
        """
        Calculate node merge scores for pairs of nodes in working_memory
        based on dependency parse merge outputs

        args[0] - span merges based on dependency parse
        args[1] - span dict
        args[2] - working memory
        """
        wm = ConceptGraph(
            predicates=[
                ('X', 'likes', 'Y'),
                ('')
            ]
        )

        merges = [

        ]

