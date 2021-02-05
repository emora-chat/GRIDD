
from structpy import specification
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph


@specification
class GraphMatchingEngineSpec:

    @specification.init
    def GRAPH_MATCHING_ENGINE(GraphMatchingEngine):
        matcher = GraphMatchingEngine()
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
        ], nodes={
            'mary': dict(attributes={'leader'})
        })

        query1 = Graph([
            ('X', 'Y', 'likes'),
        ], nodes={
            'X': dict(var=True),
            'Y': dict(var=True)
        })

        query2 = Graph([
            ('X', 'Y', 'likes'),
            ('Y', 'Z', 'dislikes')
        ])

        query3 = Graph([
            ('X', 'Y', 'likes'),
            ('Y', 'Z', 'likes'),
            ('Z', 'Y', 'likes')
        ], nodes={
            'X': dict(attributes={'leader'})
        })

        solutions = matcher.match(data_graph, query1, (query2, 'XYZ'), (query3, 'XYZ'))

        assert solutions == {
            query1: [
                {'X': 'mary', 'Y': 'john'},
                {'X': 'mary', 'Y': 'sally'},
                {'X': 'sally', 'Y': 'john'},
                {'X': 'tom', 'Y': 'mary'},
                {'X': 'john', 'Y': 'mary'}
            ],
            query2: [
                {'X': 'mary', 'Y': 'john', 'Z': 'tom'},
                {'X': 'mary', 'Y': 'sally', 'Z': 'tom'},
                {'X': 'sally', 'Y': 'john', 'Z': 'tom'}
            ],
            query3: [
                {'X': 'mary', 'Y': 'sally', 'Z': 'john'},
                {'X': 'john', 'Y': 'mary', 'Z': 'sally'},
                {'X': 'sally', 'Y': 'john', 'Z': 'mary'}
            ]
        }
