
import torch

from GRIDD.data_structures.graph_matching.jagged_tensor import JaggedTensor
from GRIDD.data_structures.graph_matching.hash_tensor import HashTensor
from GRIDD.data_structures.graph_matching.reverse_label import ReverseLabel as Rlabel
from GRIDD.data_structures.graph_matching.root import root, rooted_edge
from GRIDD.data_structures.id_map import IdMap


class GraphTensor:

    def __init__(self, graph, nodemap=None, edgemap=None, device='cpu'):
        self.device = device
        self.nodemap = nodemap or IdMap(namespace=int)
        self.edgemap = edgemap or IdMap(namespace=int)
        nodes = set(graph.nodes())
        edges = set(graph.edges())
        edges.update({(t, s, Rlabel(l)) for s, t, l in edges})
        edges.update({(root, n, rooted_edge) for n in nodes})
        medges = [(self.nodemap.get(s), self.nodemap.get(t), self.edgemap.get(l)) for s, t, l in edges]
        self.ne = len(self.edgemap)
        self.nn = len(self.nodemap)
        dedges = {}
        for s, t, l in medges:
            dedges.setdefault((s * self.ne + l), []).append(t)
        edgehashes = {}
        for s, t, l in medges:
            edgehashes[s * self.nn * self.ne + t * self.ne + l] = 1
        keys = {k: i for i, k in enumerate(dedges.keys())}
        vedges = {keys[k]: ts for k, ts in dedges.items()}
        self._keytensor = HashTensor(keys, device=self.device)
        self._targettensor = JaggedTensor([vedges[i] for i in range(len(vedges))], device=self.device)
        self._edgestensor = HashTensor(edgehashes, device=self.device)
        return

    def __getitem__(self, source_label):
        inodes = self._keytensor[source_label[:, 0] * self.ne + source_label[:, 1]]
        targets, inverse = self._targettensor.map(inodes)
        return targets

    def targets(self, source_label):
        transform = source_label[:,0] * self.ne + source_label[:,1]
        inodes = self._keytensor[transform]
        exists = torch.nonzero(torch.ne(inodes, -1)).squeeze(1)
        inodes = inodes[exists]
        targets, inverse = self._targettensor.map(inodes)
        inverse = exists[inverse]
        return targets, inverse

    def has(self, edges):
        x = self.nn * self.ne
        edgehashes = edges[:,0] * x + edges[:,2] * self.ne + edges[:,1]
        result = self._edgestensor[edgehashes]
        return result > 0


if __name__ == '__main__':
    from structpy.graph.directed.labeled.multilabeled_digraph_networkx import MultiLabeledDigraphNX as Graph

    g = Graph({
        ('john', 'mary', 'likes'),
        ('john', 'tom', 'likes'),
        ('mary', 'john', 'likes')
    })
    gt = GraphTensor(g)

    st = [
        [gt.nodemap.get('john'), gt.edgemap.get('likes')],
        [gt.nodemap.get('tom'), gt.edgemap.get('likes')]
    ]

    targets, inv = gt.targets(torch.tensor(st, dtype=torch.long))

    for i, target in enumerate(targets):
        print(gt.nodemap.identify(st[inv[i].item()][0]),
              '->', gt.nodemap.identify(target.item()) )

    edgetest = torch.tensor([
        [gt.nodemap.get('john'), gt.edgemap.get('likes'), gt.nodemap.get('mary')],
        [gt.nodemap.get('john'), gt.edgemap.get('likes'), gt.nodemap.get('john')],
        [gt.nodemap.get('mary'), gt.edgemap.get('likes'), gt.nodemap.get('tom')]
    ], dtype=torch.long)

    contains = gt.has(edgetest)

    print(contains)





