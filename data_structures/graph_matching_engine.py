
from GRIDD.data_structures.graph_matching_engine_spec import GraphMatchingEngineSpec

from GRIDD.utilities import IdNamespace
from collections import deque
from itertools import chain
import torch

class GraphMatchingEngine:

    def __init__(self):
        pass

    def match(self, data_graph, *query_graphs):
        query_graphs = list(query_graphs)
        for i, qg in enumerate(query_graphs):
            if isinstance(qg, tuple):
                qg, vars = qg
                query_graphs[i] = qg
                for var in vars:
                    qg.data(var)['var'] = True

        edge_ids = IdNamespace(namespace=int)

        data_node_ids = IdNamespace(data_graph.nodes(), namespace=int)

        attribute_ids = IdNamespace(data_node_ids, namespace=int)

        for node in data_graph.nodes():
            if 'attributes' in data_graph.data(node):
                for attribute in data_graph.data(node)['attributes']:
                    attribute_ids.get(attribute)

        data_edges = [(data_node_ids[s], data_node_ids[t], edge_ids.get(l))
                       for s, t, l in data_graph.edges()]
        query_node_ids = IdNamespace(namespace=int)
        for query_graph in query_graphs:
            for node in query_graph.nodes():
                query_node_ids.get((query_graph, node))
                attribute_ids.get(node)
                if 'attributes' in query_graph.data(node):
                    for attribute in query_graph.data(node)['attributes']:
                        attribute_ids.get(attribute)

        query_edges = list(chain(*[
            [[query_node_ids[q, s], query_node_ids[q, t], edge_ids.get(l)]
                for s, t, l in q.edges()] for q in query_graphs
        ]))

        num_labels = len(edge_ids)

        data_graph_adjacency = torch.sparse.LongTensor(
            torch.LongTensor(list(zip(*data_edges))),
            torch.ones(len(data_edges)),
            torch.Size([len(data_node_ids), len(data_node_ids), num_labels])
        )

        query_graphs_adjacency = torch.sparse.LongTensor(
            torch.LongTensor(list(zip(*query_edges))),
            torch.ones(len(query_edges)),
            torch.Size([len(query_node_ids), len(query_node_ids), num_labels])
        )

        data_node_attr_pairs = []
        for node in data_graph.nodes():
            data_node_attr_pairs.append((data_node_ids[node], attribute_ids[node]))
            if 'attributes' in data_graph.data(node):
                for attr in data_graph.data(node)['attributes']:
                    data_node_attr_pairs.append((data_node_ids[node], attribute_ids[attr]))

        data_attributes = torch.sparse.LongTensor(
            indices=torch.LongTensor(list(zip(*data_node_attr_pairs))),
            values=torch.ones(len(data_node_attr_pairs)),
            size=torch.Size([len(data_node_ids), len(attribute_ids)])
        )

        query_node_attr_pairs = []
        for query_graph in query_graphs:
            for node in query_graph.nodes():
                q = query_node_ids[(query_graph, node)]
                query_node_attr_pairs.append((q, attribute_ids[node]))
                if 'attributes' in query_graph.data(node):
                    for attr in query_graph.data(node)['attributes']:
                        query_node_attr_pairs.append((q, attribute_ids[attr]))

        query_attributes = torch.sparse.LongTensor(
            indices=torch.LongTensor(list(zip(*query_node_attr_pairs))),
            values=torch.ones(len(query_node_attr_pairs)),
            size=torch.Size([len(query_node_ids), len(attribute_ids)])
        )



        return




if __name__ == '__main__':
    print(GraphMatchingEngineSpec.verify(GraphMatchingEngine))