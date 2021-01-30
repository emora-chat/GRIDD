
from GRIDD.modules.elit_models_spec import ElitModelsSpec

from elit.client import Client
import GRIDD.globals as globals


class ElitModels:
    """
    Interacts with running ELIT server to retrieve ELIT model outputs for a given utterance
    """
    def __init__(self):
        self.model = Client('http://0.0.0.0:8000')

    def __call__(self, user_utterance, system_utterance=None, coref_context=None):
        """
        args[0] - string utterance
        returns list of tokens, list of pos tags, list of dependency parse connections
        """

        if user_utterance is None and system_utterance is None:
            return [], [], [], None
        elif user_utterance is None:
            parse_dict = self.model.parse(
                [system_utterance],
                models=['tok', 'pos', 'ner', 'srl', 'dep', 'ocr'],
                speaker_ids=[1]
            )
            return [], [], [], parse_dict["ocr"]
        elif system_utterance is None:
            parse_dict = self.model.parse(
                [user_utterance],
                models=['tok', 'pos', 'ner', 'srl', 'dep', 'ocr'],
                speaker_ids=[2]
            )
            tok = [tok.lower() for tok in parse_dict["tok"][0]]
            pos = parse_dict["pos"][0]
            dep = parse_dict["dep"][0]
            self.print(tok, pos, dep)
            return tok, pos, dep, parse_dict["ocr"]
        else:
            parse_dict = self.model.parse(
                [system_utterance, user_utterance],
                models=['tok', 'pos', 'ner', 'srl', 'dep', 'ocr'],
                speaker_ids=[1, 2]
            )
            tok = [tok.lower() for tok in parse_dict["tok"][1]]
            pos = parse_dict["pos"][1]
            dep = parse_dict["dep"][1]
            self.print(tok, pos, dep)
            return tok, pos, dep, parse_dict["ocr"]

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
