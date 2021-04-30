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
                expansions = wm.structure(predicate[3],
                                          subj_emodifiers={'time', 'mode', 'qualifier', 'property',
                                                           'indirect_obj', 'negate'},
                                          obj_emodifiers={'possess', 'question'})
                expansions = set(expansions) # todo - fix this list to set to list conversion
                for pred in list(expansions):
                    for c in pred:
                        expansions.update(self.knowledge_base.predicates(c, 'expr'))
                        expansions.update(self.knowledge_base.predicates(predicate_type='expr', object=c))
                expansions = list(expansions)
                # check for unresolved user request
                emora_idk = False
                for s, t, o, i in expansions:
                    if s == 'user' and t == 'question' and wm.metagraph.out_edges(o, REF):
                        emora_idk = True
                        break

                if emora_idk:
                    responses.append((predicate, expansions, 'idk'))
                else:
                    responses.append((predicate, expansions, generation_type))
            elif generation_type in {'ack_conf'}:
                responses.append((predicate, [], generation_type))
            elif generation_type == "backup":
                cg = ConceptGraph(namespace='bu_', predicates=predicate[1])
                mapped_ids = wm.concatenate(cg)
                main_pred = mapped_ids[predicate[0][3]]
                main_pred_sig = wm.predicate(main_pred)
                exp_preds = [mapped_ids[pred[3]] for pred in predicate[1]]
                exp_pred_sigs = [wm.predicate(pred) for pred in exp_preds if pred != main_pred]
                responses.append((main_pred_sig, exp_pred_sigs, generation_type))
        spoken_predicates = set()
        for main, exps, _ in responses:
            # expansions contains main predicate too
            spoken_predicates.update([pred[3] for pred in exps if pred[1] != 'expr'])
            self.identify_request_resolutions(exps, wm)
        self.assign_cover_and_salience(wm, concepts=spoken_predicates)
        self.assign_user_confidence(wm, concepts=spoken_predicates)
        return responses, working_memory

    def identify_request_resolutions(self, spoken_predicates, wm):
        # identify emora answers to user requests and remove request bipredicate
        for s, t, o, i in spoken_predicates:
            if s == 'user' and t == 'question':
                wm.remove(s, t, o, i)

    def assign_cover_and_salience(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if not graph.has(predicate_id=concept) or graph.type(concept) not in PRIM:
                graph.add(concept, USER_AWARE)
            if graph.has(predicate_id=concept):
                graph.features[concept][SALIENCE] = SENSORY_SALIENCE

    def assign_user_confidence(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            graph.features[concept][BASE_UCONFIDENCE] = graph.features.get(concept, {}).get(BASE_CONFIDENCE, 0.0)

if __name__ == '__main__':
    print(ResponseExpansionSpec.verify(ResponseExpansion))