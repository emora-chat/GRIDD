
from GRIDD.data_structures.score_graph_spec import ScoreGraphSpec
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph
from collections import defaultdict


class ScoreGraph(Graph):

    def __init__(self, edges=None, updaters=None, get_fn=None, set_fn=None, default=0):
        Graph.__init__(self, edges=edges)
        self._get_fn = get_fn
        self._set_fn = set_fn
        self.updaters = {}
        if updaters is not None:
            for label, updater in updaters.items():
                self.set_updater(label, updater)
        self._default = float(default)
        if self._get_fn is not None:
            for node in self.nodes():
                self.data(node).score = self._get_fn(node)
        else:
            for node in self.nodes():
                self.data(node).score = 0

    def score(self, node):
        return self.data(node).score

    def push(self):
        for node in self.nodes():
            self._set_fn(node, self.data(node).score)

    def pull(self):
        for node in self.nodes():
            self.data(node).score = self._get_fn(node)

    def update(self, iterations=1, pull=False, push=False, lr=1):
        if pull:
            self.pull()
        for i in range(iterations):
            deltas = defaultdict(float)
            for s, t, l in self.edges():
                if l in self.updaters:
                    s_delta, t_delta = self.updaters[l](self.score(s), self.score(t))
                    deltas[s] += s_delta * lr
                    deltas[t] += t_delta * lr
            for node, delta in deltas.items():
                self.data(node).score += delta
        if push:
            self.push()

    def set_updater(self, label, updater_fn):
        self.updaters[label] = updater_fn


if __name__ == '__main__':
    print(ScoreGraphSpec.verify(ScoreGraph))
