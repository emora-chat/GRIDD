
from GRIDD.data_structures.graph_matching_engine_spec import GraphMatchingEngineSpec

from GRIDD.data_structures.id_map import IdMap
from itertools import chain
import torch


class GraphMatchingEngine:

    def __init__(self):
        pass

    def match(self, data_graph, *query_graphs, limit=10):
        query_graphs = query_graph_var_preproc(*query_graphs)
        data_adj_entries, data_attr_entries, data_ids, edge_ids, attr_ids = graph_to_entries(data_graph)
        query_adj_entries, query_attr_entries, query_ids, _, _ = graph_to_entries(*query_graphs, edge_ids=edge_ids, attribute_ids=attr_ids)
        data_adj = torch.LongTensor(list(chain(*data_adj_entries)))
        data_attr = entries_to_tensor(data_attr_entries, data_ids, attr_ids)
        query_adj = torch.LongTensor(list(chain(*query_adj_entries)))
        query_attr = entries_to_tensor(query_attr_entries, query_ids, attr_ids)
        compatible_nodes = joined_subset(query_attr, data_attr)
        query_nodes = torch.arange(0, query_attr.size(0), dtype=torch.long)
        floating_node_filter = ~row_membership(query_nodes.unsqueeze(1),
                                               torch.unique(torch.cat([query_adj[:,0], query_adj[:,1]], 0)).unsqueeze(1))
        floating_nodes = filter_rows(query_nodes.unsqueeze(1), floating_node_filter).squeeze(1)
        fc = torch.nonzero(compatible_nodes[floating_nodes,:])
        floating_compatibilities = torch.cat([floating_nodes[fc[:,0]].unsqueeze(1), fc[:,1:]], 1)
        edge_pairs = join(query_adj, data_adj, 2, list(range(len(edge_ids))))
        source_compatible = gather_by_indices(compatible_nodes, edge_pairs[:,[0,2]])
        target_compatible = gather_by_indices(compatible_nodes, edge_pairs[:,[1,3]])
        compatible = torch.logical_and(source_compatible, target_compatible)
        edge_pairs = filter_rows(edge_pairs, compatible)
        display(edge_pairs, query_ids, query_ids, data_ids, data_ids, edge_ids,
                label='Initial edge candidates (%d)' % len(edge_pairs))
        qs, rqs, qsc = torch.unique(query_adj[:, [0, 2]], dim=0, return_inverse=True, return_counts=True)
        display(torch.cat([qs, qsc.unsqueeze(1)], dim=1), query_ids, edge_ids, None,
                label='Query out-constraint counts')
        qt, rqt, qtc = torch.unique(query_adj[:, [1, 2]], dim=0, return_inverse=True, return_counts=True)
        display(torch.cat([qt, qtc.unsqueeze(1)], dim=1), query_ids, edge_ids, None,
                label='Query in-constraint counts')
        query_source_counts = torch.sparse.LongTensor(qs.T, qsc, [len(query_ids), len(edge_ids)]).to_dense()
        display(query_source_counts, query_ids, edge_ids, None,
                label='Query out-constraint counts')
        query_target_counts = torch.sparse.LongTensor(qt.T, qtc, [len(query_ids), len(edge_ids)]).to_dense()
        display(query_target_counts, query_ids, edge_ids, None,
                label='Query in-constraint counts')
        constraints = torch.cat([query_source_counts, query_target_counts], 1)
        display(constraints, query_ids, None, None,
                label='Query constraint counts')
        prev_num_edges = edge_pairs.size(0) * 2
        num_edges = edge_pairs.size(0)
        i = 0
        while num_edges < prev_num_edges or i == limit:
            qsqtdsl = torch.unique(edge_pairs[:,[0,1,2,4]], dim=0)
            qsqtdtl = torch.unique(edge_pairs[:,[0,1,3,4]], dim=0)
            qsdsl, source_counts = torch.unique(qsqtdsl[:,[0,2,3]], dim=0, return_counts=True)
            display(torch.cat([qsdsl, source_counts.unsqueeze(1)], dim=1), query_ids, data_ids, edge_ids, None,
                    label='Out-property counts per candidate node assignment')
            qtdtl, target_counts = torch.unique(qsqtdtl[:,[1,2,3]], dim=0, return_counts=True)
            display(torch.cat([qtdtl, target_counts.unsqueeze(1)], dim=1), query_ids, data_ids, edge_ids, None,
                    label='In-property counts per candidate node assignment')
            qsds, asi = torch.unique(qsdsl[:,:2], dim=0, return_inverse=True)
            display(qsds, query_ids, data_ids, label='Source assignments')
            qtdt, ati = torch.unique(qtdtl[:,:2], dim=0, return_inverse=True)
            display(qtdt, query_ids, data_ids, label='Target assignments')
            qd, dsi = torch.unique(torch.cat([qsds, qtdt], dim=0), dim=0, return_inverse=True)
            display(qd, query_ids, data_ids, label='Assignments')
            source_indices = (dsi[:len(qsds)][asi], qsdsl[:,2])
            target_indices = (dsi[len(qsds):][ati], qtdtl[:,2]+len(edge_ids))
            source_values = source_counts
            target_values = target_counts
            properties_template = torch.zeros(len(qd), len(edge_ids)*2).long()
            indices = (torch.cat([source_indices[0], target_indices[0]], 0), torch.cat([source_indices[1], target_indices[1]], 0))
            values = torch.cat([source_values, target_values], 0)
            properties = torch.index_put(properties_template, indices, values)
            display(torch.cat([qd,properties],1), query_ids, data_ids, *([None]*len(edge_ids)*2),
                    label='Properties per assignment')
            requirements = constraints[qd[:,0]]
            display(torch.cat([qd,requirements],1), query_ids, data_ids, *([None]*len(edge_ids)*2),
                    label='Requirements per assignment')
            satisfactions = torch.eq(torch.sum(torch.le(requirements, properties).long(), 1), len(edge_ids)*2)
            display(torch.cat([qd,satisfactions.unsqueeze(1)],1), query_ids, data_ids, None,
                    label='Satisfactions')
            invalid_assignments = filter_rows(qd, ~satisfactions)
            display(invalid_assignments, query_ids, data_ids, label='Invalid assignments')
            edge_filter_1 = row_membership(edge_pairs[:,[0,2]], invalid_assignments)
            display(torch.cat([edge_pairs,edge_filter_1.unsqueeze(1)],1), query_ids, query_ids, data_ids, data_ids, edge_ids, None,
                    label='Edge filter 1')
            edge_pairs = filter_rows(edge_pairs, ~edge_filter_1)
            edge_filter_2 = row_membership(edge_pairs[:,[1,3]], invalid_assignments)
            display(torch.cat([edge_pairs,edge_filter_2.unsqueeze(1)],1), query_ids, query_ids, data_ids, data_ids, edge_ids, None,
                    label='Edge filter 2')
            edge_pairs = filter_rows(edge_pairs, ~edge_filter_2)
            display(edge_pairs, query_ids, query_ids, data_ids, data_ids, edge_ids,
                    label='Edge candidates (%d) after %d link filters' % (len(edge_pairs), i + 1))
            prev_num_edges = num_edges
            num_edges = edge_pairs.size(0)
            i += 1
        edge_assignments, node_assignments = edge_pairs_postproc(edge_pairs, floating_compatibilities, query_ids, data_ids, edge_ids)
        all_solutions = gather_solutions(edge_assignments, node_assignments)
        return all_solutions

