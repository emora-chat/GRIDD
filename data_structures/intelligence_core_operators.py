
from GRIDD.utilities.utilities import aliases
from GRIDD.globals import *

@aliases('not')
def _negation(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][CONFIDENCE] = -1.0

def maybe(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][UCONFIDENCE] = 0.0
    elif wrt == 'emora':
        cg.features[sub][CONFIDENCE] = 0.0

@aliases('assert')
def _assert(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    cg.features[sub][UCONFIDENCE] = 1.0
    cg.features[sub][CONFIDENCE] = 1.0
    cg.features[sub][BASE] = True

def affirm(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][UCONFIDENCE] = 1.0
    elif wrt == 'emora':
        cg.features[sub][CONFIDENCE] = 1.0
    cg.features[sub][BASE] = True

def reject(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][CONFIDENCE] = -1.0
    cg.features[sub][BASE] = True
