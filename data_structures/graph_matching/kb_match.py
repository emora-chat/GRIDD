
from itertools import chain

from GRIDD.globals import *

rootconcept = object()
rootpredicate = object()


def match(query, variables, kb, priorities=True, limit=10, reduction=3):
    solutions = [{}]
    constraints = create_constraint_list(query, variables, kb if priorities else None)
    for center, constraint in constraints:
        new_solutions = []
        for assignments in solutions:
            for satisfaction in satisfactions(constraint, assignments, variables, kb):
                new_solutions.append({**assignments, **satisfaction})
        solutions = new_solutions
        if not solutions:
            break
        if len(solutions) > limit:
            solutions = solutions[:reduction]
    return solutions

def satisfactions(constriant, assignments, variables, kb, branch_limit=10, reduction=1):
    supertypes = kb.compiled_types
    subtypes = kb.compiled_subtypes
    result = []
    constriant = [assignments.get(c, c) for c in constriant]
    s, t, o, i = constriant
    if (s is rootconcept and kb.has(o)) or (i not in variables and kb.has(s, t, o, i)):
        return [{}]
    elif t == TYPE:
        if s in variables and o in variables and i in variables:
            for i, (k, v) in enumerate(kb.compiled_types.values()):
                result.append({s: k, t: t, o: v, i: None})
                if i > branch_limit:
                    return result[:reduction]
        elif s in variables and i in variables:
            for i, st in enumerate(subtypes.get(o, set()) - {o}):
                result.append({s: st, i: None})
                if i > branch_limit:
                    return result[:reduction]
        elif o in variables and i in variables:
            for i, st in enumerate(supertypes.get(s, set()) - {s}):
                result.append({o: st, i: None})
                if i > branch_limit:
                    return result[:reduction]
        elif o in supertypes.get(s, []):
            result.append({i: None})
        else:
            return []
    else:
        sub, typ, obj = [None if x in variables else x for x in (s, t, o)]
        predicates = []
        for num, predicate in enumerate(kb.predicates(sub, typ, obj)):
            predicates.append(predicate)
            if num > branch_limit:
                predicates = predicates[:reduction]
                break
        for sub, typ, obj, ins in predicates:
            assigned = {}
            if s in variables: assigned[s] = sub
            if t in variables: assigned[t] = typ
            if o in variables: assigned[o] = obj
            if i in variables: assigned[i] = ins
            result.append(assigned)
    return result


def create_constraint_list(query, variables, kb=None):
    constraints = []
    ctodo = set(query.concepts())
    ptodo = set(query.predicates())
    visited = set()
    while ctodo:
        options = set()
        for concept in ctodo:
            options.update(expand_options(concept, query, ptodo))
        if options:
            constraint = min(options, key=lambda x: priority(*x, variables, kb))
        else:
            concept = ctodo.pop()
            constraint = (concept, (rootconcept, rootpredicate, concept, None))
        concept, predicate = constraint
        constraints.append(constraint)
        ctodo.difference_update({*predicate})
        ptodo.discard(predicate)
        toexpand = list({*predicate} - {concept, None})
        while toexpand:
            expander = toexpand.pop()
            options = expand_options(expander, query, ptodo)
            visited.add(concept)
            if options:
                constraint = min(options, key=lambda x: priority(*x, variables, kb))
                concept, predicate = constraint
                constraints.append(constraint)
                ctodo.difference_update({*predicate})
                ptodo.discard(predicate)
                toexpand.extend([c for c in predicate if c not in visited and c is not None])
    return constraints


def priority(concept, predicate, variables, kb=None):
    s, t, o, i = predicate
    if kb is None:
        return 0 if concept not in variables else 1
    elif concept not in variables:
        if concept == s:
            return -(1 / (1 + kb.counts['s'][concept]))
        elif concept == t:
            return -(1 / (1 + kb.counts['t'][concept]))
        elif concept == o:
            return -(1 / (1 + kb.counts['o'][concept]))
        elif concept == i:
            return -1
        else:
            raise ValueError
    else:
        if concept == s and o not in variables:
            return 0
        elif concept == o and s not in variables:
            return 0
        elif t not in variables:
            return 1
        else:
            return 2


def expand_options(concept, query, ptodo):
    options = []
    for predicate in chain(
            query.predicates(subject=concept),
            query.predicates(object=concept),
            query.predicates(predicate_type=concept),
            [query.predicate(concept)] if query.has(predicate_id=concept) else []
    ):
        if predicate in ptodo:
            options.append((concept, predicate))
    return options


