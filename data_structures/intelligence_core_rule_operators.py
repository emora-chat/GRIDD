
from GRIDD.globals import *
from itertools import chain

def _exists(cg, i, aux_state=None):
    sub, _, _, _ = cg.predicate(i)
    for pred in chain(list(cg.predicates(sub, predicate_type='not')), list(cg.predicates(sub, predicate_type='maybe'))):
        cg.remove(*pred)
    if len(set(cg.subtypes_of('not'))) == 1:
        cg.remove('not')
    if len(set(cg.subtypes_of('maybe'))) == 1:
        cg.remove('maybe')