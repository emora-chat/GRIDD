import os

DP_LABELS = [x.strip()
             for x in open(os.path.join('GRIDD', 'resources', 'elit_dp_labels.txt'), 'r').readlines()
             if len(x.strip()) > 0]

def alignment_ref(ref_span_node, cg):
    frontier = [ref_span_node]
    subtree = set()
    while len(frontier) > 0:
        node = frontier.pop(0)
        for s,t,o,i in cg.predicates(node):
            if t in DP_LABELS:
                frontier.append(o)
                subtree.add(o)
    return list(subtree)

REFERENCES_BY_RULE = {
    'obj_of_possessive': alignment_ref,
    'ref_concept_determiner': alignment_ref,
    'ref_determiner': alignment_ref
}
