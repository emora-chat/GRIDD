
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
        dedges = {}
        for s, t, l in medges:
            dedges.setdefault((s * self.ne + l), []).append(t)
        keys = {k: i for i, k in enumerate(dedges.keys())}
        vedges = {keys[k]: ts for k, ts in dedges.items()}
        self._keytensor = HashTensor(keys, device=self.device)
        self._edgetensor = JaggedTensor([vedges[i] for i in range(len(vedges))], device=self.device)

    def __getitem__(self, source_label):
        inodes = self._keytensor[source_label[:,0] * self.ne + source_label[:,1]]
        targets, inverse = self._edgetensor.map(inodes)
        return targets

    def map(self, source_label):
        transform = source_label[:,0] * self.ne + source_label[:,1]
        inodes = self._keytensor[transform]
        exists = torch.nonzero(torch.ne(inodes, -1)).squeeze(1)
        inodes = inodes[exists]
        targets, inverse = self._edgetensor.map(inodes)
        inverse = exists[inverse]
        return targets, inverse


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

    targets, inv = gt.map(torch.tensor(st, dtype=torch.long))

    for i, target in enumerate(targets):
        print(gt.nodemap.identify(st[inv[i].item()][0]),
              '->', gt.nodemap.identify(target.item()) )





