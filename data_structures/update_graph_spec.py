
from structpy import specification

@specification
class UpdateGraphSpec:

    @specification.init
    def UPDATE_GRAPH(UpdateGraph, edges=None, nodes=None, updaters=None,
                     get_fn=None, set_fn=None, default=None):
        graph = UpdateGraph(
            [
                ('a', 'd', '+'),
                ('b', 'd', '+'),
                ('c', 'd', '-'),
                ('d', 'f', '+'),
                ('e', 'f', '-')
            ],
            nodes={
                'a': 4,
                'b': 8,
                'c': 2,
                'd': 3,
                'e': 5
            },
            updaters={
                'd': (lambda x: sum([e if v=='+' else -e for e, v in x]) / len(x)),
                'f': (lambda y: sum([e for e, v in y if v=='+']))
            },
            default=0
        )

        graph.update()
        assert graph['d'] == 10 / 3
        assert graph['f'] == 3