def query_graph_var_preproc(*query_graphs):
    """Preprocess query graph vars"""
    query_graphs = list(query_graphs)
    for i, qg in enumerate(query_graphs):
        if isinstance(qg, tuple):
            qg, vars = qg
            query_graphs[i] = qg
            for var in vars:
                qg.data(var)['var'] = True
    return query_graphs

def graph_to_entries(*graphs, edge_ids=None, attribute_ids=None):
    """
    Returns (adjacencies, attributes, node id namespace, edge id namespace, attribute id namespace)
    """
    with_disambiguation = len(graphs) > 1
    if edge_ids is None:
        edge_ids = IdMap(namespace=int)
    if attribute_ids is None:
        attribute_ids = IdMap(namespace=int)
    node_ids = IdMap(namespace=int)
    adjacencies = []
    attrs = []
    for graph in graphs:
        for node in graph.nodes():
            if with_disambiguation:
                node_ids.get((graph, node))
            else:
                node_ids.get(node)
            attribute_ids.get(node)
            if 'attributes' in graph.data(node):
                for attribute in graph.data(node)['attributes']:
                    attribute_ids.get(attribute)
        if with_disambiguation:
            get_id = lambda n: node_ids[(graph, n)]
        else:
            get_id = lambda n: node_ids[n]
        edges = [(get_id(s), get_id(t), edge_ids.get(l))
                      for s, t, l in graph.edges()]
        adjacencies.append(edges)
        for node in graph.nodes():
            if not ('var' in graph.data(node) and graph.data(node)['var'] is True):
                attrs.append((get_id(node), attribute_ids[node]))
            if 'attributes' in graph.data(node):
                for attr in graph.data(node)['attributes']:
                    attrs.append((get_id(node), attribute_ids[attr]))
    return adjacencies, attrs, node_ids, edge_ids, attribute_ids

