
from itertools import chain


rootconcept = object()
rootpredicate = object()


def match(query, variables, kb):
    solutions = []


def priority(concept, predicate, variables, kb=None):
    s, t, o, i = predicate
    if kb is None:
        return 0 if concept not in variables else 1
    elif concept not in variables:
        if concept == s:
            return kb.counts['s'][concept]
        elif concept == t:
            return kb.counts['t'][concept]
        elif concept == o:
            return kb.counts['o'][concept]
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


def create_constraint_list(query, variables, kb=None):
    ctodo = set(query.concepts())
    ptodo = {(s, t, o) for s, t, o, i in query.predicates()}
    constants = {c for c in query.concepts() if c not in variables}
    predicates = set(ptodo)
    while ctodo:
        options = []
        for concept in ctodo:
            for predicate in chain(
                    query.predicates(subject=concept),
                    query.predicates(object=concept),
                    query.predicates(type=concept)
            ):
                if predicate not in ptodo:
                    options.append((concept, predicate))
        constraint = max(options, key=lambda x: priority(*x, variables, kb))

