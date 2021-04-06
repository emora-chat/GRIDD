
from GRIDD.utilities.utilities import aliases
from GRIDD.globals import *

@aliases('not')
def _negation(cg, i):
    sub = cg.predicate(i)[0]
    cg.features[sub][CONFIDENCE] = -1.0

def maybe(cg, i):
    sub = cg.predicate(i)[0]
    cg.features[sub][CONFIDENCE] = 0.0

@aliases('assert')
def _assert(cg, i):
    sub = cg.predicate(i)[0]
    cg.features.setdefault(sub, {})[CONFIDENCE] = 1.0
    cg.features[sub][BASE] = True
