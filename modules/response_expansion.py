
expansion_types = ['type', 'property', 'qualifier', 'time', 'question', 'referential', 'instantiative',
                   'possess', 'indirect_obj', 'mode', 'negate']

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

        working_memory.features['salience'][main_i] = 1.0
        working_memory.features['cover'][main_i] = 1.0
        for pred in expansions:
            working_memory.features['salience'][pred[3]] = 1.0
            working_memory.features['cover'][pred[3]] = 1.0

        return main_predicate, expansions - {main_predicate}, working_memory

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
            for pred_type in expansion_types:
                expansions.update(working_memory.predicates(element, predicate_type=pred_type))
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
                if t not in expansion_types:
                    preds = self.get_predicate_supports((s,t,o,i), working_memory)
                    predicate_supports.update(preds)
            expansions.update(predicate_supports)
        return expansions