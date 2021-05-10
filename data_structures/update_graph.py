
from GRIDD.data_structures.update_graph_spec import UpdateGraphSpec

from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph


class UpdateGraph(Graph):

    def __init__(self, edges=None, nodes=None, updaters=None,
                 get_fn=None, set_fn=None, default=None):
        Graph.__init__(self, edges=edges, nodes=list(nodes))
        self.values = {}
        self._get_fn = get_fn
        self._set_fn = set_fn
        self.updaters = {}
        if updaters:
            self.set_updaters(updaters)
        if isinstance(nodes, dict):
            self.set_values(nodes)
        self.default = default
        if get_fn is not None:
            self.pull()

    def update(self, iteration=1, pull=False, push=False):
        if pull: self.pull()
        for i in range(iteration):
            newvalues = {}
            for node, fn in self.updaters.items():
                args = [(self.values.get(s, self.default), l)
                        for s, t, l in self.in_edges(node)]
                newvalues[node] = fn(self.values.get(node, self.default), args)
            self.set_values(newvalues)
        if push: self.push()

    def pull(self):
        if self._get_fn:
            for node in self.nodes():
                self[node] = self._get_fn(node)

    def push(self):
        if self._set_fn:
            for node in self.nodes():
                if node in self.values:
                    self._set_fn(node, self.values[node])

    def set_updaters(self, updaters):
        self.updaters.update(updaters)

    def set_values(self, values):
        self.values.update(values)
        for node in values:
            self.add(node)

    def remove(self, node, target=None, label=None):
        if target is None and label is None:
            self.updaters.pop(node)
        return Graph.remove(self, node, target, label)

    def __getitem__(self, item):
        return self.values[item]

    def __setitem__(self, key, value):
        self.values[key] = value


if __name__ == '__main__':
    print(UpdateGraphSpec.verify(UpdateGraph))
