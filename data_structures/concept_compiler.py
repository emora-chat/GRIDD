
from GRIDD.data_structures.concept_compiler_spec import ConceptCompilerSpec

from lark import Lark, Tree
from lark.visitors import Visitor_Recursive
from GRIDD.data_structures.id_map import IdMap
from itertools import chain
from GRIDD.utilities.utilities import combinations


class ConceptCompiler:

    _default_instances = frozenset({

    })
    _default_types = frozenset({
        'object', 'entity', 'predicate',
        'number', 'expression', 'imp_rule'
    })
    _default_predicates = frozenset({
        'type', 'expr', 'predicate'
    })

    def __init__(self, instances=_default_instances, types=_default_types, predicates=_default_predicates, namespace='c_'):
        self.parser = Lark(ConceptCompiler._grammar, parser='earley')
        self.visitor = ConceptVisitor(instances, types, predicates, namespace)

    def _compile(self, string, instances=_default_instances, types=_default_types, predicates=_default_predicates):
        if not string.strip().endswith(';'):
            string = string + ';'
        parse_tree = self.parser.parse(string)
        if instances is not None: self.visitor.instances.update(instances)
        if types is not None: self.visitor.types.update(types)
        if predicates is not None: self.visitor.predicates.update(predicates)
        self.visitor.visit(parse_tree)
        return self.visitor.entries, self.visitor.metadatas

    def compile(self, logic_strings, instances=_default_instances, types=_default_types, predicates=_default_predicates, namespace=None):
        """
        compile and update types, instances, and predicates to reflect new definitions
        """
        entries, metas = [], {}
        if isinstance(logic_strings, str):
            logic_strings = [logic_strings]
        for string in logic_strings:
            if len(string) < 300 and string.endswith('.kg'):
                with open(string) as f:
                    string = f.read()
            e, m = self._compile(string, instances, types, predicates)
            entries.extend(e)
            metas.update(m)
            self.instances.update(self.visitor.instances)
            self.types.update(self.visitor.types)
            self.predicates.update(self.visitor.predicates)
        return entries, metas

    @property
    def namespace(self): return self.visitor.globals.namespace

    @property
    def instances(self): return self.visitor.instances

    @property
    def types(self): return self.visitor.types

    @property
    def predicates(self): return self.visitor.predicates

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
        rule: precondition "=>" (ID "=>")? postcondition
        precondition: declaration+
        postcondition: declaration+
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

