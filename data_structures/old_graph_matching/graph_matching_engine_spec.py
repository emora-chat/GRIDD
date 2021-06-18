
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
        ], nodes={
            'mary': dict(attributes={'leader'}, num=2),
            'tom': dict(attributes={'leader'}, num=4),
            'sally': dict(num=6),
        })

        query1 = Graph([
            ('A', 'B', 'likes'),
        ], nodes={
            'A': dict(var=True, gt=1, le=5),
            'B': dict(var=True, gt=3, le=9.3)
        })

        query2 = Graph([
            ('C', 'D', 'likes'),
            ('D', 'E', 'dislikes')
        ])

        query3 = Graph([
            ('X', 'Y', 'likes'),
            ('Y', 'Z', 'likes'),
            ('Z', 'X', 'likes')
        ], nodes={
            'X': dict(attributes={'leader'})
        })

        query4 = Graph(nodes={
            'F': dict(attributes={'leader'})
        })

        query5 = Graph([
            ('G', 'H', 'likes')
        ], nodes={
            'G': dict(attributes={'leader'}),
            'H': dict(attributes={'leader'})
        })

        solutions = matcher.match(data_graph, query1, (query2, 'CDE'), (query3, 'XYZ'), (query4, 'F'), (query5, 'GH'))

        assert solutions_equal(
            solutions[query1],
            [
                {'A': 'mary', 'B': 'sally'}
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
                {'X': 'mary', 'Y': 'sally', 'Z': 'john'}
            ])

        assert solutions_equal(
            solutions[query4],
            [
                {'F': 'tom'},
                {'F': 'mary'}
            ])

        assert solutions_equal(
            solutions[query5],
            [
                {'G': 'tom', 'H': 'mary'}
            ])

    def match_predicate(matcher):
        data = Graph([
            ('wm0', 'fido', 's'), ('wm0', 'fluffy', 'o'), ('wm0', 'chase', 't')
        ], nodes={
            'wm0': dict(attributes={'wm0', 'chase', 'predicate'}),
            'fido': dict(attributes={'fido', 'dog', 'animal'}),
            'fluffy': dict(attributes={'fluffy', 'cat', 'animal'}),
            'chase': dict(attributes={'chase'})
        })
        query = Graph([
            ('I', 'X', 's'), ('I', 'Y', 'o'), ('I', 'chase', 't'),
        ], nodes={
            'I': dict(attributes={'chase'}, var=True),
            'X': dict(attributes={'animal'}, var=True),
            'Y': dict(attributes={'animal'}, var=True),
            'chase': dict(attributes={'chase'})
        })
        solutions = matcher.match(data, query)
        assert solutions_equal(solutions[query], [{'I': 'wm0', 'X': 'fido', 'Y': 'fluffy'}])

def solutions_equal(a, b):
    a_cmp = sorted([sorted(e.items()) for e in a])
    b_cmp = sorted([sorted(e.items()) for e in b])
    cmp = a_cmp == b_cmp
    return cmp