from elit.client import Client

class ElitModels:
    """
    Interacts with running ELIT server to retrieve ELIT model outputs for a given utterance
    """
    def __init__(self):
        self.model = Client('http://0.0.0.0:8000')

    def __call__(self, *args, **kwargs):
        """
        args[0] - string utterance
        returns (list of tokens, list of pos tags, list of dependency parse connections
        """
        parse_dict = self.model.parse([args[0]], models=['tok', 'pos', 'ner', 'srl', 'dep'])
        print(parse_dict["tok"][0])
        print(parse_dict["pos"][0])
        print(parse_dict["dep"][0])
        print()
        return [tok.lower() for tok in parse_dict["tok"][0]], parse_dict["pos"][0], parse_dict["dep"][0]