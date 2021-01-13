
from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX as Graph


class ScoreGraph(Graph):

    def __init__(self, edges=None, updater_dict=None, get_fn=None, set_fn=None, default=0):
        Graph.__init__(self, edges=edges)


