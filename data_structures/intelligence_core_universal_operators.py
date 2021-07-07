
from GRIDD.globals import *
from itertools import chain

def affirm(cg, i, aux_state=None):
    _, _, sub, _ = cg.predicate(i)
    if sub is not None:
        for pred in chain(list(cg.predicates(sub, 'not')), list(cg.predicates(sub, 'maybe'))):
            cg.remove(*pred)

def reject(cg, i, aux_state=None):
    _, _, sub, _ = cg.predicate(i)
    if sub is not None:
        for pred in list(cg.predicates(sub, 'maybe')):
            cg.remove(*pred)
        if not cg.has(sub, 'not'):
            cg.add(sub, 'not')

def _exists(cg, i, aux_state=None):
    sub, _, _, _ = cg.predicate(i)
    for pred in chain(list(cg.predicates(sub, predicate_type='not')), list(cg.predicates(sub, predicate_type='maybe'))):
        cg.remove(*pred)
    if len(set(cg.subtypes_of('not'))) == 1:
        cg.remove('not')
    if len(set(cg.subtypes_of('maybe'))) == 1:
        cg.remove('maybe')

def eturn(cg, i, aux_state=None):
    concept, _, turn_pos, _ = cg.predicate(i)
    turn_pos = str(turn_pos)
    if turn_pos.isdigit():
        cg.features[concept].setdefault(ETURN_POS, set()).add(int(turn_pos))
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
        cg.features[concept].setdefault(UTURN_POS, set()).add(int(turn_pos))
        if len(list(cg.predicates(predicate_type=OP_UTURN))) == 1:
            cg.remove(OP_UTURN)
        if len(list(chain(cg.subjects(turn_pos), cg.objects(turn_pos)))) == 1:
            cg.remove(turn_pos)
        cg.remove(predicate_id=i)
    else:
        print('[WARNING] eturn predicate has been found that does not have a numeric object!')
