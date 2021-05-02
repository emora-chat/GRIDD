
from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph

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
        jlm1=like(john1=object(), mary1=object())
        jlm1{"c": -1}
        mls1=like(mary1, sally1=object())
        '''
        solutions = inference_engine.infer(facts, *rules)
        assert solutions_equal(solutions['trans_like'][2], [])


        # KB unsure test
        facts = '''
        jlm2=like(john2=object(), mary2=object())
        jlm2{"c": 0}
        mls2=like(mary2, sally2=object())
        '''
        solutions = inference_engine.infer(facts, *rules)
        assert solutions_equal(solutions['trans_like'][2], [])

        # Query negation test
        facts = '''
        jlm3=like(john3=object(), mary3=object())
        jlm3{"c": -0.6}
        mls3=like(mary3, sally3=object())
        jlk3=like(john3, kate3=object())
        jlk3{"c": -0.4}
        klt3=like(kate, tom3=object())
        '''
        rules = '''
        xly3=like(x3=object(), y3=object())
        xly3{"c": -0.5}
        ylz3=like(y3, z3=object())
        -> trans_like3 ->
        like(x3, z3)
        '''.split(';')

        solutions = inference_engine.infer(facts, *rules)

        assert solutions_equal(solutions['trans_like3'][2], [
            {'x3': 'john3', 'y3': 'mary3', 'z3': 'sally3', 'xly3': 'jlm3', 'ylz3': 'mls3'}
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

        implications = inference_engine.apply(inference_engine.infer(facts, *rules))

        assert concept_graphs_equal(
            implications['trans_like'][0][1],
            ConceptGraph('''
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