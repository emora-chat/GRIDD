
from structpy import specification
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_graph import ConceptGraph

def alignment_ref(ref_span_node, data_dict):
    cg = data_dict['dependency_parse_cg']
    frontier = [ref_span_node]
    subtree = set()
    while len(frontier) > 0:
        node = frontier.pop(0)
        for s,t,o,i in cg.predicates(node):
            if t != 'type':
                frontier.append(o)
                subtree.add(o)
    return subtree

REFERENCES_BY_RULE = {
    'obj_of_possessive': alignment_ref,
    'ref_concept_determiner': alignment_ref,
    'ref_determiner': alignment_ref
}

@specification
class ReferenceIdentifierSpec:

    @specification.init
    def REFERENCE_IDENTIFIER(ReferenceIdentifier, identify_by_rule):
        ref_identifier = ReferenceIdentifier(REFERENCES_BY_RULE)
        return ref_identifier

    def identify(ref_identifier, rule, span, data_dict):
        """
        Returns a list of spans that are identified as the constraints of the argument `span`
        based on `rule` and the provided `data_dict`
        """
        # Test referential alignment gather
        i_span = Span('i', 0, 1, 0, 0, 1)
        like_span = Span('like', 1, 2, 0, 0, 1)
        my_span = Span('my', 2, 3, 0, 0, 1)
        very_span = Span('very', 3, 4, 0, 0, 1)
        red_span = Span('red', 4, 5, 0, 0, 1)
        car_span = Span('car', 5, 6, 0, 0, 1)
        cg = ConceptGraph(predicates=[
            (like_span.to_string(), 'nsbj', i_span.to_string()),
            (like_span.to_string(), 'obj', car_span.to_string()),
            (car_span.to_string(), 'poss', my_span.to_string()),
            (car_span.to_string(), 'attr', red_span.to_string()),
            (red_span.to_string(), 'adv', very_span.to_string())
        ])
        data = {'dependency_parse_cg': cg}
        assert ref_identifier.identify('obj_of_possessive', car_span.to_string(), data) \
               == {my_span.to_string(), very_span.to_string(), red_span.to_string()}

        # test: the man who bought a car
        # test: the man with red hair

        # Test y/n question gather
        # did_span = Span('did', 0, 1, 0, 0, 1)
        # you_span = Span('you', 1, 2, 0, 0, 1)
        # like_span = Span('like', 2, 3, 0, 0, 1)
        # the_span = Span('the', 3, 4, 0, 0, 1)
        # movie_span = Span('movie', 4, 5, 0, 0, 1)
        # cg = ConceptGraph(predicates=[
        #     (like_span.to_string(), 'nsbj', you_span.to_string()),
        #     (like_span.to_string(), 'obj', movie_span.to_string()),
        #     (movie_span.to_string(), 'det', the_span.to_string()),
        #     (like_span.to_string(), 'aux', did_span.to_string())
        # ])
        # assert ref_identifier.identify('q_aux_do_past', did_span.to_string(), cg) == \
        #        {did_span.to_string()}

        # Test concept question gather