
from GRIDD.data_structures.new_knowledge_parser_spec import KnowledgeParserSpec

from lark import Lark, Transformer, Tree
from GRIDD.data_structures.id_map import IdMap
from itertools import chain
from GRIDD.utilities.utilities import combinations


class KnowledgeParser:

    def __init__(self):
        self.parser = Lark(KnowledgeParser._grammar, parser='earley')
        self.transformer = KnowledgeTransformer()
        self.local_namespace = IdMap('local_')
        self.global_namespace = IdMap('global_')

    def parse(self, string):
        if not string.strip().endswith(';'):
            string = string + ';'
        parse_tree = self.parser.parse(string)
        print(parse_tree.pretty())
        print('\n\n')
        transformed = self.transformer.transform(parse_tree)
        entries = self.compile(transformed)
        return entries

    def compile(self, blocks):
        entries = []
        for block in blocks:
            # Expand multiplicities
            self.expand_predicate_multiplicities(block)
            for entry in block.values():
                ident = entry['id']
                type = entry.get('type', {'id': [entry['init']], 'mult': 'top'})
                mult = entry.get('mult', 'top')
                isglobal = entry.get('global', False)
                args = entry.get('args', [])
                inittype = entry['init']

            # Create entries
            for entry in block.values():
                ident = entry['id']
                mult = entry.get('mult', 'top')
                isglobal = entry.get('global', False)
                args = entry.get('args', [])
                inittype = entry['init']
                if inittype == 'concept':
                    type = entry['type']
                elif inittype == 'type':
                    pass
                elif inittype == 'ref':
                    pass
                elif inittype == 'string':
                    pass
                elif inittype == 'number':
                    pass
        return entries

    def expand_predicate_multiplicities(self, block, ident=None):
        if ident is None:
            for entry in block.values():
                ident = entry['id']
                type = entry.get('type', {'id': [entry['init']], 'mult': 'top'})
                mult = entry.get('mult', 'top')
                isglobal = entry.get('global', False)
                args = entry.get('args', [])
                inittype = entry['init']
                for arg in args:
                    if arg['mult'] == 'preds':
                        arg_ids = []
                        visited = set()
                        stack = list(arg['id'])
                        while stack:
                            i = stack.pop()
                            if i not in visited and 'args' in block.get(i, {}):
                                arg_ids.append(i)
                                stack.extend([])
                                visited.add(i)


    _grammar = r'''

        start: block*
        block: (rule | references) ";"
        references: reference+
        reference: comment? (declarations | identifiers) json? comment?
        declarations: declaration | predicates_declarations | concepts_declarations 
        declaration: (type_init | concept_init | ref_init | string_init | number_init)
        predicates_declarations: "<" reference (","? reference)* ">"
        concepts_declarations: "[" reference (","? reference)* "]"
        identifiers: ID | "[" ID (","? ID)* "]"
        type_init: global_name "(" identifiers ("," identifiers)* ")"
        concept_init: (global_name | local_name)? type "(" (reference ("," reference)?)? ")"
        ref_init: identifiers ":" reference
        string_init: string
        number_init: number
        global_name: identifiers "="
        local_name: identifiers "/"
        type: identifiers
        ID: /[a-zA-Z_.0-9]+/
        rule: references "=>" (ID "=>")? references
        json: dict
        value: dict | list | string | number | constant
        string: ESCAPED_STRING 
        number: SIGNED_NUMBER
        constant: CONSTANT
        CONSTANT: "true" | "false" | "null"
        list: "[" [value ("," value)*] "]"
        dict: "{" [pair ("," pair)*] "}"
        pair: ESCAPED_STRING ":" value
        comment: "/*" /[^*]+/ "*/"

        %import common.ESCAPED_STRING
        %import common.SIGNED_NUMBER
        %import common.WS    
        %ignore WS
        '''

class KnowledgeTransformer(Transformer):

    def __init__(self):
        Transformer.__init__(self)
        self._blocks = []
        self._block = {}

    def start(self, _):
        return self._blocks

    def block(self, _):
        self._blocks.append(self._block)
        self._block = {}
        return self._block

    def references(self, args):
        ret = args
        return ret

    def reference(self, args):
        args = [arg for arg in args if not isinstance(arg, Tree)]
        ret = args[0]
        if len(args) > 1:
            args[1]
        return ret

    def declarations(self, args):
        ret = args[0]
        return ret

    def declaration(self, args):
        ret = {**args[0], 'mult': 'top'}
        return ret

    def predicates_declarations(self, args):
        ret = {'id': list(chain(*[arg['id'] for arg in args])), 'mult': 'preds'}
        return ret

    def concepts_declarations(self, args):
        ret = {'id': list(chain(*[arg['id'] for arg in args])), 'mult': 'top'}
        return ret

    def identifiers(self, args):
        ret = {'id': [str(arg) for arg in args], 'mult': 'top'}
        return ret

    def type_init(self, args):
        init = {**args[0], 'args': args[1:], 'init': 'type'}
        for i in init['id']:
            self._block[i] = init
        ret = {'id': init['id']}
        return ret

    def concept_init(self, args):
        tidx = ['type' in arg for arg in args].index(True)
        identifier = {'id': [None], 'mult': 'top', 'global': False} if tidx == 0 else args[0]
        init = {**identifier, **args[tidx], 'args': args[tidx+1:], 'init': 'concept'}
        for i in init['id']:
            self._block[i] = init
        ret = {'id': init['id']}
        return ret

    def ref_init(self, args):
        init = {**args[0], 'args': args[1], 'init': 'ref'}
        for i in init['id']:
            self._block[i] = init
        ret = {'id': init['id']}
        return ret

    def string_init(self, args):
        init = {'id': list(chain(*[[a.strip() for a in arg.split(',')] for arg in args])),
                'init': 'string', 'mult': 'top', 'global': False}
        self._block[args[0]] = init
        ret = {'id': init['id']}
        return ret

    def number_init(self, args):
        init = {'id': args, 'init': 'number', 'mult': 'top', 'global': False}
        self._block[args[0]] = init
        ret = {'id': init['id']}
        return ret

    def global_name(self, args):
        ret = {**args[0], 'global': True}
        return ret

    def local_name(self, args):
        ret = {**args[0], 'global': False}
        return ret

    def type(self, args):
        ret = {'type': args[0]['id']}
        return ret

    def rule(self, args):
        if len(args) == 2:
            ret = {'pre': args[0], 'post': args[1]}
            return ret
        else:
            ret = {'pre': args[0], 'post': args[2], 'rid': args[1]}
            return ret

    def json(self, args):
        return {'metadata': args[0]}

    def value(self, args):
        return args[0]

    def list(self, args):
        return args

    def dict(self, args):
        return {str(k)[1:-1]: v for k, v in args}

    def pair(self, args):
        return args

    def string(self, args):
        return str(args[0][1:-1])

    def number(self, args):
        return float(args[0]) if '.' in args[0] else int(args[0])

    def constant(self, args):
        return {'true': True, 'false': False, 'null': None}[args[0]]


if __name__ == '__main__':
    print(KnowledgeParserSpec.verify(KnowledgeParser))