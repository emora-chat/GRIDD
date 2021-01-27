
from structpy import specification

from data_structures.concept_graph import ConceptGraph


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
        working_memory = ConceptGraph(
            predicates=[
                ('X', 'likes', 'Y', 'xly'),
                ('"likes"', 'exprof', 'xly'),
                ('"user"', 'exprof', 'user'),
                ('"avengers"', 'exprof', 'avengers')
            ]
        )

        span_merges = [
            (('"user"', 'center'), ('"likes"', 'subject')),
            (('"avengers"', 'center'), ('"likes"', 'object'))
        ]

        concept_merges = mstmc(span_merges, working_memory)

        assert set(concept_merges) == {('user', 'X'), ('avengers', 'Y')}

