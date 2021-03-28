
from structpy.graph.directed.labeled.multilabeled_digraph_networkx import MultiLabeledDigraphNX as Graph


class MetaGraph(Graph):

    def __init__(self, feature_cls):
        Graph.__init__(self)
        self._features_cls = feature_cls
        self.features = feature_cls()

    def merge(self, concept_a, concept_b):
        out_edges = self.out_edges(concept_b)
        in_edges = self.in_edges(concept_b)
        for s,t,l in out_edges:
            self.add(concept_a, t, l)
        for s,t,l in in_edges:
            self.add(s, concept_a, l)
        if self.has(concept_b):
            Graph.remove(self, concept_b)
        self.features.merge(concept_a, concept_b)

    def update(self, graph=None, features=None, id_map=None):
        if features is not None:
            if id_map is not None:
                features = {id_map[k]: v for k, v in features.items()}
            self.features.update(features)
        if graph is not None:
            for n in graph.nodes():
                self.add(n if id_map is None else id_map[n])
            for s,t,l in graph.edges():
                if id_map is not None:
                    s, t, l = id_map[s], id_map[t], id_map[l]
                self.add(s, t, l)

    def remove(self, node, target=None, label=None):
        Graph.remove(node, target, label)
        if target is None and label is None:
            self.features.remove(node)

    def copy(self):
        mg = MetaGraph(self._features_cls)
        mg.features = self.features.copy()
        for n in self.nodes():
            mg.add(n)
        for s,t,l in self.edges():
            mg.add(s,t,l)
        return mg

    def to_json(self):
        return {
            'features': self.features.to_json(),
            'concepts': list(self.nodes()),
            'edges': [list(e) for e in self.edges()]
        }

    def from_json(self, data, id_map=None):
        mg = MetaGraph(self._features_cls)
        mg.features.from_json(data['features'])
        for c in data['concepts']:
            mg.add(c)
        for s,t,l in data['edges']:
            mg.add(s,t,l)
        self.update(mg, mg.features, id_map)

