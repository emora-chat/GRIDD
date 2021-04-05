
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_parser import KnowledgeParser

def test_determiner_parse_graph_matching():
    pre = ConceptGraph([
        ('A', 'det', 'C', 'B'),
        ('A', 'ref', 'I', 'H'),
        ('I', 'expr', 'K', 'J'),
        ('C', 'ref', 'E', 'D'),
        ('E', 'expr', 'G', 'F'),
        ('A', 'type', 'pstg'),
        ('C', 'type', 'dt'),
        ('G', 'type', 'inst_det')
    ])
    for var in 'ABCDEFGHIJK':
        pre.add(var, 'var')

    pg = ConceptGraph([
        ('a', 'det', 'c', 'b'),
        ('a', 'ref', 'i', 'h'),
        ('i', 'expr', 'k', 'j'),
        ('c', 'ref', 'e', 'd'),
        ('e', 'expr', 'g', 'f'),
        ('a', 'type', 'nn'),
        ('nn', 'type', 'noun'),
        ('noun', 'type', 'pstg'),
        ('c', 'type', 'dt'),
        ('g', 'type', 'inst_det')
    ])

    ie = InferenceEngine(device='cuda')
    solutions = ie.infer(pg, (pre, ConceptGraph(), 'determiner'))
    return solutions

def test_adv_question_parse_graph_matching():
    preds = [
        ('A', 'adv', 'B', 'C'),
        ('B', 'ref', 'D', 'E'),
        ('D', 'expr', 'F', 'G'),
        ('A', 'aux', 'H', 'I'),
        ('H', 'ref', 'J', 'K'),
        ('J', 'expr', 'L', 'M'),
        ('A', 'nsbj', 'N', 'O'),
        ('N', 'ref', 'P', 'Q'),
        ('P', 'expr', 'R', 'S'),
        ('A', 'ref', 'T', 'U'),
        ('T', 'expr', 'V', 'W'),
        ('B', 'precede', 'H', 'X'),
        ('H', 'precede', 'N', 'Y'),
        ('A', 'type', 'pstg', 'AA'),
        ('B', 'type', 'question_word', 'BB'),
        ('H', 'type', 'pstg', 'HH'),
        ('N', 'type', 'pstg', 'NN')
    ]
    pre = ConceptGraph(preds)
    for var in 'ABCDEFGHIJKLMNOPQRSTUVWXY':
        pre.add(var, 'var')

    l = '''
    adv(X/pos(), Y/question_word())
	aux(X, Z/pos())
	nsbj(X, A/pos())
	precede(Y, Z)
	precede(Z, A)
	-> q_nadv ->
	p/Y(X, o/object())
	question(user, o)
	focus(p)
	center(Y)
	cover(Z)
	;
    '''
    pre_from_parse = KnowledgeParser.rules(l)

    pg = ConceptGraph([(s.lower(),t,o.lower(),i.lower()) for s,t,o,i in preds])

    ie = InferenceEngine(device='cuda')
    solutions = ie.infer(pg, (pre_from_parse['q_nadv'][0], ConceptGraph(), 'q_nadv'))
    return solutions

def test_lone_comp():
    rule = '''
    comp(X/pos(), Y/pos())
    -> lone_comp ->
    p/property(X, Y)
	focus(p)
	center(Y)
    ;
    '''
    pre_from_parse = KnowledgeParser.rules(rule)

    preds = [
        ('A', 'adv', 'B', 'C'),
        ('B', 'ref', 'D', 'E'),
        ('D', 'expr', 'F', 'G'),
        ('A', 'aux', 'H', 'I'),
        ('H', 'ref', 'J', 'K'),
        ('J', 'expr', 'L', 'M'),
        ('A', 'nsbj', 'N', 'O'),
        ('N', 'ref', 'P', 'Q'),
        ('P', 'expr', 'R', 'S'),
        ('A', 'ref', 'T', 'U'),
        ('T', 'expr', 'V', 'W'),
        ('B', 'precede', 'H', 'X'),
        ('H', 'precede', 'N', 'Y'),
        ('A', 'type', 'pstg', 'AA'),
        ('B', 'type', 'question_word', 'BB'),
        ('H', 'type', 'pstg', 'HH'),
        ('N', 'type', 'pstg', 'NN')
    ]

    pg = ConceptGraph([(s.lower(),t,o.lower(),i.lower()) for s,t,o,i in preds])

    ie = InferenceEngine(device='cuda')
    solutions = ie.infer(pg, (pre_from_parse['q_nadv'][0], ConceptGraph(), 'q_nadv'))
    return solutions


if __name__ == '__main__':
    for rule_id, (pre, post, sols) in test_adv_question_parse_graph_matching().items():
        print(rule_id)
        for sol in sols:
            print(sol)
            print()
        print('-'*20)


