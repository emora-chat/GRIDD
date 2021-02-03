
from GRIDD.utilities import IdNamespace
from GRIDD.data_structures.tree import Tree
from collections import deque
import torch


class GraphMatchingEngine:

    def match(self, data_graph, *query_graphs):
        query_trees, single_node_queries, edge_map = self.query_to_trees(*query_graphs)


    def query_to_trees(self, *query_graphs):
        queries = []  # (query tree, query graph, node map of tree_node: graph_node)
        single_node_queries = []  # query tree of single node
        edge_map = IdNamespace('__edge__')  # (actual_label, reversed?): fabricated_label
        for query_graph in query_graphs:
            trees = []
            all_visited = set()  # nodes from the query not yet organized into some query tree
            while all_visited != set(query_graph.nodes()):
                node_ids = IdNamespace('__node__')
                node_map = {}  # map to construct of tree_node: query_node
                root = list(set(query_graph.nodes()) - all_visited)[0]
                root_id = node_ids.get()
                tree = Tree(root_id)  # query tree to construct
                node_map[root_id] = root
                visited = set()  # nodes visited in the traversal
                q = deque([root_id])  # frontier
                while q:
                    expanding = q.popleft()
                    if expanding not in visited:
                        visited.add(expanding)
                        for s, t, l in query_graph.out_edges(expanding):
                            t_ = node_ids.get()
                            l_ = edge_map.get((l, False))
                            tree.add(s, t_, l_)
                            node_map[t_] = t
                        for s, t, l in query_graph.in_edges(expanding):
                            s_ = node_ids.get()
                            l_ = edge_map.get((l, True))
                            tree.add(s_, t, l_)
                            node_map[s_] = s
                all_visited |= set(node_map.values())
            for tree, node_map in trees:
                if len(tree.edges()) > 1:
                    queries.append((tree, query_graph, node_map))
                else:
                    single_node_queries.append((tree, query_graph, node_map))
        return queries, single_node_queries, edge_map