class ConceptVisitor(Visitor_Recursive):

    def __init__(self, instances=None, types=None, predicates=None, namespace='c_'):
        Visitor_Recursive.__init__(self)
        self.entries = []               # quadruples to output
        self.rules = set()
        self.lentries = []              # quadruples of block
        self.metadatas = {}             # concept: json metadata entries
        self.lmetadatas = {}            # concept: json entries for local block
        self.globals = IdMap(namespace=namespace)   # global id generator
        self.locals = {}                # mapping of local_id : global_id
        self.linstances = set()         # all instances (for rule collection)
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

    def rule(self, tree):
        if len(tree.children) > 2:
            rid = tree.children[1]
        else:
            rid = self.globals.get()
        self.check_double_init([rid], self.instances)
        self.instances.add(rid)
        self.lentries.append((rid, 'type', 'imp_rule', self.globals.get()))
        precondition, variables = tree.children[0].data
        postcondition = tree.children[-1].data
        self.metadatas.setdefault(rid, {}).update(
            {'precondition': precondition, 'postcondition': postcondition, 'vars': variables})

    def precondition(self, tree):
        preinst = set(chain(*[t.refs for t in tree.iter_subtrees() if hasattr(t, 'refs')]))
        preinst = {self.locals.get(str(i), str(i)) for i in preinst}
        variables = set(chain(*[t.inits for t in tree.iter_subtrees() if hasattr(t, 'inits')]))
        variables = {self.locals.get(str(i), str(i)) for i in variables}
        tree.data = (preinst, variables)
        self.linstances = set()

    def postcondition(self, tree):
        postinst = set(chain(*[t.refs for t in tree.iter_subtrees() if hasattr(t, 'refs')]))
        postinst = {self.locals.get(str(i), str(i)) for i in postinst}
        tree.data = postinst
        self.linstances = set()

    def block(self, _):
        entries = [[self.locals.get(c, c) for c in e] for e in self.lentries]
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
        self.metadatas.update({self.locals.get(k, k): v for k, v in self.lmetadatas.items()})
        self.lentries = []
        self.lmetadatas = {}
        self.locals = {}
        self.plinstances = set()
        self.linstances = set()

    def type_init(self, tree):
        newtype = [str(c) for c in tree.children[0].children]
        supertypes = [str(c.children[0]) for c in tree.children[1:]]
        for t, st in combinations(newtype, supertypes):
            self.lentries.append((t, 'type', st, self.globals.get()))
        if self.types is not None:
            self.types.update(newtype)
        if any([st in self.predicates for st in supertypes]):
            self.predicates.update(newtype)
        tree.refs = newtype

    def concept_init(self, tree):
        types = [str(c) for c in tree.children[-1].children]
        if len(tree.children) > 1:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.locals)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.locals.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in types]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, types)
        self.linstances.update(newconcepts)
        tree.children[-1].refs = [str(r) for r in tree.children[-1].children]
        tree.children[-1].inits = []
        for i, type in enumerate(types):
            typeinst = self.globals.get()
            self.lentries.append((newconcepts[i], 'type', type, typeinst))
            tree.children[-1].refs.extend([typeinst, 'type'])  # Duct tape add type instance
            tree.children[-1].inits.append(typeinst)
            self.plinstances.add(typeinst)
        tree.refs = newconcepts
        tree.inits = newconcepts

    def monopred_init(self, tree):
        types = [str(c) for c in tree.children[-2].children]
        args = [str(c) for c in tree.children[-1].refs]
        type_arg = combinations(types, args)
        if len(tree.children) > 2:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.locals)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.locals.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in type_arg]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, type_arg)
        self.linstances.update(newconcepts)
        tree.children[-2].refs = types
        for i, (type, arg) in enumerate(type_arg):
            self.lentries.append((arg, type, None, newconcepts[i]))
            self.plinstances.add(newconcepts[i])
        tree.refs = newconcepts
        tree.inits = newconcepts

    def bipred_init(self, tree):
        types = [str(c) for c in tree.children[-3].children]
        arg0s = [str(c) for c in tree.children[-2].refs]
        arg1s = [str(c) for c in tree.children[-1].refs]
        type_args = combinations(types, arg0s, arg1s)
        if len(tree.children) > 3:
            newconcepts = [str(c) for c in tree.children[0].children]
            islocal = tree.children[1].data == 'local'
            if islocal:
                self.check_double_init(newconcepts, self.locals)
                newmap = {nc: self.globals.get() for nc in newconcepts}
                self.locals.update(newmap)
                self.instances.update(newmap.values())
            else:
                self.check_double_init(newconcepts, self.instances)
                self.instances.update(newconcepts)
        else:
            newconcepts = [self.globals.get() for _ in type_args]
            self.instances.update(newconcepts)
        self.check_mismatched_multiplicity(newconcepts, type_args)
        self.linstances.update(newconcepts)
        tree.children[-3].refs = types
        for i, (type, arg0, arg1) in enumerate(type_args):
            self.lentries.append((arg0, type, arg1, newconcepts[i]))
            self.plinstances.add(newconcepts[i])
        tree.refs = newconcepts
        tree.inits = newconcepts

    def ref_init(self, tree):
        tree.refs = tree.children[0].children
        tree.inits = tree.children[0].children
        ref_tree = tree.children[1]
        constraints = set(chain(*[t.refs for t in ref_tree.iter_subtrees() if hasattr(t, 'refs')]))
        constraints = {self.locals.get(str(i), str(i)) for i in constraints}
        variables = set(chain(*[t.inits for t in ref_tree.iter_subtrees() if hasattr(t, 'inits')]))
        variables = {self.locals.get(str(i), str(i)) for i in variables}
        for i in tree.children[0].children:
            if 'ref' in self.metadatas.get(i, {}):
                raise ValueError('Reference defined twice for concept {}'.format(i))
            self.lmetadatas.setdefault(i, {}).setdefault('ref', set()).update(constraints)
            self.lmetadatas[i].setdefault('vars', set()).update(variables)

    def string_init(self, tree):
        inits = ['"'+s.strip()+'"' for s in tree.children[0].children[0][1:-1].split(',')]
        for init in inits:
            if init not in self.instances:
                inst = self.globals.get()
                self.lentries.append((init, 'type', 'expression', inst))
                self.instances.add(init)
        tree.refs = inits

    def number_init(self, tree):
        inits = tree.children[0].children
        for init in inits:
            if init not in self.instances:
                inst = self.globals.get()
                self.lentries.append((init, 'type', 'number', inst))
                self.instances.add(init)
        tree.refs = inits

    def declaration(self, tree):
        if len(tree.children) > 1:
            for ident in tree.children[0].refs:
                self.lmetadatas.setdefault(ident, {}).update(tree.children[1].children[0].data)
        tree.refs = tree.children[0].refs

    def reference(self, tree):
        tree.refs = tree.children

    def m_predicates(self, tree):
        predicates = []
        stack = [tree]
        while stack:
            t = stack.pop()
            if isinstance(t, Tree):
                if hasattr(t, 'refs'):
                    predicates.extend(set(t.refs) & self.plinstances)
                stack.extend(t.children)
        tree.refs = predicates

    def m_concepts(self, tree):
        tree.refs = list(chain(*[c.refs for c in tree.children]))

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

    def string(self, tree):
        tree.data = str(tree.children[0][1:-1])

    def number(self, tree):
        tree.data = float(tree.children[0])

    def constant(self, tree):
        tree.data = {'null': None, 'true': True, 'false': False}[tree.children[0]]

    def list(self, tree):
        tree.data = [c.data for c in tree.children]

    def dict(self, tree):
        tree.data = {str(c.children[0])[1:-1]: c.children[1].data for c in tree.children}

    def value(self, tree):
        tree.data = tree.children[0].data


def compile_concepts(logic_strings, instances=None, types=None, predicates=None, namespace='c_'):
    return ConceptCompiler().compile(logic_strings, instances, types, predicates, namespace)


if __name__ == '__main__':
    print(ConceptCompilerSpec.verify(ConceptCompiler))