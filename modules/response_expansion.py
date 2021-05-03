from GRIDD.modules.response_expansion_spec import ResponseExpansionSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *

class ResponseExpansion:

    def __init__(self, kb):
        self.knowledge_base = kb

    def __call__(self, main_predicates, working_memory):
        """
        Select the supporting predicates for the main predicates.
        Update the node features of the selected predicates.

        :param main_predicates: [(main_pred_sig, generation_type), ...]
        """
        wm = working_memory
        responses = []
        for predicate, generation_type in main_predicates:
            if generation_type == 'nlg':
                # predicate is the main predicate tuple signature (subj, type, obj, id)
                expansions = wm.structure(predicate[3],
                                          subj_emodifiers={'time', 'mode', 'qualifier', 'property',
                                                           'indirect_obj', 'negate'},
                                          obj_emodifiers={'possess', REQ_TRUTH, REQ_ARG})
                expansions = set(expansions) # todo - fix this list to set to list conversion
                for pred in list(expansions):
                    for c in pred:
                        expansions.update(self.knowledge_base.predicates(c, 'expr'))
                        expansions.update(self.knowledge_base.predicates(predicate_type='expr', object=c))
                expansions = list(expansions)
                # check for unresolved user request
                emora_idk = False
                for s, t, o, i in expansions:
                    if s == 'user' and t in {REQ_TRUTH, REQ_ARG} and wm.metagraph.out_edges(o, REF):
                        emora_idk = True
                        break

                if emora_idk:
                    responses.append((predicate, expansions, 'idk'))
                else:
                    responses.append((predicate, expansions, generation_type))
            elif generation_type in {'ack_conf'}:
                # predicate is the main predicate tuple signature (subj, type, obj, id)
                responses.append((predicate, [], generation_type))
            elif generation_type == "backup":
                # predicate is a tuple (main predicate signature, list of all selected predicates)
                cg = ConceptGraph(namespace='bu_', predicates=predicate[1])
                mapped_ids = wm.concatenate(cg)
                main_pred = mapped_ids[predicate[0][3]]
                main_pred_sig = wm.predicate(main_pred)
                exp_preds = [mapped_ids[pred[3]] for pred in predicate[1]]
                exp_pred_sigs = [wm.predicate(pred) for pred in exp_preds if pred != main_pred]
                responses.append((main_pred_sig, exp_pred_sigs, generation_type))
            elif generation_type == 'template':
                # predicate is a tuple (response utterance, list of all selected predicates)
                responses.append((predicate[0], predicate[1], generation_type))
        responses = self.apply_dialogue_management_on_response(responses, wm)
        return responses, working_memory

    def apply_dialogue_management_on_response(self, responses, wm):
        final_responses = []
        for main, exps, generation_type in responses: # exps contains main predicate too
            final_exps = []
            spoken_predicates = set()
            for s, t, o, i in exps:
                if s == 'user' and t in {REQ_TRUTH, REQ_ARG}: # identify emora answers to user requests and add req_sat to request predicate
                    wm.add(i, REQ_SAT)
                else: # all other predicates are maintained as expansions and spoken predicates
                    final_exps.append((s,t,o,i))
                    if t != EXPR:
                        spoken_predicates.add(i)
            final_responses.append((main, final_exps, generation_type))
            self.assign_cover(wm, concepts=spoken_predicates)
            self.assign_salience(wm, concepts=spoken_predicates)
            self.assign_user_confidence(wm, concepts=spoken_predicates)
        return final_responses

    def assign_cover(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if graph.has(predicate_id=concept):
                if graph.type(concept) not in PRIM:
                    graph.add(concept, USER_AWARE)
            else:
                graph.add(concept, USER_AWARE)

    def assign_salience(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if graph.has(predicate_id=concept):
                graph.features[concept][SALIENCE] = SENSORY_SALIENCE

    def assign_user_confidence(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            graph.features[concept][BASE_UCONFIDENCE] = graph.features.get(concept, {}).get(BASE_CONFIDENCE, 0.0)

if __name__ == '__main__':
    print(ResponseExpansionSpec.verify(ResponseExpansion))