def entries_to_tensor(attrs, node_ids, attribute_ids):
    attr_indices = torch.LongTensor(list(zip(*attrs)))
    attr_values = torch.ones(len(attrs))
    attr_size = torch.Size([len(node_ids), len(attribute_ids)])
    attrs = torch.sparse.LongTensor(indices=attr_indices, values=attr_values, size=attr_size).to_dense()
    return attrs

def edge_pairs_postproc(edge_pairs, floating_compatibilities, query_ids, data_ids, edge_ids):
    ids = [query_ids.reverse(), query_ids.reverse(), data_ids.reverse(), data_ids.reverse(), edge_ids.reverse()]
    edge_assignments = {}
    for row in edge_pairs:
        row = [(ids[i][int(e)]) for i, e in enumerate(row)]
        (qg, qs), (_, qt), ds, dt, l = row
        edge_assignments.setdefault(qg, {}).setdefault((qs, qt, l), []).append((ds, dt))
    edge_assignments = {qg: qa for qg, qa in edge_assignments.items() if len(qg.edges()) == len(qa)}
    floating_comps = [(ids[0][int(e[0])], ids[2][int(e[1])]) for i, e in enumerate(floating_compatibilities)]
    node_assignments = {}
    for (qg, qn), dn in floating_comps:
        node_assignments.setdefault(qg, {}).setdefault(qn, []).append(dn)
        if qg not in edge_assignments:
            edge_assignments[qg] = {}
    return edge_assignments, node_assignments

def gather_solutions(edge_assignments, node_assignments):
    all_solutions = {}
    for query_graph, edge_assignment in edge_assignments.items():
        node_assignment = node_assignments.get(query_graph, {})
        num_vars = len(query_graph.nodes())
        solutions = [{}]
        edges = list(edge_traversal(query_graph))
        for qs, qt, l in edges:
            alternative_solutions = []
            for ds, dt in edge_assignment[(qs, qt, l)]:
                new_solutions = [dict(solution) for solution in solutions]
                for var, val in [(qs, ds), (qt, dt)]:
                    for solution in list(new_solutions):
                        if var in solution:
                            if solution[var] != val and solution in new_solutions:
                                new_solutions.remove(solution)
                        else:
                            solution[var] = val
                alternative_solutions.extend(new_solutions)
            solutions = alternative_solutions
        full_solutions = combinations(solutions, *[[(var, val) for val in valset] for var, valset in node_assignment.items()])
        final_solutions = []
        for solution in full_solutions:
            if len(solution) == 1:
                final_solutions.append(solution[0])
            else:
                edge_sol, node_sols = dict(solution[0]), solution[1:]
                edge_sol.update(node_sols)
                final_solutions.append(edge_sol)
        for solution in final_solutions:
            if len(solution) == num_vars:
                all_solutions.setdefault(query_graph, set()).add(frozenset(solution.items()))
    all_solutions = {qg: [{k: v for k, v in sol if 'var' in qg.data(k)} for sol in sols]
                     for qg, sols in all_solutions.items()}
    return all_solutions

def edge_traversal(graph):
    visited = set()
    stack = list(graph.edges())
    while stack:
        ps, pt, pl = stack.pop()
        if (ps, pt, pl) not in visited:
            visited.add((ps, pt, pl))
            yield (ps, pt, pl)
            stack.extend(list(graph.in_edges(ps)))
            stack.extend(list(graph.out_edges(ps)))
            stack.extend(list(graph.in_edges(pt)))
            stack.extend(list(graph.out_edges(pt)))

def combinations(*itemsets):
    c = [[]]
    for itemset in list(itemsets):
        if itemset:
            cn = []
            for item in list(itemset):
                ce = [list(e) for e in c]
                for sol in ce:
                    sol.append(item)
                cn.extend(ce)
            c = cn
    return c

def joined_subset(x, y):
    """
    Computes a 2D matrix representing whether row i of 2D
    matrix x represents a subset of row j of 2D matrix y.
    """
    xt = torch.repeat_interleave(x, y.size()[0], dim=0)
    yt = y.repeat(x.size()[0], 1)
    xs = torch.sum(xt, dim=1)
    conj = torch.logical_and(xt, yt).long()
    cs = torch.sum(conj, dim=1)
    cmp = torch.eq(xs, cs).long()
    res = cmp.view(-1, y.size()[0])
    return res

