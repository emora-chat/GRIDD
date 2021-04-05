
from structpy import specification
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.id_map import IdMap

@specification
class ReferenceGathererSpec:

    @specification.init
    def REFERENCE_GATHERER(ReferenceGatherer):
        ref_gatherer = ReferenceGatherer()
        return ref_gatherer

    def gather(ref_gatherer, reference_node, constraints_as_spans, concept_graph):
        """
        'reference_node' is the node that is a reference.

        `constraints_as_spans` is a set of span strings that are constraints.

        `concept_graph` is a concept_graph containing all mentions.

        Return a set of predicates corresponding to the constraints of `reference_node`
        based on the `concept_graph`.

        The returned predicates should enumerate the contentful predicates defining the reference,
        and exclude the framework primitives (`focus`, `center`, `cover`, `question`, `var`)
        """
        my_span = Span('my', 'my', 2, 3, 0, 0, 1)
        very_span = Span('very', 'very', 3, 4, 0, 0, 1)
        red_span = Span('red', 'red', 4, 5, 0, 0, 1)
        car_span = Span('car', 'car', 5, 6, 0, 0, 1)
        graph = ConceptGraph(predicates=[
            ('user', 'possess', 'c1', 'upc'),
            ('c1', 'type', 'car', 'ctc'),
            ('user', 'like', 'c1', 'ulc'),
            ('c1', 'property', 'red', 'cpr'),
            ('cpr', 'property', 'very', 'rpv'),
            ('u1', 'type', 'extra', 'extra1'),
            ('c1', 'focus', None, 'prim1'),
            (my_span.to_string(), 'ref', 'upc'),
            (very_span.to_string(), 'ref', 'rpv'),
            (red_span.to_string(), 'ref', 'cpr'),
            (car_span.to_string(), 'ref', 'c1')
        ])
        graph.features['upc']['comps'] = set()
        graph.features['rpv']['comps'] = set()
        graph.features['cpr']['comps'] = {'prim1'}
        graph.features['c1']['comps'] = {'ctc', 'extra1'}
        constraints_as_spans = {my_span.to_string(), very_span.to_string(),
                                red_span.to_string()}

        assert ref_gatherer.gather('c1', constraints_as_spans, graph) == \
               {'upc', 'rpv', 'cpr', 'ctc'}
