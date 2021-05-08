"""
Identifies all spans that are reference constraints on the reference node, based on the parse-to-logic
rule that was matched.

The reference node is not considered a constraint on itself.
"""

import os

DP_LABELS = [x.strip()
             for x in open(os.path.join('GRIDD', 'resources', 'elit_dp_labels.txt'), 'r').readlines()
             if len(x.strip()) > 0]

NOT_CONSTRAINTS = {'voc', 'disc'}

CONSTRAINTS = set(DP_LABELS) - NOT_CONSTRAINTS

def subtree_dependencies(ref_span_node, cg):
    frontier = [ref_span_node]
    subtree = set()
    while len(frontier) > 0:
        node = frontier.pop(0)
        for s,t,o,i in cg.predicates(node):
            if t in CONSTRAINTS:
                frontier.append(o)
                subtree.add(o)
    return list(subtree)

def all_connected_dependencies(ref_span_node, cg):
    frontier = [ref_span_node]
    connections = set()
    while len(frontier) > 0:
        node = frontier.pop(0)
        for s,t,o,i in cg.predicates(node):
            if t in CONSTRAINTS and o not in connections:
                frontier.append(o)
                connections.add(o)
        for s,t,o,i in cg.predicates(object=node):
            if t in CONSTRAINTS and s not in connections:
                frontier.append(s)
                connections.add(s)
    return list(connections - {ref_span_node})

def parent_subtree_dependencies(ref_span_node, cg):
    parent_node = None
    for s, t, o, i in cg.predicates(object=ref_span_node):
        if t in CONSTRAINTS:
            parent_node = s
            break
    if parent_node:
        return list(set(subtree_dependencies(parent_node, cg) + [parent_node]) - {ref_span_node})
    return []

REFERENCES_BY_RULE = {
    'obj_of_possessive': subtree_dependencies,
    'ref_concept_determiner': subtree_dependencies,
    'q_sbj_copula_past': subtree_dependencies,
    'q_sbj_copula_present': subtree_dependencies,
    'q_aux_past': parent_subtree_dependencies,
    'q_aux_present': parent_subtree_dependencies,
    'q_aux_have': parent_subtree_dependencies,
    'q_modal': parent_subtree_dependencies,
    'q_aux_det': parent_subtree_dependencies,
    'q_det': parent_subtree_dependencies,
    'obj_question': parent_subtree_dependencies,
    'sbj_question': parent_subtree_dependencies,
    'dat_question': parent_subtree_dependencies,
    'qdet_copula_present': subtree_dependencies,
    'qdet_copula_past': subtree_dependencies,
    'qw_copula_present': subtree_dependencies,
    'qw_copula_past': subtree_dependencies,
    'q_aux_adv': parent_subtree_dependencies,
    'q_adv': parent_subtree_dependencies
}

QUESTION_INST_REF = {'q_aux_past', 'q_aux_present', 'q_aux_have'}