def join(x, y, group_idx=None, possible_groups=None):
    """
    Join 2D tensors x and y along 1st dimension,
    returning a 2D tensor where dim 2 is size x.size(1)+y.size(1).
    Represents every combination of rows between x and y.
    Passing in a group_idx will return the same output, but
    row combinations will only be made if x's row and y's row have
    the same value at group_idx of dim 1. possible_groups represents
    the range of grouping values that are possible.
    """
    if group_idx is None:
        xt = torch.repeat_interleave(x, y.size()[0], dim=0)
        yt = y.repeat(x.size()[0], 1)
        j = torch.cat([xt, yt], dim=1)
        return j
    else:
        xgroups = group_by_value(x, possible_groups, group_idx)
        ygroups = group_by_value(y, possible_groups, group_idx)
        jgroups = []
        for i in range(len(possible_groups)):
            xg, yg = xgroups[i], ygroups[i]
            xg_ = torch.cat([xg[:,:group_idx], xg[:,group_idx+1:]], 1)
            jg_ = join(xg_, yg)
            jgroups.append(jg_)
        j = torch.cat(jgroups, 0)
        return j

def group_by_value(x, possible_groups, group_idx=2):
    """
    Return a list of tensors, where each tensor represents
    the rows of 2D tensor x that have the same value at
    group_idx of dim 1.
    Must pass possible_groups as the range of possible values
    of the grouping, and the result list is returned in order
    of possible_groups' grouping order.
    """
    to_cmp = x.select(1, group_idx)
    groups = []
    for group in possible_groups:
        cmp = torch.eq(to_cmp, group).long()
        idx = torch.nonzero(cmp).squeeze(1)
        gathered = x[idx]
        groups.append(gathered)
    return groups

def filter_rows(x, condition):
    """
    Take only rows of tensor x if the corresponding
    entry of 1D tensor condition is True/1.
    """
    idx = torch.nonzero(condition).squeeze(1)
    return x[idx]

def gather_by_indices(a, idxs):
    """
    Create a 1D tensor formed from 2D tensor
    a at the indices given by 2D tensor indxs,
    which is a list of indices representation.
    """
    x = idxs.T[0]
    y = idxs.T[1]
    a_ = a[x]
    a__ = torch.gather(a_, 1, y.unsqueeze(1))
    return a__.squeeze(1)

def row_membership(a, b):
    """
    Checks for each row of a whether there exists
    an equivalent row in b, producing a 1D bool tensor.
    """
    a_unique, a_ridx, a_counts = torch.unique(a, dim=0, return_inverse=True, return_counts=True)
    c = torch.cat([a, b], 0)
    c_unique, c_ridx, c_counts = torch.unique(c, dim=0, return_inverse=True, return_counts=True)
    a_exist = a_counts[a_ridx]
    c_exist = c_counts[c_ridx[:a.size(0)]]
    m = torch.gt(c_exist, a_exist)
    return m

def display(x, *ids, label=None):
    """
    Print edge assignments in readable form for Nx5 tensor
    where 5d entries represent (qs, qt, ds, dt, label).
    """
    if label is not None:
        print(label, ':')
    ids = [(e.reverse() if e is not None else e) for e in ids]
    if len(ids) == x.size()[1]:
        for row in x:
            to_print = []
            for i, e in enumerate(row):
                if hasattr(ids[i], '__getitem__'):
                    if int(e) == 3:
                        djakfd = 0
                    e_ = ids[i][int(e)]
                else:
                    e_ = int(e)
                if isinstance(e_, tuple):
                    _, e_ = e_
                to_print.append(e_)
            print(('{:10}'*len(row)).format(*to_print))
    else:
        colnames = [((ids[1][i]) if ids[1] is not None else '') for i in range(x.size(1))]
        print((' '*9+'{:>9}'*x.size(1)).format(*colnames))
        for i in range(x.size(0)):
            s = x.size(1)
            fmtstr = '{:>9}'+'{:>9}'*int(s)
            args = [ids[0][i], *[int(j) for j in x[i]]]
            for i, arg in enumerate(args):
                if isinstance(arg, tuple):
                    args[i] = arg[1]
            print(fmtstr.format(*args))
    print()

if __name__ == '__main__':
    print(GraphMatchingEngineSpec.verify(GraphMatchingEngine))