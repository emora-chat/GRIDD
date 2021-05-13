
import unittest

from GRIDD.data_structures.concept_graph import ConceptGraph


def pull(kb, wm, limit=None, branch_limit=None, reach=1):
    """
    kb:             ConceptGraph representing the knowledge base.
    wm:             ConceptGraph representing current working memory.
    limit:          maximum total number of concepts to pull.
    branch_limit:   maximum number of concepts to pull per puller.
    reach:          number of "hops"
    """
    raise NotImplementedError


class TestPullKnowledge(unittest.TestCase):

    def test_pull_simple(self):
        kb = ConceptGraph('''
        
        dog = (entity)
        cat = (entity)
        chase = (predicate)
        happy = (predicate)
        ;
        
        a = dog()
        b = dog()
        c = cat()
        d = dog()
        e = cat()
        f = dog()
        g = dog()
        h = cat()
        i = cat()
        ;
        
        cab=chase(a, b)
        cbc=chase(b, c)
        ccd=chase(c, d)
        cde=chase(d, e)
        cef=chase(e, f)
        cfg=chase(f, g)
        cgh=chase(g, h)
        cgi=chase(g, i)
        ;
        
        ''')

        wm = ConceptGraph('''
        happy(d)
        ''')

        pulled = pull(kb, wm)
        # neighbors of d pulled, since d was mentioned
        assert set(pulled) == {'c', 'e', 'ccd', 'cde'}

        pulled = pull(kb, wm, reach=2)
        # neighbors of d and neighbors-of-neighbors of d pulled
        assert set(pulled) == {'c', 'e', 'ccd', 'cde',
                               'b', 'cbc', 'f', 'cef'}

        pulled = pull(kb, wm, limit=3)
        # since the absolute limit is 3, a maximum of 3 concepts
        # should be returned by the pull operation.
        assert len(set(pulled)) <= 3

        pulled = pull(kb, wm, branch_limit=1)
        # since the branch limit is 1, after pulling along one
        # of d's connections, the pull operation should terminate
        # without pulling any additional neighbors of d
        print(set(pulled))

        '''
        Additional considerations:
        
        * there will potentially be hundreds of nodes in working memory--
          make sure the pull operation efficiently scales for large working
          memory and large KB.
        
        * if a predicate instance is pulled, its arguments MUST be pulled
        
        * when pulling concept A, any related predicates of type ESSENTIAL
          (see globals.ESSENTIAL) MUST be pulled
          
        * Test pulling with a large branch factor-- setting a small limit
          such as branch_limit=5 should make pulling efficient even with
          thousands of neighbors per concept
        '''



if __name__ == '__main__':
    unittest.main()