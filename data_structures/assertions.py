from GRIDD.globals import *

def assertions(cg, consider=None):
    """
    Arguments of a NONASSERT are set to uncertain confidence with `maybe`
    """
    types = cg.types()
    predicates = set()
    not_asserted = set()
    if consider is None:
        consider = cg.predicates()
    for s, _, o, pred in consider:
        if not cg.has(pred, 'not'): # only update predicates whose confidence is not specified
            predicates.add(pred)
        if NONASSERT in types[pred]:
            if cg.has(predicate_id=s):
                not_asserted.add(s)
            if cg.has(predicate_id=o):
                not_asserted.add(o)
    for na in predicates & not_asserted:
        i = cg.add(na, 'maybe')
        # if na is part of a rule, then need to add the `maybe` instance so that it can be properly extracted into pre/post-graphs
        pre_sources = cg.metagraph.sources(na, PRE)
        for s in pre_sources:
            cg.metagraph.add(s, i, PRE)
            cg.metagraph.add(s, i, VAR)
        post_sources = cg.metagraph.sources(na, POST)
        for s in post_sources:
            cg.metagraph.add(s, i, POST)
            if not cg.metagraph.has(s, i, VAR):
                cg.metagraph.add(s, i, VAR)