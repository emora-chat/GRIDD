
class ResponseAssembler:

    def __call__(self, aux_state, *responses):
        """
        Combine all responses from multiple response generator modules
        :param responses: Variable number of same-length response lists
        """
        turn_idx = aux_state.get('turn_index', None)
        if turn_idx is not None and int(turn_idx) == 0:
            final_response = ['Hi, this is an Alexa Prize Socialbot']
        else:
            final_response = []
        response_elements = [list(x) for x in zip(*responses)]
        for response_element in response_elements:
            response_element = [x for x in response_element if x is not None]
            if len(response_element) > 0:
                final_response.append(response_element[0])
        if len(final_response) > 0:
            return '. '.join(final_response)
        else:
            return "Well, that is quite an idea. But what else do you want to talk about?"
