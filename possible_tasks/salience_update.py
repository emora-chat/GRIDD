
import unittest

from GRIDD.data_structures.concept_graph import ConceptGraph
from globals import *


def update_salience(wm):
    """
    wm: a ConceptGraph representing current working memory.
    """
    raise NotImplementedError


class TestSalienceUpdate(unittest.TestCase):

    def test_update_salience(self):
        wm = ConceptGraph('''
        
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
        
        ''', metadata={
            'd': {SALIENCE: 1.0}
        })

        # Here's how to access concept salience
        assert wm.features['d'][SALIENCE] == 1.0

        saliences = update_salience(wm)

        for concept, salience in saliences.items():
            print(concept, ':', salience)

        '''
        Considerations:
        
        * Salience is supposed to model how an intelligent agent's attention
          shifts between concepts based on their semantic relatedness. There
          may be a few formulas for this; we basically just want the salience
          to "pool" onto concepts that are related to most of the existing 
          mentioned concepts. Feel free to change the salience update formula
          if you feel like the salience should be updated differently to get
          the right behavior.
        
        * Efficiency matters here. We want to update the salience of about
          200-400 concepts in under 0.1s if possible.        
          Best practices for efficient code:
            1) make sure time complexity of your algorithm makes sense
            2) don't bother with ANY micro-optimizations (optimizations
               that fall within the same big-O) until you run a profiler
               (cProfile is really good).
            3) Python is slow, especially when using lots of function calls
               within loops. If you do get to micro-optmizing, and are confident
               your alogrithm doesn't repeat any work, try refactoring to use 
               more built-in functions (e.g. python set operations) or libraries
               implemented in C such as numpy.
        '''



if __name__ == '__main__':
    unittest.main()


