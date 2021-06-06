
import torch

from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.graph_matching.graph_tensor import GraphTensor
from GRIDD.data_structures.graph_matching.preprocess_query_graph import preprocess_query_graph
from GRIDD.utilities.utilities import TensorDisplay as Display
from GRIDD.data_structures.graph_matching.root import root


class GraphMatchingEngine:

    def __init__(self, device='cpu'):
        self.device = device
        self.checklist = []             # list<Tensor<q x 3: (n, l, n)>> list of required next edge lists
        self.querylist = []             # list<Tensor<q: query>> list of queries corresponding to checklist requirements
        self.n = IdMap(namespace=int)   # nodes (both query and data nodes: static query nodes, dynamic query nodes, data nodes)
        self.v = IdMap(namespace=int,   # var nodes (vars are nodes < 0)
            start_index=-1, next_function=(lambda x: x-1) )
        self.l = IdMap(namespace=int)   # labels
        self.q = IdMap(namespace=int)   # query graphs

    def add_queries(self, *query_graphs):
        self.checklist = self._add_queries(query_graphs)

    def _add_queries(self, query_graphs):
        querylist = []
        checklist = []
        for query_graph in query_graphs:
            cl = preprocess_query_graph(query_graph, self.n, self.v, self.l)
            for i, req in enumerate(cl):
                while len(checklist) <= i:
                    checklist.append([])
                    querylist.append([])
                checklist[i].append(req)
                querylist[i].append(self.q.get(query_graph))
        checklist = [torch.LongTensor(req) for req in checklist]
        querylist = [torch.LongTensor(query) for query in querylist]
        combined_cl = []
        combined_ql = []
        acl, aql = (self.checklist, self.querylist)
        bcl, bql = (checklist, querylist)
        for i, aclr in enumerate(acl[:len(bcl)]):
            aclq = aql[i]
            bclr = bcl[i]
            bclq = bql[i]
            combined_cl.append(torch.cat((aclr, bclr), 0))
            combined_ql.append(torch.cat((aclq, bclq), 0))
        for i, aclr in enumerate(acl[len(bcl):]):
            i += len(bcl)
            aclq = aql[i]
            combined_cl.append(aclr)
            combined_ql.append(aclq)
        for i, bclr in enumerate(bcl[len(acl):]):
            i += len(acl)
            bclq = bql[i]
            combined_cl.append(bclr)
            combined_ql.append(bclq)
        return combined_cl, combined_ql

    def match(self, data_graph, *query_graphs):
        display = Display()
        complete = []                                                       # list<Tensor<steps: ((qn1, dn1), (qn2, dn2), ...)>> completed solutions
        checklist, querylist = self._add_queries(query_graphs)              # list<Tensor<query x 3: (s, l, t)>> list of required next edge lists
        edges = GraphTensor(data_graph, self.n, self.l)                     # GraphTensor<Tensor<X x 2: (s, l)>) -> (Tensor<Y: t>, Tensor<Y: inverse_index>>
        solutions = torch.full((len(querylist[0]), 2), self.n.get(root),    # Tensor<solution x step: ((qn1, dn1), (qn2, dn2), ...)> in-progress solutions
                               dtype=torch.long, device=self.device)
        queries = torch.arange(0, len(querylist[0]),                        # Tensor<solution: query> inverse indices for solutions and checklist requirements
                               dtype=torch.long, device=self.device)
        for req in checklist:                                               # Tensor<query x 3: (s, l, t)>: required next edges

            display(req, self.n, self.l, self.n, label='Requirements')

            # get assignments
            hi = torch.nonzero(torch.eq(req[queries], solutions[:,::2]))
            hi = torch.cat([hi[:,0:1], (hi[:,1:2] + 1)], 1)
            ei = hi[:,0]
            ev = solutions[hi]
            expander = torch.full(solutions.size(), -1, device=self.device)
            expander[ei] = ev

            # expand solutions
            t, inv = edges.map(expander)
            r = req[queries][inv][:,2]
            isvar = r < 0
            match = torch.logical_or(isvar, torch.eq(r, t))
            m = torch.nonzero(match)
            solutions = torch.cat([solutions[inv][m], req[queries][inv][m][:,2], t[m]], 1)

            # CHECK AND PUBLISH FULL SOLUTIONS (???)



if __name__ == '__main__':
    from GRIDD.data_structures.graph_matching.graph_matching_engine_spec import GraphMatchingEngineSpec as Spec
    print(Spec.verify(GraphMatchingEngine))




