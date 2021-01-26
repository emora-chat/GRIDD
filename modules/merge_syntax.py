
class MergeSyntax:

    def __call__(self, span_merges, span_dict, working_memory):
        """
        Calculate node merge scores for pairs of nodes in working_memory
        based on dependency parse merge outputs

        args[0] - span merge scores based on dependency parse
        args[1] - span dict
        args[2] - working memory
        """
        node_merges = []
        for (spanobj1, pos1), (spanobj2, pos2) in span_merges:
            span1 = span_dict[spanobj1]
            span2 = span_dict[spanobj2]
            (concept1,) = working_memory.objects(span1, 'exprof')
            concept1 = self._follow_path(concept1, pos1, working_memory)
            (concept2,) = working_memory.objects(span2, 'exprof')
            concept2 = self._follow_path(concept2, pos2, working_memory)
            node_merges.append((concept1,concept2))
        return node_merges

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        return concept