
from GRIDD.data_structures.new_knowledge_parser_spec import KnowledgeParserSpec

from lark import Lark, Visitor
from lark.visitors import Visitor_Recursive
from GRIDD.data_structures.id_map import IdMap
from itertools import chain
from GRIDD.utilities.utilities import combinations


class KnowledgeParser:

    def __init__(self, instances=None, types=None, predicates=None):
        self.parser = Lark(KnowledgeParser._grammar, parser='earley')
        self.visitor = KnowledgeVisitor(instances, types, predicates)

    def parse(self, string):
        if not string.strip().endswith(';'):
            string = string + ';'
        parse_tree = self.parser.parse(string)
        print(parse_tree.pretty())
        print('\n\n')
        self.visitor.visit(parse_tree)
        for e in self.visitor.lentries:
            print(e)
        print('--')
        for e in self.visitor.entries:
            print(e)
        print('--')
        for e, d in self.visitor.metadatas.items():
            print(e, ':', d)
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

class KnowledgeVisitor(Visitor_Recursive):

    def __init__(self, instances=None, types=None, predicates=None):
        Visitor_Recursive.__init__(self)
        self.entries = []               # quadruples to output
        self.lentries = []              # quadruples of block
        self.metadatas = {}             # concept: json metadata entries
        self.lmetadatas = {}            # concept: json entries for local block
        self.globals = IdMap(namespace='kg_')   # global id generator
        self.linstances = {}            # mapping of local_id : global_id
        self.plinstances = set()        # local predicate instances for predicate multiplicity
        self.refgen = instances is None # whether references autogenerate concepts
        instances = set() if instances is None else instances
        self.instances = instances      # set of all initialized concepts
        self.typegen = types is None
        types = set() if types is None else types
        self.types = types              # set of all declared types
        self.predgen = predicates is None
        predicates = set() if predicates is None else predicates
        self.predicates = predicates    # set of all declared predicate types

    def block(self, _):
        entries = [[self.linstances.get(c, c) for c in e] for e in self.lentries]
        if not self.refgen:
            refs = []
            for s, t, o, _ in entries:
                if t != 'type':
                    refs.append(s)
                    if o is not None:
                        refs.append(o)
            for e in refs:
                if e not in self.instances:
                    raise ValueError('Reference to undeclared concept `{}`'.format(e))
        predicate_types = [t for _, t, _, _ in entries]
        if not self.typegen:
            types = predicate_types + [o for _, t, o, _ in entries if t == 'type']
            for e in types:
                if e not in self.types:
                    raise ValueError('Reference to unknown type `{}`'.format(e))
        if not self.predgen:
            for e in predicate_types:
                if e not in self.predicates:
                    raise ValueError('Predicate initialization with non-predicate `{}`'.format(e))
        self.entries.extend(entries)
        self.lentries = []
        self.lmetadatas = {}
        self.linstances = {}
        self.plinstances = set()

    def type_init(self, tree):
        newtype = [str(c) for c in tree.children[0].children]
        supertypes = [str(c.children[0]) for c in tree.children[1:]]
        for t, st in combinations(newtype, supertypes):
            self.lentries.append((t, 'type', st, self.globals.get()))
        if self.types is not None:
            self.types.update(newtype)
        if any([st in self.predicates for st in supertypes]):
            self.predicates.update(newtype)

    def concept_init(self, tree):
        types = [str(c) for c in tree.children[-1].children]
        if len(tree.children) > 1:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.linstances)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.linstances.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in types]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, types)
        tree.children[-1].data = []
        for i, type in enumerate(types):
            typeinst = self.globals.get()
            self.lentries.append((newconcepts[i], 'type', type, typeinst))
            tree.children[-1].data.append(typeinst)  # Duct tape add type instance
            self.plinstances.add(typeinst)
        tree.data = newconcepts

    def monopred_init(self, tree):
        types = [str(c) for c in tree.children[-2].children]
        args = [str(c) for c in tree.children[-1].data]
        type_arg = combinations(types, args)
        if len(tree.children) > 2:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.linstances)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.linstances.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in type_arg]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, type_arg)
        for i, (type, arg) in enumerate(type_arg):
            self.lentries.append((arg, type, None, newconcepts[i]))
            self.plinstances.add(newconcepts[i])
        tree.data = newconcepts

    def bipred_init(self, tree):
        types = [str(c) for c in tree.children[-3].children]
        arg0s = [str(c) for c in tree.children[-2].data]
        arg1s = [str(c) for c in tree.children[-1].data]
        type_args = combinations(types, arg0s, arg1s)
        if len(tree.children) > 3:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.linstances)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.linstances.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in type_args]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, type_args)
        for i, (type, arg0, arg1) in enumerate(type_args):
            self.lentries.append((arg0, type, arg1, newconcepts[i]))
            self.plinstances.add(newconcepts[i])
        tree.data = newconcepts

    def ref_init(self, tree):
        for i in tree.children[0].children:
            if 'ref' in self.metadatas.get(i, {}):
                raise ValueError('Reference defined twice for concept {}'.format(i))
            self.metadatas.setdefault(i, {}).setdefault('ref', []).extend(tree.children[1].data)
        tree.data = tree.children[0].children

    def string_init(self, tree):
        inits = ['"'+s.strip()+'"' for s in tree.children[0].children[0][1:-1].split(',')]
        for init in inits:
            if init not in self.instances:
                inst = self.globals.get()
                self.lentries.append((init, 'type', 'expression', inst))
                self.instances.add(init)
        tree.data = inits

    def number_init(self, tree):
        inits = tree.children[0].children
        for init in inits:
            if init not in self.instances:
                inst = self.globals.get()
                self.lentries.append((init, 'type', 'number', inst))
                self.instances.add(init)
        tree.data = inits

    def declaration(self, tree):
        tree.data = tree.children[0].data

    def reference(self, tree):
        tree.data = tree.children

    def m_predicates(self, tree):
        predicates = []
        stack = [tree]
        while stack:
            t = stack.pop()
            if hasattr(t, 'data'):
                if isinstance(t.data, list):
                    predicates.extend(set(t.data) & self.plinstances)
                stack.extend(t.children)
        tree.data = predicates

    def m_concepts(self, tree):
        tree.data = list(chain(*[c.data for c in tree.children]))

    def check_double_init(self, initialized, existing):
        if len(set(initialized)) != len(initialized):
            raise ValueError('Double instantiation within {}'.format(initialized))
        doubles = set(initialized) & set(existing)
        if doubles:
            raise ValueError('Double instantiation of concepts {}'.format(doubles))

    def check_mismatched_multiplicity(self, first, *lists):
        for l in lists:
            if len(first) != len(l):
                raise ValueError('Mismatched multiplicity in init: |{}| != |{}|'.format(first, l))


if __name__ == '__main__':
    print(KnowledgeParserSpec.verify(KnowledgeParser))