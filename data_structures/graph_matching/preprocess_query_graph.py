
import random
from collections import defaultdict

from GRIDD.data_structures.graph_matching.reverse_label import ReverseLabel as Rlabel
from GRIDD.data_structures.graph_matching.root import root, rooted_edge


def preprocess_query_graphs(query_graphs, nodemap, varmap, edgemap, querymap):
    constant_counts = defaultdict(int)
    query_graphs = preprocess_query_tuples(query_graphs)
    querylist = []
    checklist = []
    qlengths = []
    for query_graph in query_graphs:
        constants = {n for n in query_graph.nodes()
                     if 'var' not in query_graph.data(n)
                     or not (query_graph.data(n)['var'])}
        for c in constants:
            constant_counts[c] += 1
    for query_graph in query_graphs:
        cl = preprocess_query_graph(query_graph, nodemap, varmap, edgemap, constant_counts)
        for i, req in enumerate(cl):
            while len(checklist) <= i:
                checklist.append([])
                querylist.append([])
            checklist[i].append(req)
            querylist[i].append(querymap.get(query_graph))
        qlengths.append(len(cl))
    return checklist, querylist, qlengths


def preprocess_query_graph(graph, nodemap, varmap, edgemap, constant_counts):
    checklist = []
    variables = set()
    variables = {n for n in graph.nodes()
                 if 'var' in graph.data(n)
                 and graph.data(n)['var']}
    constants = set(graph.nodes()) - variables
    left_nodes = set(graph.nodes())
    left_edges = set(graph.edges())
    while left_nodes:
        left_constants = left_nodes & constants
        if left_constants:
            trunk = min(left_constants, key=lambda c: constant_counts[c])
        else:
            trunk = random.choice(list(left_nodes))
        left_edges.add((root, trunk, rooted_edge))
        stack = [(root, trunk, rooted_edge)]
        while stack:
            s, t, l = stack.pop()
            if (s, t, l) not in left_edges or (t, s, Rlabel(l)) not in left_edges:
                left_edges.discard((s, t, l))
                left_edges.discard((t, s, Rlabel(l)))
            if isinstance(l, Rlabel):
                left_edges.discard((t, s, Rlabel(l)))
                left_edges.discard((s, t, l))
            else:
                left_edges.discard((s, t, l))
                left_edges.discard((t, s, Rlabel(l)))
            checklist.append((s, t, l))
            if t in left_nodes:
                left_nodes.remove(t)
                for s_, t_, l_ in sorted(graph.out_edges(t),
                                         key=lambda e: 0 if e[1] in variables else 1/constant_counts.get(e, 1)):
                    stack.append((s_, t_, l_))
                for s_, t_, l_ in sorted(graph.in_edges(t),
                                         key=lambda e: 0 if e[0] in variables else 1/constant_counts.get(e, 1)):
                    stack.append((t_, s_, Rlabel(l_)))
    mapped_checklist = []
    for s, t, l in checklist:
        s = varmap.get(s) if s in variables else nodemap.get(s)
        t = varmap.get(t) if t in variables else nodemap.get(t)
        l = edgemap.get(l)
        mapped_checklist.append((s, l, t))
    return mapped_checklist


def preprocess_query_tuples(query_graphs):
    qgs = []
    for qg in query_graphs:
        if isinstance(qg, tuple):
            qg, vars = qg
            for var in vars:
                qg.data(var)['var'] = True
        qgs.append(qg)
    return qgs










