
from GRIDD.utilities.utilities import aliases
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *

@aliases('not')
def _negation(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = -1.0

def maybe(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = 0.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = 0.0

@aliases('assert')
def _assert(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = 1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = 1.0

    # wrt, t, sub, i = cg.predicate(i)
    # if cg.has(predicate_id=sub):
    #     if wrt == 'user':
    #         if BASE_UCONFIDENCE not in cg.features.get(sub, {}):
    #             assertions(cg, [cg.predicate(sub)], conf=UCONFIDENCE, bconf=BASE_UCONFIDENCE)
    #     elif wrt == 'emora':
    #         if BASE_CONFIDENCE not in cg.features.get(sub, {}):
    #             assertions(cg, [cg.predicate(sub)], conf=CONFIDENCE, bconf=BASE_CONFIDENCE)

def affirm(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = 1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = 1.0

def reject(cg, i):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = -1.0
