from GRIDD.globals import *

def assertions(cg, consider=None, default=1.0, conf=CONFIDENCE, bconf=BASE_CONFIDENCE):
    """
    Set confidence of predicates to `default` if they don't already
    have a confidence AND they are not an argument of a NONASSERT.
    """
    types = cg.types()
    predicates = set()
    not_asserted = set()
    if consider is None:
        consider = cg.predicates()
    for s, _, o, pred in consider:
        if conf not in cg.features.get(pred, {}):
            predicates.add(pred)
        if NONASSERT in types[pred]:
            if cg.has(predicate_id=s):
                not_asserted.add(s)
            if cg.has(predicate_id=o):
                not_asserted.add(o)
    for a in predicates - not_asserted:
        cg.features.setdefault(a, {})[bconf] = default
    for na in predicates & not_asserted:
        cg.features.setdefault(na, {})[bconf] = 0.0