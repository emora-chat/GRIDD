
import random

from GRIDD.data_structures.graph_matching.reverse_label import ReverseLabel as Rlabel
from GRIDD.data_structures.graph_matching.root import root, rooted_edge


def preprocess_query_graph(graph, nodemap, varmap, edgemap):
    checklist = []
    if isinstance(graph, tuple):
        graph, variables = graph
    else:
        variables = set()
    variables = set(variables)
    variables.update({n for n in graph.nodes()
                      if 'var' in graph.data(n)
                      and graph.data(n)['var']})
    constants = set(graph.nodes()) - variables
    left_nodes = set(graph.nodes())
    left_edges = set(graph.edges())
    while left_nodes:
        left_constants = left_nodes & constants
        if left_constants:
            trunk = random.choice(list(left_constants))
        else:
            trunk = random.choice(list(left_nodes))
        left_edges.add((root, trunk, rooted_edge))
        stack = [(root, trunk, rooted_edge)]
        while stack:
            s, t, l = stack.pop()
            if (s, t, l) not in left_edges and (t, s, Rlabel(l)) not in left_edges:
                continue
            if isinstance(l, Rlabel):
                left_edges.remove((t, s, Rlabel(l)))
            else:
                left_edges.remove((s, t, l))
            checklist.append((s, t, l))
            if t in left_nodes:
                left_nodes.remove(t)
                for s_, t_, l_ in sorted(graph.out_edges(t),
                                         key=lambda e: 0 if e[1] in variables else 1):
                    stack.append((s_, t_, l_))
                for s_, t_, l_ in sorted(graph.in_edges(t),
                                         key=lambda e: 0 if e[0] in variables else 1):
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










