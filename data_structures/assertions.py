from GRIDD.globals import *

def assertions(cg, default=1.0):
    """
    Set confidence of predicates to `default` if they don't already
    have a confidence AND they are not an argument of a NONASSERT.
    """
    types = cg.types()
    predicates = set()
    not_asserted = set()
    for s, _, o, pred in cg.predicates():
        if CONFIDENCE not in cg.features.get(pred, {}):
            predicates.add(pred)
        if NONASSERT in types[pred]:
            if cg.has(predicate_id=s):
                not_asserted.add(s)
            if cg.has(predicate_id=o):
                not_asserted.add(o)
    for a in predicates - not_asserted:
        cg.features.setdefault(a, {})[BASE_CONFIDENCE] = default
    for na in predicates & not_asserted:
        cg.features.setdefault(na, {})[BASE_CONFIDENCE] = 0.0