
from structpy import specification
from structpy.graph.directed.labeled.data.multilabeled_digraph_data_spec import MultiLabeledDigraphDataSpec


E = 0.0001

my_values = {'a': 2, 'b': 8, 'c': 3, 'd': 6}

def push(a, b):
    num = (b - a)
    denom = (b - a) ** 2
    bdelta = num / denom
    adelta = 0
    return adelta, bdelta

def pull(a, b):
    pass

@specification
class ScoreGraphSpec:
    """

    """

    @specification.init
    def SCOREGRAPH(ScoreGraph, edges=None, updaters=None, get_fn=None, set_fn=None, default=0):
        """
        Create a ScoreGraph.
        """
        score_graph = ScoreGraph(
            edges=[
            ('a', 'c', 'push'),
            ('b', 'c', 'push'),
            ('c', 'd', 'pull')],
            updaters={
                'push': (lambda x, y: (0, (y - x) / (y - x) ** 2 if y != x else 0)),
                'pull': (lambda x, y: (0, (x - y)))
            },
            get_fn=lambda x: my_values.get(x),
            set_fn=lambda x, y: my_values.__setitem__(x, y)
        )
        return score_graph

    def score(score_graph, node):
        """
        Get the score (float) of a given node.
        """
        assert score_graph.score('a') == 2
        assert score_graph.score('b') == 8

    def update(score_graph, iterations=1, pull=False, push=False):
        """

        """
        score_graph.update()
        c_score = score_graph.score('c')
        assert c_score == 3.8
        score_graph.update(1000, lr=0.1)
        c_score = score_graph.score('c')
        assert 5 - E < c_score < 5 + E

    def push(score_graph):
        """

        """
        score_graph.push()
        assert 5 - E < my_values['c'] < 5 + E
        assert 5 - E < my_values['d'] < 5 + E
        assert my_values['a'] == 2

    def pull(score_graph):
        """

        """
        my_values['d'] = 10
        score_graph.pull()
        assert score_graph.score('d') == 10

    def set_updater(score_graph, label, updater_fn):
        """

        """
        score_graph.set_updater('pull', lambda x, y: (0, 12-y))
        score_graph.update()
        assert score_graph.score('d') == 12