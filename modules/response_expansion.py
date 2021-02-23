
subj_expansion_types = {'type', 'property', 'qualifier', 'time', 'question', 'referential', 'instantiative',
                        'indirect_obj', 'mode', 'negate'}
obj_expansion_types = {'possess'}

class ResponseExpansion:

    def __call__(self, main_predicate, working_memory):
        """
        Select the supporting predicates for the main predicate.
        """
        main_s, main_t, main_o, main_i = main_predicate
        if main_t != 'question':
            expansions = self.get_predicate_supports(main_predicate, working_memory)
        else:
            expansions = self.get_question_supports(main_s, working_memory)
        expansions -= {main_predicate}
        working_memory.features.update_from_response(main_predicate, expansions)
        return main_predicate, expansions, working_memory

    def get_predicate_supports(self, main_predicate, working_memory):
        main_s, main_t, main_o, main_i = main_predicate
        expansions = self.get_one_degree_supports([main_s, main_o, main_i], working_memory)
        if working_memory.has(predicate_id=main_s):
            subj_pred = working_memory.predicate(main_s)
            expansions.add(subj_pred)
            expansions.update(self.get_one_degree_supports([subj_pred[0], subj_pred[2]], working_memory))
        if working_memory.has(predicate_id=main_o):
            obj_pred = working_memory.predicate(main_o)
            expansions.add(obj_pred)
            expansions.update(self.get_one_degree_supports([obj_pred[0], obj_pred[2]], working_memory))
        return expansions

    def get_one_degree_supports(self, items, working_memory):
        expansions = set()
        items = [item for item in items if item is not None]
        for element in items:
            for pred_type in subj_expansion_types:
                expansions.update(working_memory.predicates(element, predicate_type=pred_type))
            for pred_type in obj_expansion_types:
                expansions.update(working_memory.predicates(predicate_type=pred_type, object=element))
        return expansions

    def get_question_supports(self, question_focus, working_memory):
        expansions = set()
        if working_memory.has(predicate_id=question_focus):
            # question is on a predicate
            question_predicate = working_memory.predicate(question_focus)
            expansions.add(question_predicate)
            supports = self.get_predicate_supports(question_predicate, working_memory)
            expansions.update(supports)
        else:
            # question is on an entity
            expansions.update(working_memory.predicates(question_focus))
            expansions.update(working_memory.predicates(object=question_focus))
            predicate_supports = set()
            for s, t, o, i in expansions:
                if t not in subj_expansion_types.union(obj_expansion_types):
                    preds = self.get_predicate_supports((s,t,o,i), working_memory)
                    predicate_supports.update(preds)
            expansions.update(predicate_supports)
        return expansions