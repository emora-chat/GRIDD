from structpy import specification
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.knowledge_base import KnowledgeBase
import time

@specification
class ResponseExpansionSpec:
    """

    """

    @specification.init
    def RESPONSEEXPANSION(ResponseExpansion):
        response_expansion = ResponseExpansion()
        return response_expansion

    def __call__(response_expansion, main_predicate, working_memory):
        """
        Get all supporting predicates for selected main predicate response
        """

        # Statement test
        logicstring = '''
        sbb=be(sky,blue)
        sib=be(sbb,bad)
        bta=think(bot, sib)
        sbj=bring(bta, joy)
        isb=indirect_obj(sbj, bot)
        bs=shower(bot)
        sba=be(bs, annoying)
        sbs=but(sbj, sba)
        sbp=be(sky,pretty)
        '''
        wm = WorkingMemory(KnowledgeBase(), logicstring)
        selections = [
            (wm.predicate('sbs'), 'nlg')
        ]
        s = time.time()
        responses, wm = response_expansion(selections, wm)
        print('%.3f sec'%(time.time()-s))
        for pred in ['sbb', 'sib', 'bta', 'sbj', 'isb', 'bs', 'sba']:
            assert wm.predicate(pred) in responses[0][1]
        assert 'sbp' not in responses[0][1]
        for type_pred in wm.predicates('bot', 'type'):
            assert type_pred in responses[0][1]

        # Entity Question  test
        logicstring = '''
        dpc=property(d=dog(), c=color())
        cq=question(c)
        sba=be(d, annoying)
        sld=locate(sba, dreams)
        '''
        wm = WorkingMemory(KnowledgeBase(), logicstring)
        selections = [
            (wm.predicate('sld'), 'nlg')
        ]
        s = time.time()
        responses, wm = response_expansion(selections, wm)
        print('%.3f sec'%(time.time()-s))
        for pred in ['dpc', 'sba', 'cq']:
            assert wm.predicate(pred) in responses[0][1]
        for type_pred in wm.predicates('d', 'type'):
            assert type_pred in responses[0][1]
        for type_pred in wm.predicates('c', 'type'):
            assert type_pred in responses[0][1]

        # Entity Question test
        # todo - fix (?) bc currently if entity question is focus, does not pull in all predicates...
        logicstring = '''
        dpc=property(d=dog(), c=color())
        cq=question(c)
        sba=be(d, annoying)
        sld=locate(sba, dreams)
        '''
        wm = WorkingMemory(KnowledgeBase(), logicstring)
        selections = [
            (wm.predicate('cq'), 'nlg')
        ]
        s = time.time()
        responses, wm = response_expansion(selections, wm)
        print('%.3f sec'%(time.time()-s))
        for pred in ['dpc', 'sba', 'sld']:
            assert wm.predicate(pred) in responses[0][1]
        for type_pred in wm.predicates('d', 'type'):
            assert type_pred in responses[0][1]
        for type_pred in wm.predicates('c', 'type'):
            assert type_pred in responses[0][1]