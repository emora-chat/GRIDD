
from structpy import specification
import json


@specification
class ElitModelsSpec:

    @specification.init
    def ELIT_MODELS(ElitModels):
        elit = ElitModels()
        tokens, pos, dep, ocr = elit('Hello, this is Emora.', 'My name is Susan.')
        print('Tokens:', tokens)
        print('POS:', pos)
        print('\nDP:', dep)
        #print(json.dumps(dep, indent=2))
        print('\nCR:')
        print(json.dumps(ocr, indent=2))

