from GRIDD.modules.response_selection_salience_spec import ResponseSelectionSalienceSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *

class ResponseSelectionSalience:

    def __call__(self, aux_state, working_memory, template_response_selection):
        if template_response_selection[0] is not None:
            # template response takes priority
            responses = [((template_response_selection[0],template_response_selection[1], template_response_selection[2]),
                          template_response_selection[3])]
        else:
            # removed nlg model
            responses = []
        return aux_state, responses

if __name__ == '__main__':
    print(ResponseSelectionSalienceSpec.verify(ResponseSelectionSalience))