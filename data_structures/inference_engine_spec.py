
from structpy import specification

from GRIDD.data_structures.concept_graph import ConceptGraph
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
        =>
        happy(b)
        '''.split(';')

        inference_engine = InferenceEngine(*rules)
        return inference_engine

    def infer(inference_engine, facts, rules):
        """
        `facts` define a graph against which the rule preconditions will be checked for matches.

        `facts` can be a concept graph or a logic string.

        Same `rules` format as constructor.

        If no rules are provided, then all rules present in the concept graph will be applied.

        Returns dictionary mapping rules to their solutions.
        """

        facts = '''
        jlm=like(john=object(), mary=object())
        mls=like(mary, sally=object())
        '''

        rules = '''
        xly=like(x=object(), y=object())
        ylz=like(y, z=object())
        =>
        like(x, z)
        '''.split(';')

        t = time.time()
        solutions = inference_engine.infer(facts, *rules)
        print('Elapsed: %.3f'%(time.time()-t))

        assert solutions_equal(solutions[list(inference_engine.rules.keys())[0]], [
                {'a': 'john', 'b': 'mary', 'alb': 'jlm'},
                {'a': 'mary', 'b': 'sally', 'alb': 'mls'}
            ]
        )

        assert solutions_equal(solutions[rules[0]], [
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
        =>
        like(x, z)
        '''.split(';')

        implications = inference_engine.apply(facts, *rules)

        assert concept_graphs_equal(
            implications[rules[0]][0],
            ConceptGraph('''
            like(john, sally)
            ''')
        )

def solutions_equal(a, b):
    a_cmp = sorted([sorted(e.items()) for e in a])
    b_cmp = sorted([sorted(e.items()) for e in b])
    cmp = a_cmp == b_cmp
    return cmp

def concept_graphs_equal(a, b):
    return False