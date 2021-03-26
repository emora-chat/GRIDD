import random

neutral = ['Yeah', 'Gotcha', 'Sure', 'I see', 'Interesting', 'Hmm', 'Oh', 'Okay']

class ResponseAcknowledgment:

    def __call__(self, expanded_response_predicates, aux_state):
        generations = []
        turn_idx = aux_state.get('turn_index', None)
        for selection in expanded_response_predicates:
            if selection[2] == 'ack_conf' and (turn_idx is None or int(turn_idx) > 0):
                generations.append(self.generate(selection[0], selection[1]))
            else:
                generations.append(None)
        return generations

    def generate(self, main_predicate, supporting_predicates):
        return random.choice(neutral)