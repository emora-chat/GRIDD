

import lark, time


grammar = r'''

start: block*
block: (rule | declaration+) ";"
rule: precondition "->" (ID "->")? postcondition
precondition: declaration+
postcondition: declaration+

type_init: identifiers "=" "(" reference ("," reference)* ")"
concept_init: (identifiers (global | local))? identifiers "()"
monopred_init: (identifiers (global | local))? identifiers "(" declaration ")"
bipred_init: (identifiers (global | local))? identifiers "(" declaration "," declaration ")"
ref_init: identifiers ":" declaration

global: "="
local: "/"
identifiers: ID | "[" ID (","? ID)* "]"
declaration: ID

ID: /[a-zA-Z_.0-9]+/

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.WS    
%ignore WS
'''


parser = lark.Lark(grammar, parser='lalr')

to_parse = '''

a; a; a b c; a b c -> b; a;

'''


if __name__ == '__main__':
    i = time.time()
    tree = parser.parse(to_parse)
    f = time.time()
    print(tree.pretty())
    print(f'\nElapsed time: {str(f - i)[:9]}')