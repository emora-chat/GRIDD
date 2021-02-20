
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_graph import ConceptGraph

def test_determiner_parse_graph_matching():
    pre = ConceptGraph([
        ('A', 'det', 'C', 'B'),
        ('A', 'ref', 'I', 'H'),
        ('I', 'expr', 'K', 'J'),
        ('C', 'ref', 'E', 'D'),
        ('E', 'expr', 'G', 'F'),
        ('A', 'type', 'pos'),
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
        ('noun', 'type', 'pos'),
        ('c', 'type', 'dt'),
        ('g', 'type', 'inst_det')
    ])

    ie = InferenceEngine(device='cuda')
    solutions = ie.infer(pg, (pre, ConceptGraph(), 'determiner'))
    return solutions

if __name__ == '__main__':
    for rule_id, (pre, post, sols) in test_determiner_parse_graph_matching().items():
        print(rule_id)
        for sol in sols:
            print(sol)
            print()
        print('-'*20)


