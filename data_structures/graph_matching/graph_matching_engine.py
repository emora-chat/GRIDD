
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
            nums_rows = torch.arange(0, seg, dtype=torch.long, device=self.device).unsqueeze(1).expand(self.checklist.size()[:2])
            nums_cols = torch.arange(0, self.checklist.size()[1], dtype=torch.long, device=self.device).unsqueeze(0).expand(self.checklist.size()[:2])
            for i in range(3):
                flatrows = nums_rows.flatten()
                flatcols = nums_cols.flatten()
                checklistslice = self.checklist[:,:,i]
                flatchecklist = checklistslice.flatten()
                checklist[flatrows, flatcols, i] = flatchecklist
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
        torch.cuda.reset_peak_memory_stats(self.device)
        if len(query_graphs) == 0 and len(self.query_graphs) == 0: return {}
        p.start('match')
        p.start('querygen')
        display = None
        complete = {}                                                       # list<Tensor<steps: ((qn1, dn1), (qn2, dn2), ...)>> completed solutions
        if len(query_graphs) > 0:
            query_graphs = preprocess_query_tuples(query_graphs)
            if DISPLAY: display = Display()
            query_id_index = self.q.index                                   # Query index to reset after match is complete
            checklist, query_lengths = self._add_queries(query_graphs)
        else:
            query_id_index = self.q.index
            checklist, query_lengths = self.checklist, self.query_lengths
        if len(checklist) <= 0:
            p.stop(); p.stop()
            return complete
        nn = len(data_graph.nodes())
        ne = len(data_graph.edges())
        print('Nodes: %d'%nn)
        print('Edges: %d'%ne)
        p.next(f'creating graph tensor ({nn} nodes, {ne} edges)')
        edges = GraphTensor(data_graph, self.n, self.l, device=self.device) # GraphTensor<Tensor<X x 2: (s, l)>) -> (Tensor<Y: t>, Tensor<Y: inverse_index>>
        p.next('initializing solutions matrix')
        sols = torch.full((int(checklist.size()[0]), 2), self.n.get(root),  # Tensor<solution x step: ((qn1, dn1), (qn2, dn2), ...)> in-progress solutions
                               dtype=torch.long, device=self.device)
        solqs = torch.arange(0, len(self.q),                                # Tensor<solution: query> inverse indices for solutions
                               dtype=torch.long, device=self.device)
        p.stop()
        p.start('loop')
        print('Checklist:', checklist.size())
        for num_checked, reqs in enumerate(checklist.transpose(0, 1)):      # Tensor<query x 3: (s, l, t)>: required next edges
            solreqs = reqs[solqs]
            if DISPLAY: print('{:#^50s}'.format(f' ITER {num_checked} '))
            if DISPLAY: display(solreqs, self.n, self.l, self.n, label='Requirements')
            if DISPLAY: display(sols, *[self.n for _ in range(sols.size()[1])], label='sols')
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
            expanderindx = torch.nonzero(~isfilter).squeeze(1)
            sourcelabels = torch.cat([
                sources[expanderindx].unsqueeze(1),
                solreqs[expanderindx][:,1:2]
            ], 1 )
            print(num_checked, end = ' ')
            targets, ii = edges.targets(sourcelabels)
            sols_expanded = torch.cat([
                sols[expanderindx][ii],
                solreqs[expanderindx][ii][:,2:3],
                targets.unsqueeze(1)
            ], 1 )
            if DISPLAY: display(sols_expanded, *[self.n for _ in range(sols_expanded.size()[1])], label='expansion')
            qs_expanded = solqs[expanderindx][ii]
            sols = torch.cat([sols_to_keep, sols_expanded], 0)
            solqs = torch.cat([qs_to_keep, qs_expanded], 0)
            solved = (num_checked + 1 >= query_lengths)[solqs]
            solvedindx = torch.nonzero(solved).squeeze(1)
            unsolvedindx = torch.nonzero(~solved).squeeze(1)
            full_solutions = sols[solvedindx]
            full_solqs = solqs[solvedindx]
            sols = sols[unsolvedindx]
            solqs = solqs[unsolvedindx]
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
            if len(sols) == 0:
                break
        p.stop()
        p.start(f'postprocessing (MAX MEMORY: {torch.cuda.max_memory_allocated(self.device) / 1073741824:.3f}GB)')
        for query_graph in query_graphs:
            del self.q[query_graph]
        self.q.index = query_id_index
        p.stop()
        p.stop()
        return complete


if __name__ == '__main__':
    from GRIDD.data_structures.graph_matching.graph_matching_engine_spec import GraphMatchingEngineSpec as Spec
    print(Spec.verify(GraphMatchingEngine))




