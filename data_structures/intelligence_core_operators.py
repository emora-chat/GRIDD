
from GRIDD.utilities.utilities import aliases
from GRIDD.data_structures.assertions import assertions
from GRIDD.globals import *
from itertools import chain

@aliases('not')
def _negation(cg, i, aux_state=None):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = -1.0

def maybe(cg, i, aux_state=None):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = 0.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = 0.0

@aliases('assert')
def _assert(cg, i, aux_state=None):
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

def affirm(cg, i, aux_state=None):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = 1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = 1.0

def reject(cg, i, aux_state=None):
    wrt, _, sub, _ = cg.predicate(i)
    if wrt == 'user':
        cg.features[sub][BASE_UCONFIDENCE] = -1.0
    elif wrt == 'emora':
        cg.features[sub][BASE_CONFIDENCE] = -1.0

def op_more_info(cg, i, aux_state=None):
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

def eturn(cg, i, aux_state=None):
    concept, _, turn_pos, _ = cg.predicate(i)
    turn_pos = str(turn_pos)
    if turn_pos.isdigit():
        cg.features[concept].setdefault(ETURN_POS, []).append(int(turn_pos))
        if len(list(cg.predicates(predicate_type=OP_ETURN))) == 1:
            cg.remove(OP_ETURN)
        if len(list(chain(cg.subjects(turn_pos), cg.objects(turn_pos)))) == 1:
            cg.remove(turn_pos)
        cg.remove(predicate_id=i)
    else:
        print('[WARNING] eturn predicate has been found that does not have a numeric object!')

def uturn(cg, i, aux_state=None):
    concept, _, turn_pos, _ = cg.predicate(i)
    turn_pos = str(turn_pos)
    if turn_pos.isdigit():
        cg.features[concept].setdefault(UTURN_POS, []).append(int(turn_pos))
        if len(list(cg.predicates(predicate_type=OP_UTURN))) == 1:
            cg.remove(OP_UTURN)
        if len(list(chain(cg.subjects(turn_pos), cg.objects(turn_pos)))) == 1:
            cg.remove(turn_pos)
        cg.remove(predicate_id=i)
    else:
        print('[WARNING] eturn predicate has been found that does not have a numeric object!')

def rfallback(cg, i, aux_state=None):
    s,t,o,i = cg.predicate(i)
    cg.remove(s,t,o,i)
    if aux_state is None:
        print('[WARNING] No aux_state parameter was passed to rfallback operator')
        return
    if 'fallbacks' not in aux_state:
        aux_state['fallbacks'] = []
    if s not in aux_state['fallbacks']:
        aux_state['fallbacks'].append(s)
