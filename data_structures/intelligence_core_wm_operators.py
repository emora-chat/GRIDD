
from GRIDD.globals import *

def op_more_info(cg, i, aux_state=None):
    new, _, old, _ = cg.predicate(i)
    pre = cg.metagraph.targets(old, RREF)
    vars = set(cg.metagraph.targets(old, RVAR))
    # add specific()
    i2 = cg.add(new, '_specific')
    pre.add(i2)
    vars.add(i2)
    # add links
    cg.metagraph.add_links(new, pre, REF)
    cg.metagraph.add_links(new, vars, VAR)
    cg.remove(i)


def rfallback(cg, i, aux_state=None):
    s, t, o, i = cg.predicate(i)
    cg.remove(s, t, o, i)
    if aux_state is None:
        print('[WARNING] No aux_state parameter was passed to rfallback operator')
        return
    if 'fallbacks' not in aux_state:
        aux_state['fallbacks'] = []
    if s not in aux_state['fallbacks']:
        aux_state['fallbacks'].append(s)