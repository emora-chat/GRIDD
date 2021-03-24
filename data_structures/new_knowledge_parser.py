
from GRIDD.data_structures.new_knowledge_parser_spec import KnowledgeParserSpec

from lark import Lark, Visitor
from GRIDD.data_structures.id_map import IdMap
from itertools import chain
from GRIDD.utilities.utilities import combinations


class KnowledgeParser:

    def __init__(self):
        self.parser = Lark(KnowledgeParser._grammar, parser='earley')
        self.visitor = KnowledgeVisitor()

    def parse(self, string):
        if not string.strip().endswith(';'):
            string = string + ';'
        parse_tree = self.parser.parse(string)
        print(parse_tree.pretty())
        print('\n\n')
        self.visitor.visit(parse_tree)
        for e in self.visitor.lentires:
            print(e)
        print('..')
        for e in self.visitor.entries:
            print(e)
        return self.visitor.entries

    _grammar = r'''

        start: block*
        block: (rule | declaration+) ";"
        declaration: _COMMENT? (reference | type_init | concept_init | monopred_init | bipred_init | ref_init | string_init | number_init | m_predicates | m_concepts) json? _COMMENT?     
        m_predicates: "<" declaration (","? declaration)* ">"
        m_concepts: "[" declaration (","? declaration)* "]"
        identifiers: ID | "[" ID (","? ID)* "]"
        global: "="
        local: "/"
        type_init: identifiers "=" "(" reference ("," reference)* ")"
        concept_init: (identifiers (global | local))? identifiers "()"
        monopred_init: (identifiers (global | local))? identifiers "(" declaration ")"
        bipred_init: (identifiers (global | local))? identifiers "(" declaration "," declaration ")"
        ref_init: identifiers ":" declaration
        string_init: string
        number_init: number
        reference: ID
        ID: /[a-zA-Z_.0-9]+/
        rule: declaration+ "=>" (ID "=>")? declaration+
        json: dict
        value: dict | list | string | number | constant
        string: ESCAPED_STRING 
        number: SIGNED_NUMBER
        constant: CONSTANT
        CONSTANT: "true" | "false" | "null"
        list: "[" [value ("," value)*] "]"
        dict: "{" [pair ("," pair)*] "}"
        pair: ESCAPED_STRING ":" value
        _COMMENT: "/*" /[^*]+/ "*/"

        %import common.ESCAPED_STRING
        %import common.SIGNED_NUMBER
        %import common.WS    
        %ignore WS
        '''

class KnowledgeVisitor(Visitor):

    def __init__(self, instances=None, types=None, predicates=None):
        Visitor.__init__(self)
        self.entries = []               # quadruples to output
        self.lentires = []              # quadruples of block
        self.metadatas = {}             # concept: json metadata entries
        self.globals = IdMap(namespace='kg_')   # global id generator
        self.linstances = set()         # concepts initialized within block
        self.refgen = instances is None # whether references autogenerate concepts
        instances = set() if instances is None else instances
        self.instances = instances      # set of all initialized concepts
        self.types = types              # set of all declared types
        self.predicates = predicates    # set of all declared predicate types

    def check_double_init(self, initialized, existing):
        if len(set(initialized)) != len(initialized):
            raise ValueError('Double instantiation within {}'.format(initialized))
        doubles = initialized & existing
        if doubles:
            raise ValueError('Double instantiation of concepts {}'.format(doubles))

    def check_mismatched_multiplicity(self, first, *lists):
        for l in lists:
            if len(first) != len(l):
                raise ValueError('Mismatched multiplicity in init: |{}| != |{}|'.format(first, l))

    def type_init(self, tree):
        newtype = [str(c) for c in tree.children[0].children]
        supertypes = [str(c.children[0]) for c in tree.children[1:]]
        for t, st in combinations(newtype, supertypes):
            self.lentires.append((t, 'type', st, self.globals.get()))
        if self.types is not None:
            self.types.update(newtype)

    def concept_init(self, tree):
        types = [str(c) for c in tree.children[-1].children]
        if len(tree.children) > 1:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.linstances)
                self.linstances.update(newconcepts)
            else:
                self.check_double_init(newconcepts, self.instances)
        else:
            newconcepts = [self.globals.get() for _ in types]
        self.check_mismatched_multiplicity(newconcepts, types)
        for i, type in enumerate(types):
            self.lentires.append((newconcepts[i], 'type', type, self.globals.get()))
        self.linstances.update(newconcepts)

    def monopred_init(self, tree):
        pass

    def bipred_init(self, tree):
        pass

    def ref_init(self, tree):
        pass

    def string_init(self, tree):
        pass

    def number_init(self, tree):
        pass

    def declaration(self, tree):
        pass


if __name__ == '__main__':
    print(KnowledgeParserSpec.verify(KnowledgeParser))