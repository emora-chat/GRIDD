
class ResponseRules:

    def __call__(self, aux_state, expanded_response_predicates):
        generations = [None] * len(expanded_response_predicates)
        for idx, selection in enumerate(expanded_response_predicates):
            response_type = selection[2]
            if response_type in {'template', 'fallback'}:
                generations[idx] = selection[0]
        return generations