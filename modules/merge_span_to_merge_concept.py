
from GRIDD.modules.merge_span_to_merge_concept_spec import MergeSpanToMergeConceptSpec


class MergeSpanToMergeConcept:

    def __call__(self, span_merges, working_memory):
        """
        Calculate node merge scores for pairs of nodes in working_memory
        based on dependency parse merge outputs

        args[0] - span_obj merges based on dependency parse
        args[1] - working memory
        """
        node_merges = []
        for (span1, pos1), (span2, pos2) in span_merges:
            # if no mention for span, no merge possible
            if working_memory.has(span1) and working_memory.has(span2):
                (concept1,) = working_memory.objects(span1, 'ref')
                concept1 = self._follow_path(concept1, pos1, working_memory)
                (concept2,) = working_memory.objects(span2, 'ref')
                concept2 = self._follow_path(concept2, pos2, working_memory)
                node_merges.append((concept1,concept2))
        return node_merges

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        elif pos == 'type':
            return working_memory.type(concept)
        return concept


if __name__ == '__main__':
    print(MergeSpanToMergeConceptSpec.verify(MergeSpanToMergeConcept))