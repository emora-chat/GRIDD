
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

def op_more_info(cg, i):
    new, _, old, _ = cg.predicate(i)
    pre = cg.metagraph.targets(old, RREF)
    vars = set(cg.metagraph.targets(old, RVAR))
    # add specific()
    i2 = cg.add(new, 'specific')
    pre.add(i2)
    vars.add(i2)
    # add links
    cg.metagraph.add_links(new, pre, REF)
    cg.metagraph.add_links(new, vars, VAR)
    cg.remove(i)

def eturn(cg, i):
    concept, _, turn_pos, _ = cg.predicate(i)
    turn_pos = str(turn_pos)
    rule = cg.metagraph.sources(i, PRE)
    if len(rule) > 0:
        if turn_pos.isdigit():
            new_object = cg.id_map().get()
            p1 = cg.add(new_object, TYPE, 'number')
            p2 = cg.add(concept, ETURN, new_object)
            cg.features[new_object][TURN_POS] = int(turn_pos)
            rule = next(iter(rule))
            for c in [p1, p2, new_object]:
                cg.metagraph.add(rule, c, PRE)
                cg.metagraph.add(rule, c, VAR)
            cg.remove(predicate_id=i)
            cg.remove(OP_ETURN)
            cg.remove(turn_pos)
        else:
            print('[WARNING] an eturn predicate has been found that does not have a numeric object!')

def uturn(cg, i):
    concept, _, turn_pos, _ = cg.predicate(i)
    turn_pos = str(turn_pos)
    rule = cg.metagraph.sources(i, PRE)
    if len(rule) > 0:
        if turn_pos.isdigit():
            new_object = cg.id_map().get()
            p1 = cg.add(new_object, TYPE, 'number')
            p2 = cg.add(concept, UTURN, new_object)
            cg.features[new_object][TURN_POS] = int(turn_pos)
            rule = next(iter(rule))
            for c in [p1, p2, new_object]:
                cg.metagraph.add(rule, c, PRE)
                cg.metagraph.add(rule, c, VAR)
            cg.remove(predicate_id=i)
            cg.remove(OP_UTURN)
            cg.remove(turn_pos)
        else:
            print('[WARNING] a uturn predicate has been found that does not have a numeric object!')
