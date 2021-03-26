from structpy import specification
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.knowledge_base import KnowledgeBase

@specification
class ResponseSelectionSalienceSpec:

    @specification.init
    def RESPONSE_SELECTION_SALIENCE(ResponseSelectionSalience):
        response_selector = ResponseSelectionSalience()
        return response_selector

    def __call__(response_selector, working_memory):
        """
        Return a list of predicates and their generation types such that
        the selection is the highest salience acknowledgement and follow up
        without any cover

        Format: [(predicate_signature_tuple, str), ...]
        """
        logicstring = '''
        sbb=be(sky,blue)
        sbb{"salience": 0.9}
        sbs=ack_conf(sbb)
        sbs{"salience": 0.9}
        
        bs=shower(bot)
        bs{"salience": 0.95}
        abs=ack_conf(bs)
        abs{"salience": 0.95}
        '''
        wm = WorkingMemory(KnowledgeBase(), logicstring)
        main_predicates = response_selector(wm)
        assert main_predicates[0][0][3] == 'abs'
        assert main_predicates[0][1] == 'ack_conf'
        assert main_predicates[1][0][3] == 'bs'
        assert main_predicates[1][1] == 'nlg'





