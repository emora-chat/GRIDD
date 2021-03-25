
from structpy import specification

from GRIDD.data_structures.knowledge_parser import KnowledgeParser
import time

@specification
class InferenceEngineSpec:

    @specification.init
    def INFERENCE_ENGINE(InferenceEngine, rules):
        """
        `rules` are preloaded and checked on every `infer` call.

        `rules` is a variable number of rules where the rule can be:
            logic string of SINGLE rule
            rule concept id in concept graph
            tuple of concept graphs (precondition, postcondition, name(optional))

        """
        rules = '''
        alb=like(a=object(), b=object())
        -> like_happy ->
        happy(b)
        '''.split(';')

        inference_engine = InferenceEngine(*rules)
        return inference_engine

    def infer(inference_engine, facts, rules):
        """
        `facts` define a graph against which the rule preconditions will be checked for matches.

        `facts` can be a concept graph or a logic string.

        Same `rules` format as constructor.

        Returns dictionary mapping rules to their solutions.
        """

        facts = '''
        jlm=like(john=object(), mary=object())
        mls=like(mary, sally=object())
        '''

        rules = '''
        xly=like(x=object(), y=object())
        ylz=like(y, z=object())
        -> trans_like ->
        like(x, z)
        '''.split(';')

        solutions = inference_engine.infer(facts, *rules)

        assert solutions_equal(solutions['like_happy'][2], [
                {'a': 'john', 'b': 'mary', 'alb': 'jlm'},
                {'a': 'mary', 'b': 'sally', 'alb': 'mls'}
            ]
        )

        assert solutions_equal(solutions['trans_like'][2], [
            {'x': 'john', 'y': 'mary', 'z': 'sally', 'xly': 'jlm', 'ylz': 'mls'}
        ])


        # KB negation test
        facts = '''
        jlm=like(john=object(), mary=object())
        jlm{"c": -1}
        mls=like(mary, sally=object())
        '''
        solutions = inference_engine.infer(facts, *rules)
        assert solutions_equal(solutions['trans_like'][2], [])


        # KB unsure test
        facts = '''
        jlm=like(john=object(), mary=object())
        jlm{"c": 0}
        mls=like(mary, sally=object())
        '''
        solutions = inference_engine.infer(facts, *rules)
        assert solutions_equal(solutions['trans_like'][2], [])

        # Query negation test
        facts = '''
        jlm=like(john=object(), mary=object())
        jlm{"c": -0.6}
        mls=like(mary, sally=object())
        jlk=like(john=object(), kate=object())
        jlk{"c": -0.4}
        klt=like(kate, tom=object())
        '''
        rules = '''
        xly=like(x=object(), y=object())
        xly{"c": -0.5}
        ylz=like(y, z=object())
        -> trans_like ->
        like(x, z)
        '''.split(';')

        solutions = inference_engine.infer(facts, *rules)

        assert solutions_equal(solutions['trans_like'][2], [
            {'x': 'john', 'y': 'mary', 'z': 'sally', 'xly': 'jlm', 'ylz': 'mls'}
        ])


    def apply(inference_engine, facts=None, rules=None, solutions=None):
        """
        If facts and rules are provided, run `infer` to get solutions and then generate the postconditions.

        Same `rules` format as constructor.

        If solutions are provided, generate the postconditions.

        Returns list of generated postconditions.
        """

        facts = '''
        jlm=like(john=object(), mary=object())
        mls=like(mary, sally=object())
        '''

        rules = '''
        xly=like(x=object(), y=object())
        ylz=like(y, z=object())
        -> trans_like ->
        like(x, z)
        '''.split(';')

        implications = inference_engine.apply(facts, *rules)

        assert concept_graphs_equal(
            implications['trans_like'][0],
            KnowledgeParser.from_data('''
            like(john, sally);
            ''')
        )

def solutions_equal(a, b):
    a_cmp = sorted([sorted(e.items()) for e in a])
    b_cmp = sorted([sorted(e.items()) for e in b])
    cmp = a_cmp == b_cmp
    return cmp

def concept_graphs_equal(a, b):
    return frozenset([(s,t,o) for s, t, o, i in a.predicates()]) \
        == frozenset([(s,t,o) for s, t, o, i in b.predicates()])