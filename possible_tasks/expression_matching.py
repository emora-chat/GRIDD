import unittest
import time
from GRIDD.possible_tasks.trie import SpanMatcher
import string
import random

class ExpressionMatcher:

    def __init__(self, expressions):
        self.st = SpanMatcher(expressions)

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

        count = 0
        st = self.st
        m = {}
        o = {}
        c = {}
        tokens = input.lower().split()
        leng = 0
        a = st.findall(tokens,remove_subset=False, remove_overlap=False)
        for i in a:
            m[(i[1],i[2])] = i[0]
        for i in m.keys():
            o[i] = set()
            c[i] = set()
            for j in m.keys():
                if j == i:
                    continue
                if (j[0] <= i[0] and j[1] >= i[0]):
                    o[i].add(j)
                    #continue
                if (j[0] <= i[1] and j[1] >= i[1]):
                    if j not in o[i]: o[i].add(j)
                    #continue
                if (j[0] >= i[0] and j[1] <= i[1]):
                    if j not in o[i]: o[i].add(j)
                    c[i].add(j)
                    #continue
            if (len(o[i]) is 0):
                o.pop(i)
            if (len(c[i]) is 0):
                c.pop(i)
        return m, o, c

class TestExpressionMatching(unittest.TestCase):

    def test_match_expressions_aesop(self):
        expressions = [
            'town mouse',
            'mouse',
            'country mouse',
            'felix the fox',
            'lone wolf'
        ]
        letters = string.ascii_lowercase
        for i in range(1000000):
            expressions.append(''.join(random.choice(letters) for i in range(10))) #append a million 10-long random strings for stress test

        matcher = ExpressionMatcher(expressions)

        input = 'A Town Mouse once visited a relative who lived in the country. For lunch the Country Mouse served wheat stalks, roots, and acorns, with a dash of cold water for drink. The Town Mouse ate very sparingly, nibbling a little of this and a little of that, and by her manner making it very plain that she ate the simple food only to be polite. After the meal the friends had a long talk, or rather the Town Mouse talked about her life in the city while the Country Mouse listened. They then went to bed in a cozy nest in the hedgerow and slept in quiet and comfort until morning. In her sleep the Country Mouse dreamed she was a Town Mouse with all the luxuries and delights of city life that her friend had described for her. So the next day when the Town Mouse asked the Country Mouse to go home with her to the city, she gladly said yes. When they reached the mansion in which the Town Mouse lived, they found on the table in the dining room the leavings of a very fine banquet. There were sweetmeats and jellies, pastries, delicious cheeses, indeed, the most tempting foods that a Mouse can imagine. But just as the Country Mouse was about to nibble a dainty bit of pastry, she heard a Cat mew loudly and scratch at the door. In great fear the Mice scurried to a hiding place, where they lay quite still for a long time, hardly daring to breathe. When at last they ventured back to the feast, the door opened suddenly and in came the servants to clear the table, followed by the House Dog. The Country Mouse stopped in the Town Mouses den only long enough to pick up her carpet bag and umbrella.'
        t1 = time.time()
        matched, overlaps, contains = matcher.match(input)
        t2 = time.time()
        print(f"\nTime Taken: {t2 - t1}")
        assert set(matched.values()) == {
            'town mouse', 'mouse', 'country mouse'
        }

        assert set(overlaps) > set(contains)

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
        t1 = time.time()
        matched, overlaps, contains = matcher.match(input)
        t2 = time.time()
        print(f"Time Taken: {t2 - t1}")
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
