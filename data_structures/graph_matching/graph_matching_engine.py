
import torch

from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.graph_matching.graph_tensor import GraphTensor
from GRIDD.data_structures.graph_matching.preprocess_query_graph import preprocess_query_graphs, preprocess_query_tuples
from GRIDD.utilities.utilities import TensorDisplay as Display
from GRIDD.data_structures.graph_matching.root import root

DISPLAY = True

class GraphMatchingEngine:

    def __init__(self, *query_graphs, device='cpu'):
        self.device = device
        self.checklist = []             # list<Tensor<q x 3: (n, l, n)>> list of required next edge lists
        self.querylist = []             # list<Tensor<q: query>> list of queries corresponding to checklist requirements
        self.n = IdMap(namespace=int)   # nodes (both query and data nodes: static query nodes, dynamic query nodes, data nodes)
        self.v = IdMap(namespace=int,   # var nodes (vars are nodes < 0)
            start_index=-1, next_function=(lambda x: x-1) )
        self.l = IdMap(namespace=int)   # labels
        self.q = IdMap(namespace=int)   # query graphs
        self.qlengths = torch.empty(0,  # length of query requirements lists
            dtype=torch.long, device=self.device )
        self.add_queries(*query_graphs)

    def add_queries(self, *query_graphs):
        self.checklist, self.querylist, self.qlengths = self._add_queries(query_graphs)

    def _add_queries(self, query_graphs):
        checklist, querylist, qlengths = preprocess_query_graphs(query_graphs, self.n, self.v, self.l, self.q)
        qlengths = torch.tensor(qlengths, dtype=torch.long, device=self.device)
        query_lengths = torch.cat([self.qlengths, qlengths], 0)
        checklist = [torch.tensor(req, dtype=torch.long, device=self.device) for req in checklist]
        querylist = [torch.tensor(query, dtype=torch.long, device=self.device) for query in querylist]
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
        return combined_cl, combined_ql, query_lengths

    def match(self, data_graph, *query_graphs):
        display = None
        complete = {}                                                           # list<Tensor<steps: ((qn1, dn1), (qn2, dn2), ...)>> completed solutions
        query_graphs = preprocess_query_tuples(query_graphs)
        if DISPLAY: display = Display()
        query_id_index = self.q.index                                           # Query index to reset after match is complete
        checklist, querylist, qlengths = self._add_queries(query_graphs)        # list<Tensor<query x 3: (s, l, t)>> list of required next edge lists
        if len(checklist) > 0:
            edges = GraphTensor(data_graph, self.n, self.l, device=self.device) # GraphTensor<Tensor<X x 2: (s, l)>) -> (Tensor<Y: t>, Tensor<Y: inverse_index>>
            solutions = torch.full((len(checklist[0]), 2), self.n.get(root),    # Tensor<solution x step: ((qn1, dn1), (qn2, dn2), ...)> in-progress solutions
                                   dtype=torch.long, device=self.device)
            queries = torch.arange(0, len(self.q),                              # Tensor<solution: query> inverse indices for solutions
                                   dtype=torch.long, device=self.device)

            for rlen, req in enumerate(checklist):                              # Tensor<query x 3: (s, l, t)>: required next edges
                ql = querylist[rlen]

                if DISPLAY: display(req, self.n, self.l, self.n, label='Requirements')

                # get assignments
                req_ = torch.full((len(self.q), 3), 0, dtype=torch.long, device=self.device)
                req_[ql] = req
                var_i = torch.nonzero(torch.eq(req_[queries][:,0:1], solutions[:,::2]))
                var_i = torch.cat([var_i[:,0:1], var_i[:,1:2]*2], 1)
                val_i = torch.cat([var_i[:,0:1], (var_i[:,1:2] + 1)], 1)

                # expand assigned to targets
                ei = val_i[:,0]
                ev = solutions[val_i.T[0], val_i.T[1]]
                expander = torch.full((solutions.size()[0],), -1, dtype=torch.long, device=self.device)
                expander[ei] = ev
                expander = torch.cat([expander.unsqueeze(1), req_[queries][:,1:2]], 1)

                if DISPLAY: display(expander, self.n, self.l, label='Expanders')

                # check targets against requirements
                t, inv = edges.map(expander)

                # FOR DEBUGGING
                # e = torch.cat([expander[inv], t.unsqueeze(1)], 1)
                # display(e, self.n, self.l, self.n, label='Expanded edges:')
                # -------------

                var_i = torch.nonzero(torch.eq(req_[queries][:,2:3], solutions[:,::2]))
                var_i = torch.cat([var_i[:,0:1], var_i[:,1:2]*2], 1)
                val_i = torch.cat([var_i[:,0:1], (var_i[:,1:2]+1)], 1)
                ei = val_i[:,0]
                ev = solutions[val_i.T[0], val_i.T[1]]
                req_tar = req_[queries][:,2]
                req_tar[ei] = ev
                req_targets = req_tar[inv]

                match = torch.logical_or(req_targets < 0, torch.eq(req_targets, t))
                m = torch.nonzero(match).squeeze(1)

                # expand solutions for matching targets
                solutions = torch.cat([
                    solutions[inv][m],
                    req_[queries][inv][m][:,2:3],
                    t[m].unsqueeze(1)
                ], 1 )
                queries = queries[inv][m]

                if DISPLAY: display(solutions, *[self.n for _ in range(solutions.size()[1])], label='Intermediate')

                # publish solutions
                solved = torch.eq(qlengths[queries], rlen + 1)
                solvedi = torch.nonzero(solved).squeeze(1)
                unsolvedi = torch.nonzero(~solved).squeeze(1)
                full_solutions = solutions[solvedi]
                solution_queries = queries[solvedi]
                for i, sol in enumerate(full_solutions):
                    q = self.q.identify(solution_queries[i].item())
                    assignments = {}
                    for i, vi in enumerate(sol[2::2]):
                        v = vi.item()
                        if v < 0:
                            assignments[self.v.identify(v)] = self.n.identify(sol[i*2+3].item())
                    complete.setdefault(q, []).append(assignments)
                solutions = solutions[unsolvedi]
                queries = queries[unsolvedi]

                if DISPLAY:
                    print('Complete solutions:')
                    for s in complete.values():
                        print(s)

            for query_graph in query_graphs:
                del self.q[query_graph]
            self.q.index = query_id_index

        return complete



if __name__ == '__main__':
    from GRIDD.data_structures.graph_matching.graph_matching_engine_spec import GraphMatchingEngineSpec as Spec
    print(Spec.verify(GraphMatchingEngine))




