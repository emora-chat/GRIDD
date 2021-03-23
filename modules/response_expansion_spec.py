from structpy import specification
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.knowledge_base import KnowledgeBase

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
        logicstring = '''
        sbb=be(sky,blue)
        sib=be(sbb,bad)
        bta=think(bot, sib)
        sbj=bring(bta, joy)
        isb=indirect_obj(sbj, bot)
        bs=shower(bot)
        sba=be(bs, annoying)
        sbs=but(sbj, sba)
        '''
        wm = WorkingMemory(KnowledgeBase(), logicstring)
        main_predicate, expansions, wm = response_expansion(wm.predicate('sbs'), wm)
        for pred in ['sbb', 'sib', 'bta', 'sbj', 'isb', 'bs', 'sba']:
            assert wm.predicate(pred) in expansions
        for type_pred in wm.predicates('bot', 'type'):
            assert type_pred in expansions




