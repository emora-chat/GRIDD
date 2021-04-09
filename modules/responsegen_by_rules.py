import random

neutral = ['Yeah', 'Gotcha', 'Sure', 'I see', 'Interesting', 'Hmm', 'Oh', 'Okay']
idk = ['I dont know', 'Im not sure', 'I have no idea']

class ResponseRules:

    def __call__(self, aux_state, expanded_response_predicates):
        generations = [None] * len(expanded_response_predicates)
        turn_idx = aux_state.get('turn_index', None)

        all_response_types = [s[2] for s in expanded_response_predicates]
        for idx, selection in enumerate(expanded_response_predicates):
            response_type = selection[2]
            if response_type == 'ack_conf' and 'idk' not in all_response_types:
                if turn_idx is None or int(turn_idx) > 0:
                    generations[idx] = random.choice(neutral)
            elif response_type == 'idk':
                generations[idx] = random.choice(idk)
        return generations