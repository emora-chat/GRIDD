from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *
from GRIDD.utilities.utilities import _process_answers

class ResponseExpansion:

    def __init__(self, kb):
        self.knowledge_base = kb

    def __call__(self, main_predicates, working_memory, aux_state):
        """
        Select the supporting predicates for the main predicates.
        Update the node features of the selected predicates.

        :param main_predicates: [(main_pred_sig, generation_type), ...]
        """
        wm = working_memory
        responses = []
        for response_info, generation_type in main_predicates:
            if generation_type == "fallback":
                # response_info is a tuple (main predicate signature, CG of response, list of new concepts to insert)
                mapped_ids = wm.concatenate(response_info[1])
                exp_pred_sigs = [wm.predicate(c) for c in mapped_ids.values() if wm.has(predicate_id=c)]
                responses.append((response_info[0], exp_pred_sigs, response_info[2], generation_type))
            elif generation_type == 'template':
                # response_info is a tuple (response utterance, list of all selected predicates, list of new concepts to insert)
                responses.append((response_info[0], response_info[1], response_info[2], generation_type))
        responses = self.apply_dialogue_management_on_response(responses, wm, aux_state)
        return responses, working_memory

    def apply_dialogue_management_on_response(self, responses, wm, aux_state):
        final_responses = []
        for main, exps, inserts, generation_type in responses: # exps contains main predicate too
            if exps is not None:
                final_exps = []
                spoken_concepts = set()
                for s, t, o, i in exps:
                    if COLDSTART in wm.features[i]:
                        del wm.features[i][COLDSTART]
                    final_exps.append((s,t,o,i))
                    if t != EXPR:
                        spoken_concepts.add(i)
                        # emora turn tracking
                        for c in [s,o,i]:
                            if c is not None:
                                wm.features.setdefault(c, {}).setdefault(ETURN, set()).add(int(aux_state.get('turn_index', -1)))
                final_responses.append((main, final_exps, generation_type))
                self.assign_cover(wm, concepts=spoken_concepts)

                # add any inserts
                for c in inserts:
                    if len(c[0]) > 0:
                        if not wm.has(*c):
                            i = wm.add(*c)
                            spoken_concepts.add(i)
                        else:
                            spoken_concepts.update({pred[3] for pred in wm.predicates(*c)})
                        # todo - add salience links from exp preds to c
                        spoken_concepts.add(c[0])


                self.assign_salience(wm, concepts=spoken_concepts)
        return final_responses

    def assign_cover(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if graph.has(predicate_id=concept):
                if graph.type(concept) not in PRIM and not graph.has(concept, USER_AWARE):
                    i2 = graph.add(concept, USER_AWARE)
            else:
                if not graph.has(concept, USER_AWARE):
                    i2 = graph.add(concept, USER_AWARE)

    def assign_salience(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            graph.features[concept][SALIENCE] = SENSORY_SALIENCE

if __name__ == '__main__':
    from GRIDD.modules.response_expansion_spec import ResponseExpansionSpec
    print(ResponseExpansionSpec.verify(ResponseExpansion))