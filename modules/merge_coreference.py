
from GRIDD.modules.merge_coreference_spec import MergeCoreferenceSpec

from GRIDD.modules.merge_span_to_merge_concept import MergeSpanToMergeConcept
merge_span_to_merge_concept = MergeSpanToMergeConcept()



class MergeCoreference:

    def __call__(self, coref_output, working_memory):
        """
        Output: List of pairs of nodes to merge in working memory based on coref model.

        todo - if one mention is poss DP, merge subject with self of other; otherwise, merge selves
        """
        span_merges = []
        global_tokens = coref_output['global_tokens']
        clusters = coref_output['clusters']
        for cluster in clusters:
            for i, s1 in enumerate(cluster):
                for j, s2 in enumerate(cluster[i+1:]):
                    x1, y1 = s1
                    x2, y2 = s2
                    e1 = global_tokens[y1-1]
                    e2 = global_tokens[y2-1]
                    span_merges.append(((e1, 'self'), (e2, 'self')))
        node_merges = merge_span_to_merge_concept(span_merges, working_memory)
        return node_merges


if __name__ == '__main__':
    print(MergeCoreferenceSpec.verify(MergeCoreference))