
import torch
from itertools import chain

from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.graph_matching.graph_tensor import GraphTensor
from GRIDD.data_structures.graph_matching.preprocess_query_graph import preprocess_query_graphs, preprocess_query_tuples
from GRIDD.utilities.utilities import TensorDisplay as Display
from GRIDD.utilities.profiler import profiler as p
from GRIDD.data_structures.graph_matching.root import root

DISPLAY = False

torch.no_grad()

class GraphMatchingEngine:

    def __init__(self, *query_graphs, device='cpu'):
        self.device = device
        self.query_graphs = []              # List<ConceptGraph> of unprocessed precondition concept graphs
        self.checklist = torch.tensor([])   # list<Tensor<q x 3: (n, l, n)>> list of required next edge lists
        self.querylist = []                 # list<Tensor<q: query>> list of queries corresponding to checklist requirements
        self.n = IdMap(namespace=int)       # nodes (both query and data nodes: static query nodes, dynamic query nodes, data nodes)
        self.v = IdMap(namespace=int,       # var nodes (vars are nodes < 0)
            start_index=-1, next_function=(lambda x: x-1) )
        self.l = IdMap(namespace=int)       # labels
        self.q = IdMap(namespace=int)       # query graphs
        self.query_lengths = torch.empty(0, # length of query requirements lists
            dtype=torch.long, device=self.device )
        self.add_queries(*query_graphs)
        self.process_queries()

    def add_queries(self, *query_graphs):
        self.query_graphs.extend(query_graphs)

    def process_queries(self):
        self.checklist, self.query_lengths = self._add_queries(self.query_graphs)

    def _add_queries(self, query_graphs):
        if len(query_graphs) == 0:
            return self.checklist, self.query_lengths
        cl, ls = preprocess_query_graphs(query_graphs, self.n, self.v, self.l, self.q)
        query_lengths = torch.tensor(ls, dtype=torch.long, device=self.device)
        query_lengths = torch.cat([self.query_lengths, query_lengths] if len(self.query_lengths) > 0 else [query_lengths], 0)
        max_query_len = torch.max(query_lengths) if len(query_lengths) > 0 else 0
        checklist = torch.full((self.checklist.size()[0] + len(cl), max_query_len, 3), 0, dtype=torch.long, device=self.device)
        cl_data = list(chain(*[[(s, l, t, i, j) for j, (s, l, t) in enumerate(row)] for i, row in enumerate(cl)]))
        cl_tensor = torch.tensor(cl_data, dtype=torch.long, device=self.device)
        seg = self.checklist.size()[0]
        for i in range(3):
            checklist[cl_tensor[:,3] + seg, cl_tensor[:,4], i] = cl_tensor[:,i]
        if len(self.checklist) > 0:
            nums_rows = torch.arange(0, seg, dtype=torch.long, device=self.device).unsqueeze(1).expand_as(self.checklist)
            nums_cols = torch.arange(0, self.checklist.size()[1], dtype=torch.long, device=self.device).unsqueeze(0).expand_as(self.checklist)
            checklist[nums_rows.flatten(), nums_cols.flatten()] = self.checklist.flatten()
        return checklist, query_lengths

    def assigned(self, assignments, variables):
        result = torch.full((int(assignments.size()[0]),), -1, dtype=torch.long, device=self.device)
        assnmatch = torch.eq(assignments[:, ::2], variables.unsqueeze(1))
        assnmatchindx = torch.nonzero(assnmatch)
        if len(assnmatchindx) == 0:
            return result
        valueindx = torch.cat([assnmatchindx[:, 0:1], assnmatchindx[:, 1:2] * 2 + 1], 1)
        result[valueindx[:, 0]] = assignments[valueindx[:,0], valueindx[:,1]]
        return result

    def match(self, data_graph, *query_graphs):
        if len(query_graphs) == 0 and len(self.query_graphs) == 0: return {}
        p.start('match')
        p.start('querygen')
        display = None
        complete = {}                                                       # list<Tensor<steps: ((qn1, dn1), (qn2, dn2), ...)>> completed solutions
        query_graphs = preprocess_query_tuples(query_graphs)
        if DISPLAY: display = Display()
        query_id_index = self.q.index                                       # Query index to reset after match is complete
        checklist, query_lengths = self._add_queries(query_graphs)
        if len(checklist) <= 0: return complete
        p.next(f'creating graph tensor ({len(data_graph.nodes())} nodes, {len(data_graph.edges())} edges)')
        edges = GraphTensor(data_graph, self.n, self.l, device=self.device) # GraphTensor<Tensor<X x 2: (s, l)>) -> (Tensor<Y: t>, Tensor<Y: inverse_index>>
        p.next('initializing solutions matrix')
        sols = torch.full((int(checklist.size()[0]), 2), self.n.get(root),  # Tensor<solution x step: ((qn1, dn1), (qn2, dn2), ...)> in-progress solutions
                               dtype=torch.long, device=self.device)
        solqs = torch.arange(0, len(self.q),                                # Tensor<solution: query> inverse indices for solutions
                               dtype=torch.long, device=self.device)
        p.stop()
        p.start('loop')
        for num_checked, reqs in enumerate(checklist.transpose(0, 1)):      # Tensor<query x 3: (s, l, t)>: required next edges
            p.start(f'iter {num_checked} ({sols.size()[0]} sols)')
            solreqs = reqs[solqs]
            if DISPLAY: print('{:#^50s}'.format(f' ITER {num_checked} '))
            if DISPLAY: display(solreqs, self.n, self.l, self.n, label='Requirements')
            if DISPLAY: display(sols, *[self.n for _ in range(sols.size()[1])], label='sols')
            p.start(f'filter')
            tarfilters = self.assigned(sols, solreqs[:,2])
            istarconst = solreqs[:,2] >= 0
            target_const_indx = torch.nonzero(istarconst).squeeze(1)
            tarfilters[target_const_indx] = solreqs[target_const_indx][:,2]
            sources = self.assigned(sols, solreqs[:,0])
            isfilter = tarfilters >= 0
            filterindx = torch.nonzero(isfilter)
            filterindx = filterindx.squeeze(1)
            filters = torch.cat([
                sources[filterindx].unsqueeze(1),
                solreqs[filterindx][:,1:2],
                tarfilters[filterindx].unsqueeze(1)
            ], 1 )
            satisfied = edges.has(filters)
            if DISPLAY: display(torch.cat([filters, satisfied.to(torch.long)[:,None]], 1),
                                self.n, self.l, self.n, None, label='filter')
            satindx = torch.nonzero(satisfied).squeeze(1)
            sols_to_keep = torch.cat([
                sols[filterindx][satindx],
                solreqs[filterindx][satindx][:,2:3],
                tarfilters[filterindx][satindx].unsqueeze(1)
            ], 1 )
            qs_to_keep = solqs[filterindx][satindx]
            p.next('expand')
            expanderindx = torch.nonzero(~isfilter).squeeze(1)
            sourcelabels = torch.cat([
                sources[expanderindx].unsqueeze(1),
                solreqs[expanderindx][:,1:2]
            ], 1 )
            targets, ii = edges.targets(sourcelabels)
            sols_expanded = torch.cat([
                sols[expanderindx][ii],
                solreqs[expanderindx][ii][:,2:3],
                targets.unsqueeze(1)
            ], 1 )
            if DISPLAY: display(sols_expanded, *[self.n for _ in range(sols_expanded.size()[1])], label='expansion')
            qs_expanded = solqs[expanderindx][ii]
            p.next(f'solution ({sols_to_keep.size()[0]} kept, {sols_expanded.size()[0]} expanded)')
            sols = torch.cat([sols_to_keep, sols_expanded], 0)
            solqs = torch.cat([qs_to_keep, qs_expanded], 0)
            solved = (num_checked + 1 >= query_lengths)[solqs]
            solvedindx = torch.nonzero(solved).squeeze(1)
            unsolvedindx = torch.nonzero(~solved).squeeze(1)
            full_solutions = sols[solvedindx]
            full_solqs = solqs[solvedindx]
            sols = sols[unsolvedindx]
            solqs = solqs[unsolvedindx]
            p.next('collection')
            for i, sol in enumerate(full_solutions):
                q = self.q.identify(full_solqs[i].item())
                assignments = {}
                for i, vi in enumerate(sol[2::2]):
                    v = vi.item()
                    if v < 0:
                        nid = sol[i * 2 + 3].item()
                        nident = self.n.identify(nid)
                        assignments[self.v.identify(v)] = nident
                complete.setdefault(q, []).append(assignments)
            if DISPLAY:
                print('Complete solutions:')
                for s in complete.values():
                    print(s)
            if len(sols) == 0:
                break
            p.stop()
            p.stop()
        p.end()
        p.start('postprocessing')
        for query_graph in query_graphs:
            del self.q[query_graph]
        self.q.index = query_id_index
        p.end()
        p.report()
        return complete


        #     p.start('assign reqs')
        #
        #     ql = querylist[rlen]
        #     req_ = torch.full((len(self.q), 3), 0, dtype=torch.long, device=self.device)
        #     req_[ql] = req
        #
        #     if DISPLAY: display(req, self.n, self.l, self.n, label='Requirements')
        #
        #     p.next(f'get assignments')
        #
        #     # get assignments
        #     var_i = torch.nonzero(torch.eq(req_[queries][:,0:1], solutions[:,::2]))
        #     var_i = torch.cat([var_i[:,0:1], var_i[:,1:2]*2], 1)
        #     val_i = torch.cat([var_i[:,0:1], (var_i[:,1:2] + 1)], 1)
        #
        #     ei = val_i[:,0]
        #     ev = solutions[val_i.T[0], val_i.T[1]]
        #     expander = torch.full((solutions.size()[0],), -1, dtype=torch.long, device=self.device)
        #     expander[ei] = ev
        #     expander = torch.cat([expander.unsqueeze(1), req_[queries][:,1:2]], 1)
        #
        #     if DISPLAY: display(expander, self.n, self.l, label='Expanders')
        #
        #     p.next('expand')
        #
        #     # expand assigned to targets
        #     t, inv = edges.targets(expander)
        #
        #     # FOR DEBUGGING
        #     # e = torch.cat([expander[inv], t.unsqueeze(1)], 1)
        #     # display(e, self.n, self.l, self.n, label='Expanded edges:')
        #     # -------------
        #
        #     p.next(f'check targets against reqs (expanded to {len(t)})')
        #
        #     # check targets against requirements
        #     var_i = torch.nonzero(torch.eq(req_[queries][:,2:3], solutions[:,::2]))
        #     var_i = torch.cat([var_i[:,0:1], var_i[:,1:2]*2], 1)
        #     val_i = torch.cat([var_i[:,0:1], (var_i[:,1:2]+1)], 1)
        #     ei = val_i[:,0]
        #     ev = solutions[val_i.T[0], val_i.T[1]]
        #     req_tar = req_[queries][:,2]
        #     req_tar[ei] = ev
        #     req_targets = req_tar[inv]
        #
        #     match = torch.logical_or(req_targets < 0, torch.eq(req_targets, t))
        #     m = torch.nonzero(match).squeeze(1)
        #
        #     p.next(f'update solutions for matching targets ({len(m)} matched expanded)')
        #
        #     # expand solutions for matching targets
        #     solutions = torch.cat([
        #         solutions[inv][m],
        #         req_[queries][inv][m][:,2:3],
        #         t[m].unsqueeze(1)
        #     ], 1 )
        #     queries = queries[inv][m]
        #
        #     p.next(f'filter full solutions ({len(solutions)} s)')
        #
        #     if DISPLAY: display(solutions, *[self.n for _ in range(solutions.size()[1])], label='Intermediate')
        #
        #     # publish solutions
        #     solved = torch.eq(qlengths[queries], rlen + 1)
        #     solvedi = torch.nonzero(solved).squeeze(1)
        #     unsolvedi = torch.nonzero(~solved).squeeze(1)
        #     full_solutions = solutions[solvedi]
        #     solution_queries = queries[solvedi]
        #     solutions = solutions[unsolvedi]
        #     queries = queries[unsolvedi]
        #
        #     p.next(f'publish full solutions ({len(full_solutions)} full s)')
        #     for i, sol in enumerate(full_solutions):
        #         q = self.q.identify(solution_queries[i].item())
        #         assignments = {}
        #         for i, vi in enumerate(sol[2::2]):
        #             v = vi.item()
        #             if v < 0:
        #                 assignments[self.v.identify(v)] = self.n.identify(sol[i*2+3].item())
        #         complete.setdefault(q, []).append(assignments)
        #
        #     p.stop()
        #     p.stop()
        #
        #     if DISPLAY:
        #         print('Complete solutions:')
        #         for s in complete.values():
        #             print(s)
        #
        #     if len(solutions) == 0:
        #         break
        #
        # p.end()
        # p.start('postprocessing')
        #
        # for query_graph in query_graphs:
        #     del self.q[query_graph]
        # self.q.index = query_id_index
        #
        # p.end()
        # p.report()
        #
        # return complete


if __name__ == '__main__':
    from GRIDD.data_structures.graph_matching.graph_matching_engine_spec import GraphMatchingEngineSpec as Spec
    print(Spec.verify(GraphMatchingEngine))




