
import random
from collections import defaultdict
from itertools import chain

from GRIDD.data_structures.graph_matching.reverse_label import ReverseLabel as Rlabel
from GRIDD.data_structures.graph_matching.root import root, rooted_edge


def preprocess_query_graphs(query_graphs, nodemap, varmap, edgemap, querymap, utilities=None):
    constant_counts = defaultdict(int)
    query_graphs = preprocess_query_tuples(query_graphs)
    checklist = []
    qlengths = []
    for query_graph in query_graphs:
        constants = {n for n in query_graph.nodes()
                     if 'var' not in query_graph.data(n)
                     or not (query_graph.data(n)['var'])}
        for c in constants:
            constant_counts[c] += 1
    for query_graph in query_graphs:
        querymap.get(query_graph)
        cl = preprocess_query_graph(query_graph, nodemap, varmap, edgemap, constant_counts, utilities or {})
        checklist.append(cl)
        qlengths.append(len(cl))
    return checklist, qlengths


def preprocess_query_graph(graph, nodemap, varmap, edgemap, constant_counts, utilities):
    checklist = []
    variables = set()
    variables = {n for n in graph.nodes()
                 if 'var' in graph.data(n)
                 and graph.data(n)['var']}
    utilities = {**constant_counts, **utilities}
    for variable in variables:
        related = set(chain(graph.targets(variable), graph.sources(variable))) - variables
        utilities[variable] = utilities[min(related, key=lambda x: utilities[x])] * 2 if related else 10**9
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
        pq = [(root, trunk, rooted_edge)]
        while pq:
            s, t, l = pq.pop()
            if (s, t, l) in left_edges or (t, s, Rlabel(l)) in left_edges:
                left_edges.discard((s, t, l))
                left_edges.discard((t, s, Rlabel(l)))
                checklist.append((s, t, l))
                if t in left_nodes:
                    left_nodes.remove(t)
                    pq.extend(sorted(
                        chain(graph.out_edges(t), [(t_, s_, Rlabel(l_)) for s_, t_, l_ in graph.in_edges(t)]),
                        key=lambda e: utilities[e[1]],
                        reverse=True
                    ))
                    # for s_, t_, l_ in sorted(graph.out_edges(t),
                    #                          key=lambda e: 0 if e[1] in variables else 1 / constant_counts.get(e, 1)):
                    #     pq.append((s_, t_, l_))
                    # for s_, t_, l_ in sorted(graph.in_edges(t),
                    #                          key=lambda e: 0 if e[0] in variables else 1 / constant_counts.get(e, 1)):
                    #     pq.append((t_, s_, Rlabel(l_)))
            # if isinstance(l, Rlabel):
            #     left_edges.discard((t, s, Rlabel(l)))
            #     left_edges.discard((s, t, l))
            # else:
            #     left_edges.discard((s, t, l))
            #     left_edges.discard((t, s, Rlabel(l)))

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










