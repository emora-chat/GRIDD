import unittest
from suffix_trees import STree
import time


class ExpressionMatcher:

    def __init__(self, expressions):
        self.expressions = list(expressions)  # feel free to modify

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
        st = STree.STree(input.lower())
        m = {}
        o = {}
        c = {}
        for i in self.expressions:
            for j in st.find_all(i):
                m[(j, j + len(i))] = i
        for i in m.keys():
            o[i] = set()
            c[i] = set()
            for j in m.keys():
                if j == i:
                    continue
                if (j[0] < i[0] and j[1] > i[0]):
                    o[i].add(j)
                    continue
                if (j[0] < i[1] and j[1] > i[1]):
                    o[i].add(j)
                    continue
                if (j[0] > i[0] and j[1] < i[1]):
                    o[i].add(j)
                    c[i].add(j)
                    continue
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
            'lone wolf',
            'aaaa0',
            'aaaa1',
            'aaaa2',
            'aaaa3',
            'aaaa4',
            'aaaa5',
            'aaaa6',
            'aaaa7',
            'aaaa8',
            'aaaa9',
            'aaaa10',
            'aaaa11',
            'aaaa12',
            'aaaa13',
            'aaaa14',
            'aaaa15',
            'aaaa16',
            'aaaa17',
            'aaaa18',
            'aaaa19',
            'aaaa20',
            'aaaa21',
            'aaaa22',
            'aaaa23',
            'aaaa24',
            'aaaa25',
            'aaaa26',
            'aaaa27',
            'aaaa28',
            'aaaa29',
            'aaaa30',
            'aaaa31',
            'aaaa32',
            'aaaa33',
            'aaaa34',
            'aaaa35',
            'aaaa36',
            'aaaa37',
            'aaaa38',
            'aaaa39',
            'aaaa40',
            'aaaa41',
            'aaaa42',
            'aaaa43',
            'aaaa44',
            'aaaa45',
            'aaaa46',
            'aaaa47',
            'aaaa48',
            'aaaa49',
            'aaaa50',
            'aaaa51',
            'aaaa52',
            'aaaa53',
            'aaaa54',
            'aaaa55',
            'aaaa56',
            'aaaa57',
            'aaaa58',
            'aaaa59',
            'aaaa60',
            'aaaa61',
            'aaaa62',
            'aaaa63',
            'aaaa64',
            'aaaa65',
            'aaaa66',
            'aaaa67',
            'aaaa68',
            'aaaa69',
            'aaaa70',
            'aaaa71',
            'aaaa72',
            'aaaa73',
            'aaaa74',
            'aaaa75',
            'aaaa76',
            'aaaa77',
            'aaaa78',
            'aaaa79',
            'aaaa80',
            'aaaa81',
            'aaaa82',
            'aaaa83',
            'aaaa84',
            'aaaa85',
            'aaaa86',
            'aaaa87',
            'aaaa88',
            'aaaa89',
            'aaaa90',
            'aaaa91',
            'aaaa92',
            'aaaa93',
            'aaaa94',
            'aaaa95',
            'aaaa96',
            'aaaa97',
            'aaaa98',
            'aaaa99',
            'aaaa100',
            'aaaa101',
            'aaaa102',
            'aaaa103',
            'aaaa104',
            'aaaa105',
            'aaaa106',
            'aaaa107',
            'aaaa108',
            'aaaa109',
            'aaaa110',
            'aaaa111',
            'aaaa112',
            'aaaa113',
            'aaaa114',
            'aaaa115',
            'aaaa116',
            'aaaa117',
            'aaaa118',
            'aaaa119',
            'aaaa120',
            'aaaa121',
            'aaaa122',
            'aaaa123',
            'aaaa124',
            'aaaa125',
            'aaaa126',
            'aaaa127',
            'aaaa128',
            'aaaa129',
            'aaaa130',
            'aaaa131',
            'aaaa132',
            'aaaa133',
            'aaaa134',
            'aaaa135',
            'aaaa136',
            'aaaa137',
            'aaaa138',
            'aaaa139',
            'aaaa140',
            'aaaa141',
            'aaaa142',
            'aaaa143',
            'aaaa144',
            'aaaa145',
            'aaaa146',
            'aaaa147',
            'aaaa148',
            'aaaa149',
            'aaaa150',
            'aaaa151',
            'aaaa152',
            'aaaa153',
            'aaaa154',
            'aaaa155',
            'aaaa156',
            'aaaa157',
            'aaaa158',
            'aaaa159',
            'aaaa160',
            'aaaa161',
            'aaaa162',
            'aaaa163',
            'aaaa164',
            'aaaa165',
            'aaaa166',
            'aaaa167',
            'aaaa168',
            'aaaa169',
            'aaaa170',
            'aaaa171',
            'aaaa172',
            'aaaa173',
            'aaaa174',
            'aaaa175',
            'aaaa176',
            'aaaa177',
            'aaaa178',
            'aaaa179',
            'aaaa180',
            'aaaa181',
            'aaaa182',
            'aaaa183',
            'aaaa184',
            'aaaa185',
            'aaaa186',
            'aaaa187',
            'aaaa188',
            'aaaa189',
            'aaaa190',
            'aaaa191',
            'aaaa192',
            'aaaa193',
            'aaaa194',
            'aaaa195',
            'aaaa196',
            'aaaa197',
            'aaaa198',
            'aaaa199'
        ]

        matcher = ExpressionMatcher(expressions)

        input = 'A Town Mouse once visited a relative who lived in the country. For lunch the Country Mouse served wheat stalks, roots, and acorns, with a dash of cold water for drink. The Town Mouse ate very sparingly, nibbling a little of this and a little of that, and by her manner making it very plain that she ate the simple food only to be polite. After the meal the friends had a long talk, or rather the Town Mouse talked about her life in the city while the Country Mouse listened. They then went to bed in a cozy nest in the hedgerow and slept in quiet and comfort until morning. In her sleep the Country Mouse dreamed she was a Town Mouse with all the luxuries and delights of city life that her friend had described for her. So the next day when the Town Mouse asked the Country Mouse to go home with her to the city, she gladly said yes. When they reached the mansion in which the Town Mouse lived, they found on the table in the dining room the leavings of a very fine banquet. There were sweetmeats and jellies, pastries, delicious cheeses, indeed, the most tempting foods that a Mouse can imagine. But just as the Country Mouse was about to nibble a dainty bit of pastry, she heard a Cat mew loudly and scratch at the door. In great fear the Mice scurried to a hiding place, where they lay quite still for a long time, hardly daring to breathe. When at last they ventured back to the feast, the door opened suddenly and in came the servants to clear the table, followed by the House Dog. The Country Mouse stopped in the Town Mouses den only long enough to pick up her carpet bag and umbrella.'
        t1 = time.time()
        matched, overlaps, contains = matcher.match(input)
        t2 = time.time()
        print(f"Time Taken: {t2 - t1}")
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
