from GRIDD.data_structures.graph_matching_engine import GraphMatchingEngine
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph
import random as r
from time import time
from itertools import chain
from structpy.map import Function
import inspect
import torch

def test_graph_matching_efficiency(
        data_edges,         # number of edges in data graph
        queries,            # total number of query graphs
        query_edges,        # number of edges per query graph
        solutions,          # total number of solutions
        query_solutions,    # number of solutions per query graph
        near_solutions,     # total number of near-solutions
        query_vars,         # number of variables per query
        attributes,         # total number of attributes
        data_attributes,    # number of attributes per data node
        query_attributes,   # number of attributes per query node
        nodes,              # total number of unique node ids
        query_nodes,        # total number of query node ids
        filter_iterations,  # number of edge filtering iterations
        device='cuda'       # hardware
):
    print('\n' + '#' * 80)
    args = dict(inspect.getargvalues(inspect.currentframe()).locals)
    print('Generating query graphs...')
    query_graphs = generate_queries(queries, query_edges, query_vars, attributes, query_attributes, query_nodes)
    print('Generating data graph...')
    solution_assignments = generate_solutions(query_graphs, solutions, query_solutions, attributes, data_attributes, nodes)
    data_graph = generate_data_graph(solution_assignments, data_edges, attributes, data_attributes, nodes)
    matching_engine = GraphMatchingEngine(device=device)
    print('Running inference on {}...'.format(matching_engine.device))
    t_i = time()
    solutions = matching_engine.match(data_graph, *query_graphs, limit=filter_iterations)
    t_f = time()
    print('Inference completed in {:.5f} seconds.'.format(t_f - t_i))
    print('Memory utilization:', str(torch.cuda.memory_stats()['allocated_bytes.all.peak'] / 10 ** 6), 'MB')
    print('\nArgs:')
    for k, v in args.items():
        print(k, '=', v)
    print('#'*80+'\n')
    return

def generate_queries(queries, query_edges, query_vars, attributes, query_attributes, query_nodes):
    gs = []
    for i in range(queries):
        qe = [generate_edge(query_nodes) for _ in range(query_edges // 2)]   # list of (subject, relation, object)
        g = Graph([(qe[0][1], qe[0][0], 's'), (qe[0][1], qe[0][2], 'o')])
        for e in qe[1:]:
            merger = r.randint(0, 1)
            e[merger] = r.choice(list(g.nodes()))
            g.add(e[1], e[0], 's')
            g.add(e[1], e[2], 'o')
        qa = generate_attributes(attributes, query_attributes, *list(g.nodes()))  # query_node: set of attributes
        for n, a in qa.items():
            g.data(n)['attributes'] = a
        qv = r.sample(list(qa), query_vars) if len(qa) > query_vars else set(qa)  # set of query nodes that are vars
        for v in qv:
            g.data(v)['var'] = True
        gs.append(g)
    return gs

def generate_solutions(query_graphs, solutions, query_solutions, attributes, data_attributes, nodes):
    solved = {qg: [] for qg in query_graphs}
    num_solved_queries = solutions // query_solutions
    qgs = {qg: 1 for qg in r.sample(query_graphs, num_solved_queries)}      # query_graph: num_solutions
    if qgs:
        qgkeys = list(qgs.keys())
        for _ in range(solutions - len(qgs)):
            qgs[r.choice(qgkeys)] += 1
    for qg, num_sols in qgs.items():
        for _ in range(num_sols):
            var_assignment = Function({qn: r.randint(0, nodes) if 'var' in qg.data(qn) else qn for qn in qg.nodes()})
            attrs = {}
            for var, val in var_assignment.items():
                if 'var' in qg.data(var):
                    attrs[val] = qg.data(var)['attributes']
                else:
                    attrs[val] = generate_attributes(attributes, data_attributes, val, subset=qg.data(var)['attributes'])[val]
            g = Graph()
            for s, t, l in qg.edges():
                g.add(var_assignment.get(s, s), var_assignment.get(t, t), l)
            for n, attr in attrs.items():
                g.data(n)['attributes'] = attr
            solved[qg].append((g, var_assignment))
    return solved

def generate_near_solutions():
    pass

def generate_data_graph(solution_graphs, data_edges, attributes, data_attributes, nodes):
    data_graph = Graph()
    solution_graphs = list(chain(*solution_graphs.values()))
    for g, _ in solution_graphs:
        for n in g.nodes():
            data_graph.add(n)
            data_graph.data(n)['attributes'] = g.data(n)['attributes']
        for e in g.edges():
            data_graph.add(*e)
    current_edges = len(data_graph.edges())
    for _ in range(data_edges - current_edges):
        e = generate_edge(nodes)
        for _ in range(2):
            merger = r.randint(0, 1)
            e[merger] = r.choice(list(data_graph.nodes())) if len(list(data_graph.nodes())) else r.randint(0, nodes)
        data_graph.add(e[1], e[0], 's')
        data_graph.add(e[1], e[2], 'o')
    da = generate_attributes(attributes, data_attributes, *data_graph.nodes())
    for n, a in da.items():
        if 'attributes' not in data_graph.data(n):
            data_graph.data(n)['attributes'] = a
    return data_graph

def generate_edge(nodes, sub=None, rel=None, obj=None):
    edge = [x if x is not None else r.randint(0, nodes) for x in (sub, rel, obj)]
    while len(set(edge)) < 3:
        edge = [x if x is not None else r.randint(0, nodes) for x in (sub, rel, obj)]
    return edge

def generate_attributes(attributes, node_attributes, *nodes, subset=None):
    attrs = {}
    for node in nodes:
        if subset is not None:
            attr = subset
        else:
            attr = set()
        attr = attr | {r.randint(0, attributes) for _ in range(node_attributes - len(attr))}
        while len(attr) != node_attributes:
            attr.add(r.randint(0, attributes))
        attrs[node] = attr
    return attrs

if __name__ == '__main__':
    test_graph_matching_efficiency(
        data_edges=200,
        queries=1000,
        query_edges=6,
        solutions=10,
        query_solutions=2,
        near_solutions=0,
        query_vars=5,
        attributes=10,
        data_attributes=3,
        query_attributes=1,
        nodes=50,
        query_nodes=1000,
        filter_iterations=10
    )
    print('done')