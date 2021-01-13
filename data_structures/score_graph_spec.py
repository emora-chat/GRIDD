
from structpy import specification
from structpy.graph.directed.labeled.data.multilabeled_digraph_data_spec import MultiLabeledDigraphDataSpec


E = 0.001

my_values = {'a': 2, 'b': 8, 'c': 3, 'd': 6}

@specification
class ScoreGraphSpec:
    """

    """

    @specification.init
    def SCOREGRAPH(ScoreGraph, edges=None, updater_dict=None, get_fn=None, set_fn=None, default=0):
        """
        Create a ScoreGraph.
        """
        score_graph = ScoreGraph(
            edges=[
            ('a', 'b', 'push'),
            ('c', 'b', 'push'),
            ('b', 'd', 'pull')],
            updater_dict={
                'push': (lambda x, y: (x, y + (y - x) / (y - x) ** 2 if y != x else y)),
                'pull': (lambda x, y: (x, y - (y - x) / (y - x) ** 2 if y != x else y))
            },
            get_fn=lambda x: my_values.get(x),
            set_fn=lambda x, y: my_values.setdefault(x, y)
        )
        return score_graph

    def update(score_graph, iterations=1, pull=False, push=False):
        """

        """
        score_graph.update()
        assert score_graph.node_data('b', 'value') == None


    def push(score_graph):
        """

        """
        pass

    def pull(score_graph):
        """

        """
        pass

    def set_update_function(score_graph, label, resolution_function):
        """

        """
        pass