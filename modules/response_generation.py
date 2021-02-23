
class ResponseGeneration:

    def __call__(self, main_predicate, supporting_predicates, aux_state):
        turn_idx = aux_state.get('turn_index', None)
        if turn_idx is not None and int(turn_idx) == 0:
            response = 'Hi, this is an Alexa Prize Socialbot. '
        response += str(main_predicate) + ' ' + str(supporting_predicates)
        return response