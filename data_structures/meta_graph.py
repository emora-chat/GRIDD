
from structpy.graph.directed.labeled.multilabeled_digraph_networkx import MultiLabeledDigraphNX as Graph

class MetaGraph(Graph):

    def __init__(self, feature_cls, cg, supports=None):
        Graph.__init__(self)
        self._features_cls = feature_cls
        self.features = feature_cls()
        self.concept_graph = cg
        if supports is None:
            self._supports = {}
        else:
            self._supports = supports

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

    def update(self, graph=None, features=None, id_map=None, concepts=None):
        if features is not None:
            if id_map is not None:
                features = {id_map[k]: v for k, v in features.items() if concepts is None or k in concepts}
                self.features.update(features)
            else:
                self.features.update({k:v for k,v in features.items() if concepts is None or k in concepts})
        if graph is not None:
            for n in graph.nodes():
                if concepts is None or n in concepts:
                    self.add(n if id_map is None else id_map[n])
            for s,t,l in graph.edges():
                if id_map is not None:
                    s, t, l = id_map[s], id_map[t], l
                if concepts is None or s in concepts:
                    self.add(s, t, l)

    def remove(self, node, target=None, label=None):
        if target is None and label is None:
            self.features.remove(node)
            self._remove_supports(node)
        Graph.remove(self, node, target, label)

    def discard(self, node, target=None, label=None):
        if target is None and label is None:
            self.features.discard(node)
            if Graph.has(self, node):
                self._remove_supports(node)
        if Graph.has(self, node, target, label):
            Graph.remove(self, node, target, label)

    def _remove_supports(self, node):
        for label, reverse in self._supports.items():
            if reverse:
                collection = self.sources(node, label)
            else:
                collection = self.targets(node, label)
            for target in collection:
                if not self.concept_graph.has(target):
                    self.remove(target)

    def copy(self, cg):
        mg = MetaGraph(self._features_cls, cg)
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

