
from GRIDD.modules.elit_models_spec import ElitModelsSpec
from elit.client import Client
import GRIDD.globals as globals
from GRIDD.data_structures.span import Span
from itertools import chain
import re

class ElitModels:
    """
    Interacts with running ELIT server to retrieve ELIT model outputs for a given turn
    """
    def __init__(self):
        print('init elit models')
        self.model = Client('http://0.0.0.0:8000')

    # todo - call elit_model.create_coref_context_from_online_output() and get_turn_history() before using coref_context in parse()
    def __call__(self, user_utterance, aux_state=None):
        """
        returns list of tokens, list of pos tags, list of dependency parse connections
        """
        if aux_state is None:
            aux_state = {}
        prev_global_toks = aux_state.get('coref_context', {}).get('global_tokens', [])
        aux_state.get('coref_context', {}).pop('global_tokens', None)

        system_utterance = aux_state.get('system_utterance', None) # todo - system utterance needs to be updated in chatbot_server; only happens in chatbot right now

        user_utterance = convert_contractions(user_utterance)
        if system_utterance is not None:
            system_utterance = convert_contractions(system_utterance)

        utterances = [system_utterance, user_utterance]
        speaker_ids = [1, 2]
        coref_context = aux_state.get('coref_context', None)
        models = ['lem', 'tok', 'pos', 'ner', 'srl', 'dep', 'ocr']
        for i in range(len(utterances)-1,-1,-1):
            if utterances[i] is None:
                del utterances[i]
                del speaker_ids[i]

        parse_dict = self.model.parse(utterances, models=models, speaker_ids=speaker_ids, coref_context=coref_context)

        turn_index = aux_state.get('turn_index', None)
        all_tokens = []
        for j, toks in enumerate(parse_dict['tok']):
            tokens = []
            for i, tok in enumerate(toks):
                lemma = parse_dict['lem'][j][i].lower()
                pos_tag = parse_dict['pos'][j][i].lower()
                if lemma in {"'s","s"}:
                    if 'vb' in pos_tag:
                        lemma = 'be'
                    elif 'prp' in pos_tag:
                        lemma = 'us'
                tokens.append(Span(tok.lower(), i, i+1, 0, turn_index, speaker_ids[j], lemma, pos_tag))
            all_tokens.append(tokens)

        global_tokens = list(chain(prev_global_toks, *all_tokens))
        coref_result = parse_dict.get('ocr', {})
        coref_result['global_tokens'] = global_tokens

        if 2 not in speaker_ids:
            return [], [], [], None
        user_result_idx = speaker_ids.index(2)
        parse_dict["tok"][user_result_idx] = all_tokens[user_result_idx]
        parse_dict["ocr"] = coref_result

        return {key: values[user_result_idx] if isinstance(values, list) else values
                for key, values in parse_dict.items()}


    def print(self, tok, pos, dep):
        if globals.DEBUG:
            print()
            print('<< ELIT Models >> ')
            print(tok)
            print(pos)
            print(dep)
            print()

# (1) Do not auto convert `its` to `it is` because could be possessive
# (2) no punctuation because elit auto-converts contractions if there is punctuation
# (3) todo - How to handle contractions that without punctuation are other words:
#         "shed": "she would",
#         "shell": "she will",
#         "wed": "we would",
contractions = {
        "aint": "is not",
        "arent": "are not",
        "cant": "can not",
        "cantve": "can not have",
        "couldve": "could have",
        "couldnt": "could not",
        "couldntve": "could not have",
        "didnt": "did not",
        "doesnt": "does not",
        "dont": "do not",
        "hadnt": "had not",
        "hasnt": "has not",
        "havent": "have not",
        "hed": "he would",
        "hedve": "he would have",
        "hes": "he is",
        "howd": "how did",
        "howll": "how will",
        "hows": "how is",
        "idve": "I would have",
        "illve": "I will have",
        "im": "I am",
        "ive": "I have",
        "isnt": "is not",
        "itd": "it would",
        "itll": "it will",
        "its": "it's",
        "lets": "let us",
        "mightve": "might have",
        "mustve": "must have",
        "mustnt": "must not",
        "shes": "she is",
        "shouldve": "should have",
        "shouldnt": "should not",
        "shouldntve": "should not have",
        "thats": "that is",
        "thered": "there would",
        "theredve": "there would have",
        "theres": "there is",
        "theyd": "they would",
        "theyll": "they will",
        "theyre": "they are",
        "theyve": "they have",
        "wanna": "want to",
        "wasnt": "was not",
        "wedve": "we would have",
        "weve": "we have",
        "werent": "were not",
        "whatll": "what will",
        "whatre": "what are",
        "whats": "what is",
        "whatve": "what have",
        "whens": "when is",
        "whenve": "when have",
        "whered": "where did",
        "wheres": "where is",
        "whereve": "where have",
        "wholl": "who will",
        "whollve": "who will have",
        "whos": "who is",
        "whove": "who have",
        "whys": "why is",
        "whyve": "why have",
        "willve": "will have",
        "wont": "will not",
        "wontve": "will not have",
        "wouldve": "would have",
        "wouldnt": "would not",
        "wouldntve": "would not have",
        "yall": "you all",
        "yallre": "you all are",
        "yallve": "you all have",
        "youd": "you would",
        "youdve": "you would have",
        "youll": "you will",
        "youllve": "you will have",
        "youre": "you are",
        "youve": "you have"
    }
contractions_upper = {k[0].upper() + k[1:]: v[0].upper() + v[1:] for k, v in contractions.items()}
contractions.update(contractions_upper)
contractions_re = r'\b(?:{})\b'.format('|'.join(contractions.keys()))

def convert_contractions(utter):
    matches = list(re.finditer(contractions_re, utter))
    for match in matches[::-1]:
        i, j = match.span()
        utter = utter[:i] + contractions[match.group()] + utter[j:]
    return utter

if __name__ == '__main__':
    print(ElitModelsSpec.verify(ElitModels))
