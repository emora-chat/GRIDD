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
        for predicate, generation_type in main_predicates:
            if generation_type == "fallback":
                # predicate is a tuple (main predicate signature, CG of response)
                mapped_ids = wm.concatenate(predicate[1])
                exp_pred_sigs = [wm.predicate(c) for c in mapped_ids.values() if wm.has(predicate_id=c)]
                responses.append((predicate[0], exp_pred_sigs, generation_type))
            elif generation_type == 'template':
                # predicate is a tuple (response utterance, list of all selected predicates)
                responses.append((predicate[0], predicate[1], generation_type))
        responses = self.apply_dialogue_management_on_response(responses, wm, aux_state)
        return responses, working_memory

    def apply_dialogue_management_on_response(self, responses, wm, aux_state):
        final_responses = []
        for main, exps, generation_type in responses: # exps contains main predicate too
            if exps is not None:
                final_exps = []
                spoken_predicates = set()
                for s, t, o, i in exps:
                    if COLDSTART in wm.features[i]:
                        del wm.features[i][COLDSTART]
                    if s == 'user' and t in {REQ_TRUTH, REQ_ARG}: # identify emora answers to user requests and add req_sat to request predicate
                        _process_answers(wm, i)
                    else: # all other predicates are maintained as expansions and spoken predicates
                        final_exps.append((s,t,o,i))
                        if t != EXPR:
                            spoken_predicates.add(i)
                            # emora turn tracking
                            for c in [s,o,i]:
                                if c is not None:
                                    wm.features.setdefault(c, {}).setdefault(ETURN, []).append(int(aux_state.get('turn_index', -1)))
                final_responses.append((main, final_exps, generation_type))
                self.assign_cover(wm, concepts=spoken_predicates)
                self.assign_salience(wm, concepts=spoken_predicates)
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
            if graph.has(predicate_id=concept):
                graph.features[concept][SALIENCE] = SENSORY_SALIENCE

if __name__ == '__main__':
    from GRIDD.modules.response_expansion_spec import ResponseExpansionSpec
    print(ResponseExpansionSpec.verify(ResponseExpansion))