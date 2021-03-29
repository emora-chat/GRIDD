

from GRIDD.utilities.utilities import aliases


@aliases('not')
def _negation(cg, i):
    sub = cg.predicate(i)[0]
    cg.features[sub]['c'] = -1.0

def maybe(cg, i):
    sub = cg.predicate(i)[0]
    cg.features[sub]['c'] = 0.0