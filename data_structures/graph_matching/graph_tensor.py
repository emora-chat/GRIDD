
import torch

from GRIDD.data_structures.graph_matching.jagged_tensor import JaggedTensor
from GRIDD.data_structures.graph_matching.hash_tensor import HashTensor
from GRIDD.data_structures.graph_matching.reverse_label import ReverseLabel as Rlabel
from GRIDD.data_structures.graph_matching.root import root, rooted_edge
from GRIDD.data_structures.id_map import IdMap



class GraphTensor:

    def __init__(self, graph, nodemap=None, edgemap=None):
        nodemap = nodemap or IdMap(namespace=int)
        edgemap = edgemap or IdMap(namespace=int)
        nodes = set(graph.nodes())
        edges = set(graph.edges())
        edges.update({(t, s, Rlabel(l)) for s, t, l in edges})
        edges.update({(root, n, rooted_edge) for n in nodes})
        medges = [(nodemap.get(s), nodemap.get(t), edgemap.get(l)) for s, t, l in edges]
        self.ne = len(edgemap)
        dedges = {}
        for s, t, l in medges:
            dedges.setdefault((s * self.ne + l), []).append(t)
        keys = {k: i for i, k in enumerate(dedges.keys())}
        vedges = {keys[k]: ts for k, ts in dedges.items()}
        self._keytensor = HashTensor(keys)
        self._edgetensor = JaggedTensor([vedges[i] for i in range(len(vedges))])

    def __getitem__(self, source_label):
        inodes = self._keytensor[source_label[:,0] * self.ne + source_label[:,1]]
        targets, inverse = self._edgetensor.map(inodes)
        return targets

    def map(self, source_label):
        inodes = self._keytensor[source_label[:, 0] * self.ne + source_label[:, 1]]
        targets, inverse = self._edgetensor.map(inodes)
        return targets, inverse


