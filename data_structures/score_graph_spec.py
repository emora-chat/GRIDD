
from structpy import specification
from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.graph.directed.labeled.multilabeled_digraph_networkx import MultiLabeledDigraphNX


@specification
class ScoreGraphSpec:
    """

    """

    @specification.init
    def SCOREGRAPH(ScoreGraph, edges=None, get_function=None, set_function=None):
        """
        Create a ScoreGraph
        """
        graph = MultiLabeledParallelDigraphNX([

        ])
        score_graph = ScoreGraph(graph)
        return score_graph

    def add_edge_type(self, label, resolution_function):
        """

        """
        pass