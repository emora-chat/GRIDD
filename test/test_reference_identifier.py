from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.reference_identifier import REFERENCES_BY_RULE

def test_referential_alignment():
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

def test_yn_question_reference():
    did_span = Span('did', 0, 1, 0, 0, 1)
    you_span = Span('you', 1, 2, 0, 0, 1)
    like_span = Span('like', 2, 3, 0, 0, 1)
    the_span = Span('the', 3, 4, 0, 0, 1)
    movie_span = Span('movie', 4, 5, 0, 0, 1)
    cg = ConceptGraph(predicates=[
        (like_span.to_string(), 'nsbj', you_span.to_string()),
        (like_span.to_string(), 'obj', movie_span.to_string()),
        (movie_span.to_string(), 'det', the_span.to_string()),
        (like_span.to_string(), 'aux', did_span.to_string())
    ])
    assert set(REFERENCES_BY_RULE['q_aux_do_past'](did_span.to_string(), cg)) \
           == {you_span.to_string(), like_span.to_string(), the_span.to_string(), movie_span.to_string()}

    i_span = Span('i', 0, 1, 0, 0, 1)
    was_span  = Span('was', 1, 2, 0, 0, 1)
    wondering_span  = Span('wondering', 2, 3, 0, 0, 1)
    are_span = Span('are', 0, 1, 0, 0, 1)
    you_span = Span('you', 1, 2, 0, 0, 1)
    a_span = Span('a', 2, 3, 0, 0, 1)
    student_span = Span('student', 3, 4, 0, 0, 1)
    in_span = Span('in', 4, 5, 0, 0, 1)
    college_span = Span('college', 5, 6, 0, 0, 1)

    cg = ConceptGraph(predicates=[
        (wondering_span.to_string(), 'nsbj', i_span.to_string()),
        (wondering_span.to_string(), 'aux', was_span.to_string()),
        (wondering_span.to_string(), 'comp', student_span.to_string()),
        (student_span.to_string(), 'nsbj', you_span.to_string()),
        (student_span.to_string(), 'cop', are_span.to_string()),
        (student_span.to_string(), 'det', a_span.to_string()),
        (student_span.to_string(), 'ppmod', college_span.to_string()),
        (college_span.to_string(), 'case', in_span.to_string())
    ])

    assert set(REFERENCES_BY_RULE['q_sbj_copula_present'](student_span.to_string(), cg)) \
           == {are_span.to_string(), you_span.to_string(), a_span.to_string(),
               in_span.to_string(), college_span.to_string()}

    i_span = Span('i', 0, 1, 0, 0, 1)
    was_span  = Span('was', 1, 2, 0, 0, 1)
    wondering_span  = Span('wondering', 2, 3, 0, 0, 1)
    did_span = Span('did', 4, 5, 0, 0, 1)
    you_span = Span('you', 5, 6, 0, 0, 1)
    like_span = Span('like', 6, 7, 0, 0, 1)
    the_span = Span('the', 7, 8, 0, 0, 1)
    movie_span = Span('movie', 8, 9, 0, 0, 1)
    cg = ConceptGraph(predicates=[
        (wondering_span.to_string(), 'nsbj', i_span.to_string()),
        (wondering_span.to_string(), 'aux', was_span.to_string()),
        (wondering_span.to_string(), 'comp', like_span.to_string()),
        (like_span.to_string(), 'nsbj', you_span.to_string()),
        (like_span.to_string(), 'obj', movie_span.to_string()),
        (movie_span.to_string(), 'det', the_span.to_string()),
        (like_span.to_string(), 'aux', did_span.to_string())
    ])
    assert set(REFERENCES_BY_RULE['q_aux_do_past'](did_span.to_string(), cg)) \
           == {you_span.to_string(), like_span.to_string(), the_span.to_string(),
               movie_span.to_string()}
