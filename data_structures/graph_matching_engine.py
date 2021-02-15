
from GRIDD.data_structures.graph_matching_engine_spec import GraphMatchingEngineSpec

from GRIDD.utilities import IdNamespace
from itertools import chain
import torch


class GraphMatchingEngine:

    def __init__(self):
        pass

    def match(self, data_graph, *query_graphs):
        query_graphs = query_graph_var_pp(*query_graphs)
        data_adj_entries, data_attr_entries, data_ids, edge_ids, attr_ids = graph_to_entries(data_graph)
        query_adj_entries, query_attr_entries, query_ids, _, _ = graph_to_entries(*query_graphs, edge_ids=edge_ids, attribute_ids=attr_ids)
        data_adj = torch.LongTensor(list(chain(*data_adj_entries)))
        data_attr = entries_to_tensor(data_attr_entries, data_ids, attr_ids)
        query_adj = torch.LongTensor(list(chain(*query_adj_entries)))
        query_attr = entries_to_tensor(query_attr_entries, query_ids, attr_ids)
        compatible_nodes = joined_subset(query_attr, data_attr)
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
        query_counts = torch.cat([query_source_counts, query_target_counts], 1)
        display(query_counts, query_ids, None, None,
                label='Query constraint counts')
        for i in range(1):
            unique_sts = torch.unique(edge_pairs[:,[0,1,2,4]], dim=0)
            unique_stt = torch.unique(edge_pairs[:,[0,1,3,4]], dim=0)
            cs, rcs, source_counts = torch.unique(unique_sts[:,[0,2,3]], dim=0, return_inverse=True, return_counts=True)
            display(torch.cat([cs, source_counts.unsqueeze(1)], dim=1), query_ids, data_ids, edge_ids, None,
                    label='Out-property counts per candidate node assignment')
            ct, rct, target_counts = torch.unique(unique_stt[:,[1,2,3]], dim=0, return_inverse=True, return_counts=True)
            display(torch.cat([ct, target_counts.unsqueeze(1)], dim=1), query_ids, data_ids, edge_ids, None,
                    label='In-property counts per candidate node assignment')
            sources, rsi = torch.unique(cs[:,:2], dim=0, return_inverse=True)
            display(sources, query_ids, data_ids, label='Source assignments')
            targets, rti = torch.unique(ct[:,:2], dim=0, return_inverse=True)
            display(targets, query_ids, data_ids, label='Target assignments')
            assignments, dri = torch.unique(torch.cat([sources, targets], 0), dim=0, return_inverse=True)
            source_label_counts = torch.index_put(torch.zeros(sources.size(0), len(edge_ids)).long(), (rsi, cs[:,2]), source_counts)
            display(torch.cat([sources, source_label_counts], 1), query_ids, data_ids, *([None]*len(edge_ids)),
                    label='Out-property counts per candidate node assignment')
            target_label_counts = torch.index_put(torch.zeros(targets.size(0), len(edge_ids)).long(), (rti, ct[:,2]), target_counts)
            display(torch.cat([targets, target_label_counts], 1), query_ids, data_ids, *([None]*len(edge_ids)),
                    label='In-property counts per candidate node assignment')
            req_source_counts = query_source_counts[sources[:,0]]
            display(torch.cat([sources, req_source_counts], 1), query_ids, data_ids, *([None]*len(edge_ids)),
                    label='Required out-property counts per candidate node assignment')
            req_target_counts = query_target_counts[targets[:,0]]
            display(torch.cat([targets, req_target_counts], 1), query_ids, data_ids, *([None]*len(edge_ids)),
                    label='Required in-property counts per candidate node assignment')
            source_check = torch.le(req_source_counts, source_label_counts)
            target_check = torch.le(req_target_counts, target_label_counts)
            source_compatibility_mask = torch.ge(torch.sum(source_check.long(), dim=1), len(edge_ids))
            target_compatibility_mask = torch.ge(torch.sum(target_check.long(), dim=1), len(edge_ids))
            source_incompatibility_ = filter_rows(cs, ~source_compatibility_mask)[:,:2]
            target_incompatibility_ = filter_rows(ct, ~target_compatibility_mask)[:,:2]
            incompatible_assignments = torch.cat([source_incompatibility_, target_incompatibility_], dim=0).unique(dim=0)
            display(incompatible_assignments, query_ids, data_ids,
                    label='Incompatible assignments')
            edge_pairs = filter_rows(edge_pairs, ~row_membership(edge_pairs[:,[0,2]], incompatible_assignments))
            edge_pairs = filter_rows(edge_pairs, ~row_membership(edge_pairs[:,[1,3]], incompatible_assignments))
            display(edge_pairs, query_ids, query_ids, data_ids, data_ids, edge_ids,
                    label='Edge candidates (%d) after %d link filters' % (len(edge_pairs), i+1))
        return

def query_graph_var_pp(*query_graphs):
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
        edge_ids = IdNamespace(namespace=int)
    if attribute_ids is None:
        attribute_ids = IdNamespace(namespace=int)
    node_ids = IdNamespace(namespace=int)
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
    c_exist = c_counts[a_ridx]
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
                    e_ = ids[i][int(e)]
                else:
                    e_ = int(e)
                if isinstance(e_, tuple):
                    _, e_ = e_
                to_print.append(e_)
            print(('{:6}'*len(row)).format(*to_print))
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