
from structpy import specification
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph

@specification
class GraphMatchingEngineSpec:

    @specification.init
    def GRAPH_MATCHING_ENGINE(GraphMatchingEngine):
        matcher = GraphMatchingEngine(device='cuda')
        return matcher

    def match(matcher, data_graph, query_graphs):
        """
        `data_graph` is a LabeledDigraph.

        `query_graph` is a LabeledDigraphData object with attribute
        `var=True` on each node that is a variable. All other nodes
        will be treated as instance nodes and must be matched exactly
        in the `data_graph`.

        You may provide `query_graph` objects as tuples where the first
        element is a LabeledDigraph and the second element is an iterable
        of the nodes that should be considered variables.

        Query graphs defining nodes with attributes in the set `eq, ne, gt, lt, ge, le`
        corresponding to int/float value `X` will only be assignable to nodes with an
        analagous attribute `num=Y` where the required comparison between `X` and `Y`
        is satisfied.

        Returns solutions as a `dict<query, list<dict<var, value>>`
        where `query` keys in the outer dict are the provided query
        objects, the value represents a list of solutions, where each
        solution is a dict mapping variables to values.
        """
        data_graph = Graph([
            ('mary', 'john', 'likes'),
            ('mary', 'sally', 'likes'),
            ('sally', 'john', 'likes'),
            ('john', 'tom', 'dislikes'),
            ('tom', 'john', 'dislikes'),
            ('tom', 'mary', 'likes'),
            ('sally', 'tom', 'dislikes'),
            ('john', 'mary', 'likes')
        ])

        for i in 'abcdefghijklmnopqrstuvwxyz'[:5]:
            for j in 'abcdefghijklmnopqrstuvwxyz'[:5]:
                for k in 'abcdefghijklmnopqrstuvwxyz'[:5]:
                    data_graph.add(i,j,k)

        query1 = Graph([
            ('A', 'B', 'likes'),
        ], nodes={
            'A': dict(var=True),
            'B': dict(var=True)
        })

        query2 = Graph([
            ('C', 'D', 'likes'),
            ('D', 'E', 'dislikes')
        ])

        query3 = Graph([
            ('X', 'Y', 'likes'),
            ('Y', 'Z', 'likes'),
            ('Z', 'X', 'likes')
        ])

        query4 = Graph(nodes=['F'])

        solutions = matcher.match(data_graph, query1, (query2, 'CDE'), (query3, 'XYZ'), (query4, 'F'))

        assert solutions_equal(
            solutions[query1],
            [
                {'A': 'mary', 'B': 'sally'},
                {'A': 'mary', 'B': 'john'},
                {'A': 'sally', 'B': 'john'},
                {'A': 'tom', 'B': 'mary'},
                {'A': 'john', 'B': 'mary'}
            ])

        assert solutions_equal(
            solutions[query2],
            [
                {'C': 'mary', 'D': 'john', 'E': 'tom'},
                {'C': 'mary', 'D': 'sally', 'E': 'tom'},
                {'C': 'sally', 'D': 'john', 'E': 'tom'}
            ])

        assert solutions_equal(
            solutions[query3],
            [
                {'X': 'mary', 'Y': 'sally', 'Z': 'john'},
                {'X': 'sally', 'Y': 'john', 'Z': 'mary'},
                {'X': 'john', 'Y': 'mary', 'Z': 'sally'}
            ])


        # assert solutions_equal(
        #     solutions[query4],
        #     [
        #         {'F': 'tom'},
        #         {'F': 'mary'},
        #         {'F': 'sally'},
        #         {'F': 'john'}
        #     ])

def solutions_equal(a, b):
    a_cmp = sorted([sorted(e.items()) for e in a])
    b_cmp = sorted([sorted(e.items()) for e in b])
    cmp = a_cmp == b_cmp
    return cmp