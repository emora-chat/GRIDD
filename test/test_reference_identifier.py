from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.reference_identifier import REFERENCES_BY_RULE

def test_referential_alignment_identification():
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
    assert set(REFERENCES_BY_RULE['obj_of_possessive'](car_span.to_string(), cg)) \
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