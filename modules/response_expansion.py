
expansion_types = ['type', 'property', 'qualifier', 'time', 'question', 'referential', 'instantiative',
                   'possess', 'indirect_obj', 'mode', 'negate']

class ResponseExpansion:

    def __call__(self, main_predicate, working_memory):
        """
        Select the supporting predicates for the main predicate.
        """
        main_s, main_t, main_o, main_i = main_predicate
        expansions = self.get_one_degree_supports([main_s, main_o, main_i], working_memory)
        subj_pred_expansions, obj_pred_expansions = [], []
        if working_memory.has(predicate_id=main_s):
            subj_pred_expansions = self.get_one_degree_supports([main_s], working_memory)
        if working_memory.has(predicate_id=main_o):
            obj_pred_expansions = self.get_one_degree_supports([main_o], working_memory)
        return [main_predicate] + expansions + subj_pred_expansions + obj_pred_expansions

    def get_one_degree_supports(self, items, working_memory):
        expansions = []
        for element in items:
            for pred_type in expansion_types:
                expansions.extend(working_memory.predicates(element, predicate_type=pred_type))
                expansions.extend(working_memory.predicates(predicate_type=pred_type, object=element))
        return expansions