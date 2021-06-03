
import torch

from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.graph_matching.data_preprocessing import preprocess_data_graph
from GRIDD.data_structures.graph_matching.query_preprocessing import preprocess_query_graph


class GraphMatchingEngine:

    def __init__(self, device='cpu'):
        self.device = device
        self.checklist = [] # list<Tensor<q x 3: (n, l, n)>> list of required next edge lists
        self.n = IdMap()    # nodes (both query and data nodes: static query nodes, dynamic query nodes, data nodes)
        self.v = IdMap(     # var nodes (vars are nodes < 0)
            start_index=-1, next_function=(lambda x: x-1) )
        self.l = IdMap()    # labels
        self.q = IdMap()    # query graphs

    def add_queries(self, *query_graphs):
        self.checklist = self._add_queries(query_graphs)

    def _add_queries(self, query_graphs):
        for query_graph in query_graphs:
            cl = preprocess_query_graph(query_graph)

    def match(self, data_graph, *query_graphs):
        complete = {}                                                               # list<Tensor<n>> completed solutions
        checklist = self._add_queries(query_graphs)                                 # list<Tensor<q x 3: (n, l, n)>> list of required next edge lists
        edges = preprocess_data_graph(data_graph)                                   # JaggedTensor<>
        solutions = torch.LongTensor(list(self.q.values()), device=self.device)     # Tensor<solution x step: n> in-progress solutions (1st entry is query id)
        for req in checklist:                                                       # Tensor<q x 3: (n, l, n)>: required next edge
            pass





