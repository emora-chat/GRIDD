from GRIDD.modules.response_expansion_spec import ResponseExpansionSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from collections import deque

subj_definitionals = {'type', 'property', 'qualifier', 'time', 'question', 'referential', 'instantiative',
                      'indirect_obj', 'mode', 'negate'}
obj_definitionals = {'possess'}

class ResponseExpansion:

    def __call__(self, main_predicates, working_memory):
        """
        Select the supporting predicates for the main predicates.
        Update the node features of the selected predicates.

        :param main_predicates: [(main_pred_sig, generation_type), ...]
        """
        responses = []
        for predicate, generation_type in main_predicates:
            if generation_type == 'nlg':
                p, e = self.get_expansions(predicate, working_memory)
                responses.append((p, list(e), generation_type))
            elif generation_type in {"ack_conf", "ack_emo"}:
                responses.append((predicate, [], generation_type))
            elif generation_type == "backup":
                cg = ConceptGraph(namespace='default_', predicates=predicate[1])
                mapped_ids = working_memory.concatenate(cg)
                main_pred = mapped_ids[predicate[0][3]]
                main_pred_sig = working_memory.predicate(main_pred)
                exp_preds = [mapped_ids[pred[3]] for pred in predicate[1]]
                exp_pred_sigs = [working_memory.predicate(pred) for pred in exp_preds if pred != main_pred]
                responses.append((main_pred_sig, exp_pred_sigs, generation_type))
        return responses, working_memory

    def get_expansions(self, main_predicate, wm):
        expansions = set()
        if main_predicate is not None:
            visited = set()
            frontier = deque([main_predicate[0], main_predicate[2], main_predicate[3]])
            if main_predicate[1] == 'question': # pull all predicates that pertain to question focus
                for s,t,o,i in wm.predicates(main_predicate[0]): frontier.extend([o, i])
                for s,t,o,i in wm.predicates(object=main_predicate[0]): frontier.extend([s, i])
            while len(frontier) > 0:
                concept = frontier.popleft()
                if concept is not None and concept not in visited:
                    visited.add(concept)
                    if wm.has(predicate_id=concept):
                        s,t,o,i = wm.predicate(concept)
                        expansions.add((s,t,o,i))
                        frontier.extend([s, o])
                    for pred_type in subj_definitionals:
                        sigs = wm.predicates(concept, predicate_type=pred_type)
                        expansions.update(sigs)
                        for s,t,o,i in sigs: frontier.extend([o, i])
                    for pred_type in obj_definitionals:
                        sigs = wm.predicates(predicate_type=pred_type, object=concept)
                        expansions.update(sigs)
                        for s,t,o,i in sigs: frontier.extend([s, i])
        return main_predicate, expansions - {main_predicate}


if __name__ == '__main__':
    print(ResponseExpansionSpec.verify(ResponseExpansion))