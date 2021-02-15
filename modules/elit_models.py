
from GRIDD.modules.elit_models_spec import ElitModelsSpec

from elit.client import Client
import GRIDD.globals as globals
from GRIDD.data_structures.span import Span
from itertools import chain



class ElitModels:
    """
    Interacts with running ELIT server to retrieve ELIT model outputs for a given turn
    """
    def __init__(self):
        self.model = Client('http://0.0.0.0:8000')

    # todo - call elit_model.create_coref_context_from_online_output() and get_turn_history() before using coref_context in parse()
    def __call__(self, user_utterance, aux_state=None):
        """
        args[0] - string turn
        returns list of tokens, list of pos tags, list of dependency parse connections
        """
        if aux_state is None:
            aux_state = {}
        prev_global_toks = aux_state.get('coref_context', {}).get('global_tokens', [])
        aux_state.get('coref_context', {}).pop('global_tokens', None)

        system_utterance = aux_state.get('system_utterance', None)
        utterances = [system_utterance, user_utterance]
        speaker_ids = [1, 2]
        coref_context = aux_state.get('coref_context', None)
        models = ['tok', 'pos', 'ner', 'srl', 'dep', 'ocr']
        for i in range(len(utterances)-1,-1,-1):
            if utterances[i] is None:
                del utterances[i]
                del speaker_ids[i]

        parse_dict = self.model.parse(
            utterances,
            models=models,
            speaker_ids=speaker_ids,
            coref_context=coref_context
        )

        turn_index = aux_state.get('turn_index', None)
        all_tokens = []
        for j, toks in enumerate(parse_dict['tok']):
            tokens = []
            for i, tok in enumerate(toks):
                tokens.append(Span(tok.lower(), i, i+1, 0, turn_index, speaker_ids[j]))
            all_tokens.append(tokens)

        global_tokens = list(chain(prev_global_toks, *all_tokens))
        coref_result = parse_dict.get('ocr', {})
        coref_result['global_tokens'] = global_tokens

        if 2 not in speaker_ids:
            return [], [], [], None
        user_result_idx = speaker_ids.index(2)
        tok = all_tokens[user_result_idx]
        pos = parse_dict["pos"][user_result_idx]
        dep = parse_dict["dep"][user_result_idx]
        return tok, pos, dep, coref_result


    def print(self, tok, pos, dep):
        if globals.DEBUG:
            print()
            print('<< ELIT Models >> ')
            print(tok)
            print(pos)
            print(dep)
            print()

if __name__ == '__main__':
    print(ElitModelsSpec.verify(ElitModels))
