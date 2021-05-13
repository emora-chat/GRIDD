
import unittest


class ExpressionMatcher:

    def __init__(self, expressions):
        self.expressions = list(expressions) # feel free to modify

    def match(self, input):
        """
        input:      string to check for expressions
        returns:    matched, overlaps, contains

            matched: dictionary where keys are (start, end) int tuples and
                     values are str representing matched expression
            overlaps: dictionary where keys are (start, end) int tuples and
                      values are sets of (start, end) tuples representing
                      all matches that conflict/overlap with their key
            contains: dictionary where keys are (start, end) int tuples and
                      values are (start, end) tuples representing all matches
                      that are completely contained within their key.
        """
        raise NotImplementedError


class TestExpressionMatching(unittest.TestCase):

    def test_match_expressions(self):
        expressions = [
            'the fox and the hound',
            'fox',
            'hound',
            'felix the fox',
            'lone wolf'
        ]

        matcher = ExpressionMatcher(expressions)

        input = 'I saw Felix the fox and the Hound watching the fox and the hound.'

        matched, overlaps, contains = matcher.match(input)

        assert set(matched.values()) == {
            'the fox and the hound', 'fox', 'hound', 'felix the fox'
        }

        assert set(overlaps) > set(contains)

        '''
        Considerations:
        
        * Efficiency!! Please test with thousands or hundreds of thousands
          of expressions to ensure algorithm is efficient. Using a prefix 
          tree is highly recommended (lots of packages with fast string matching,
          just check license to make sure we can use).
          
          We want under 0.05s if possible. Run profiler before micro-optimizing (cProfile).
        
        '''