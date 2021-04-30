

import lark, time
from lark.visitors import Visitor_Recursive

from GRIDD.data_structures.id_map import IdMap
from itertools import chain
from GRIDD.globals import *
from functools import reduce


class ConceptCompiler:

    _default_instances = frozenset({})

    _default_types = frozenset({
        'object', 'entity', 'predicate', 'expr',
        'number', 'expression', 'implication', 'type', 'nonassert', 'assert'
    })
    _default_predicates = frozenset({
        'type', 'expr', 'predicate', 'nonassert', 'assert'
    })

    def __init__(self, instances=_default_instances, types=_default_types, predicates=_default_predicates, namespace='c_'):
        self.parser = lark.Lark(ConceptCompiler._grammar, parser='lalr')
        self.visitor = ConceptVisitor(instances, types, predicates, namespace)

    def _compile(self, string):
        if not string.strip().endswith(';'):
            string = string + ';'
        parse_tree = self.parser.parse(string)
        self.visitor.visit(parse_tree)
        return self.visitor.entries, self.visitor.links, self.visitor.datas

    def compile(self, logic_strings):
        """
        compile and update types, instances, and predicates to reflect new definitions
        """
        self.visitor.reset()
        if isinstance(logic_strings, str):
            logic_strings = [logic_strings]
        for string in logic_strings:
            if len(string) < 300 and string.endswith('.kg'):
                with open(string) as f:
                    string = f.read()
            for block in string.split(';'):
                if block.strip():
                    parse_tree = self.parser.parse(block + ';')
                    self.visitor.visit(parse_tree)
        return self.visitor.entries, self.visitor.links, self.visitor.datas

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
    block: state* ";"
    
    state: mark? (identified | chunk | ref | type | rule | _COMMENT) json?
    chunk: "<" state* ">"
    identified: id (args | expr? ((global| local) id? args)?)
    global: "="
    local: "/"
    args: "(" arg? ("," arg)* ")"
    arg: mark? (identified | chunk | ref | type) json?
    ref: "&" id? (args | ((global| local) id args) | chunk)
    type: "@" id? (args | ((global| local) id args) | chunk)
    mark: "*"
    rule: "->"
    expr: ESCAPED_STRING
    id: ID
    ID: /[a-zA-Z_.0-9]+/
    _COMMENT: "/*" /[^*]+/ "*/"
    
    json: dict
    value: dict | list | string | number | constant
    string: ESCAPED_STRING 
    number: SIGNED_NUMBER
    constant: CONSTANT
    CONSTANT: "true" | "false" | "null"
    list: "[" [value ("," value)*] "]"
    dict: "{" [pair ("," pair)*] "}"
    pair: ESCAPED_STRING ":" value
    
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS    
    %ignore WS
    '''


class ConceptVisitor(Visitor_Recursive):

    def __init__(self, instances, types, predicates, namespace='c_'):
        Visitor_Recursive.__init__(self)
        self.refgen = instances is None
        self.typegen = types is None
        self.predgen = predicates is None
        instances = set() if instances is None else set(instances)
        predicates = set() if predicates is None else set(predicates)
        types = (set() if types is None else set(types)) | predicates
        self.instances = instances                  # set of all initialized concepts
        self.types = types                          # set of all declared types
        self.predicates = predicates                # set of all declared predicate types
        self.globals = IdMap(namespace=namespace)   # global id generator
        self.entries = []                           # concepts to output
        self.links = []                             # metalinks to output
        self.datas = {}                             # metadata to output
        self.lentries = []                          # concepts within block
        self.llinks = []                            # metalinks within block
        self.ldatas = {}                            # metadata within block
        self.locals = {}                            # mapping of local_id : global_id

    def reset(self):
        self.entries = []  # concepts to output
        self.links = []  # metalinks to output
        self.datas = {}  # metadata to output
        self.lentries = []  # concepts within block
        self.llinks = []  # metalinks within block
        self.ldatas = {}  # metadata within block
        self.locals = {}  # mapping of local_id : global_id

    def _identified_tree_to_args(self, tree):
        id = None  # identifier of focal concept
        init = None  # 'global' / 'local' initialization type
        type = None  # type for initialization
        args = None  # list of arguments
        expr = None  # str of expressions
        ch = tree.children
        len_ch = len(tree.children)
        if len_ch == 1:
            id = ch[0].children[0]
        elif len_ch == 2 and ch[1].data == 'args':
            type = ch[0].children[0]
            args = [a.focus for a in ch[1].children]
        elif len_ch == 2 and ch[1].data == 'expr':
            id = ch[0].children[0]
            expr = ch[1].children[0]
        elif len_ch == 3:
            id = ch[0].children[0]
            init = ch[1].data
            args = [a.focus for a in ch[2].children]
        elif len_ch == 4 and ch[1].data == 'expr':
            id = ch[0].children[0]
            expr = ch[1].children[0]
            init = ch[2].data
            args = [a.focus for a in ch[3].children]
        elif len_ch == 4:
            id = ch[0].children[0]
            init = ch[1].data
            type = ch[2].children[0]
            args = [a.focus for a in ch[3].children]
        elif len_ch == 5:
            id = ch[0].children[0]
            expr = ch[1].children[0]
            init = ch[2].data
            type = ch[3].children[0]
            args = [a.focus for a in ch[4].children]
        return id, init, type, args, expr

    def _init(self, id=None, init=None, type=None, args=None, tree=None):
        concepts = []
        if args is None:
            id = self.locals.get(id, id)
            self._check_generic(id, tree)
        else:
            if init == 'local':
                if id in self.locals:
                    raise ValueError(f'Local variable {id} already declared.')
                self.locals[id] = self.globals.get()
            if type is None: # type init
                for arg in args:
                    new_type_instance = self.globals.get()
                    self.lentries.append((id, TYPE, arg, new_type_instance))
                    concepts.append(new_type_instance)
                self.types.add(id)
            else: # instance init
                if id is None:
                    id = self.globals.get()
                if len(args) > 2:
                    raise ValueError(f'Initializing {type} concept {id} with too many args: {args}')
                elif len(args) == 0:
                    type_inst = self.globals.get()
                    concepts.append(type_inst)
                    self.lentries.append((id, TYPE, type, type_inst))
                elif len(args) == 1:
                    if type != TYPE and hasattr(tree, 'generics'):
                        id = tree.generics.get(id, id)
                    self.lentries.append((args[0], type, None, id))
                elif len(args) == 2:
                    if type != TYPE and hasattr(tree, 'generics'):
                        for i in [0, 1]:
                            args[i] = tree.generics.get(args[i], args[i])
                    self.lentries.append((args[0], type, args[1], id))
                concepts.append(type)
            concepts.extend(args)
        concepts.append(id)
        return concepts

    def _check_generic(self, id, tree):
        if tree is not None and id in self.types:
            if not hasattr(tree, 'generics'):
                tree.generics = {}
            tree.generics[id] = self.globals.get()
            return tree.generics[id]
        return id

    def _add_exprs(self, id, expr):
        exprs = expr.split(',')
        exprs = reduce((
            lambda x, y: x[:-1] + [x[-1][:-1] + y] if x[-1][-1] == '\\' else x + [y.strip()]
        ), [[exprs[0].strip()], *exprs[1:]])
        for expr in exprs:
            new_expr_inst = self.globals.get()
            self.lentries.append((expr, EXPR, id, new_expr_inst))

    def _get_mark(self, tree):
        for ch in tree.children:
            if hasattr(ch, 'mark'):
                if not hasattr(tree, 'mark'):
                    tree.mark = ch.mark
                else:
                    raise ValueError(f'Double mark: {tree.mark} and {ch.mark}')

    def _collect_concepts(self, tree):
        concepts = set() if not hasattr(tree, 'concepts') else set(tree.concepts)
        for ch in tree.children:
            if hasattr(ch, 'concepts'):
                concepts.update(ch.concepts)
        tree.concepts = concepts
        generics = {} if not hasattr(tree, 'generics') else dict(tree.generics)
        for ch in tree.children:
            if hasattr(ch, 'generics'):
                generics.update(ch.generics)
        tree.generics = generics

    def _init_rule(self, precondition, postcondition, rid=None):
        if rid is None:
            rid = self.globals.get()
        for c in precondition:
            self.llinks.append((rid, c, PRE))
        for c in postcondition:
            self.llinks.append((rid, c, POST))
        return rid

    def _collect_rule(self, tree):
        rid = None
        for i, ch in enumerate(tree.children):
            if ch.data == 'rule' and rid is None:
                precondition = [c.focus for c in tree.children[:i]]
                postcondition = [c.focus for c in tree.children[i + 1:]]
                rid = self._init_rule(precondition, postcondition)
            elif rid is not None:
                raise ValueError(f'Multiple rules declared in chunk {tree.pretty()}.')

    def _globalize(self, ls, qualified):
        return [tuple(((self.locals.get(e, e) if e in qualified else e) for e in entry)) for entry in ls]

    def _constrained_concept_collect(self, tree):
        ident = None
        constraints = None
        ch = tree.children
        len_ch = len(ch)
        if len_ch == 1:
            if ch[0].data == 'chunk':
                if hasattr(ch[0], 'mark'):
                    ident = ch[0].mark
                    constraints = ch[0].concepts
                else:
                    raise ValueError(f'Constraint chunk {ch[0].focus} with no mark.')
            else:
                raise ValueError(f'Invalid syntax for {ch}.')
        elif len_ch == 2:
            if ch[1].data == 'args':
                self.identified(tree)
                ident = tree.focus
                constraints = tree.concepts
            elif ch[1].data == 'chunk':
                ident = ch[0].children[0]
                constraints = ch[1].concepts
        elif len_ch == 3:
            raise ValueError(f'Invalid syntax for {ch}')
        elif len_ch == 4:
            self.identified(tree)
            ident = tree.focus
            constraints = tree.concepts
        return ident, set(constraints) - {None}

    def block(self, tree):
        self._collect_rule(tree)
        for entry in self.lentries:
            self.entries.append(tuple((self.locals.get(e, e) for e in entry)))
        for entry in self.llinks:
            self.links.append(tuple((self.locals.get(e, e) for e in entry)))
        for k, v in self.ldatas:
            self.ldatas[self.locals.get(k, k)] = v
        self.lentries = []  # concepts within block
        self.llinks = []  # metalinks within block
        self.ldatas = {}  # metadata within block
        self.locals = {}  # mapping of local_id : global_id

    def state(self, tree):
        self._get_mark(tree)
        self._collect_concepts(tree)

    def chunk(self, tree):
        self._get_mark(tree)
        if hasattr(tree, 'mark'):
            tree.focus = tree.mark
            del tree.mark
        self._collect_concepts(tree)
        if hasattr(tree, 'generics') and tree.generics:
            generics = tree.generics
            precondition = set(chain(*[self._init(generics[generic], 'global', generic, [])
                                       for generic in generics]))
            postcondition = set(tree.concepts)
            self._init_rule(precondition, postcondition)
        self._collect_rule(tree)
        self.lentries = self._globalize(self.lentries, tree.concepts)
        self.llinks = self._globalize(self.llinks, tree.concepts)
        self.ldatas = dict(self._globalize(list(self.ldatas.items()), tree.concepts))

    def identified(self, tree):
        id, init, type, args, expr = self._identified_tree_to_args(tree)
        concepts = self._init(id, init, type, args, tree=tree)
        if expr is not None:
            self._add_exprs(id, expr)
        tree.focus = id
        tree.concepts = concepts
        self._collect_concepts(tree)
        return concepts

    def arg(self, tree):
        self._get_mark(tree)
        i = 0
        if tree.children[0].data == 'mark':
            i = 1
            tree.mark = tree.children[i].focus
        tree.focus = tree.children[i].focus
        self._collect_concepts(tree)

    def args(self, tree):
        self._get_mark(tree)
        self._collect_concepts(tree)

    def ref(self, tree):
        id, constraints = self._constrained_concept_collect(tree)
        tree.focus = id
        if hasattr(tree, 'mark'):
            del tree.mark
        for constraint in constraints:
            self.llinks.append((id, constraint, REF))
        tree.concepts = {tree.focus}
        if tree.focus in self.types:            # is this real?
            if not hasattr(tree, 'generics'):
                tree.generics = {}
            tree.generics[tree.focus] = self.globals.get()

    def type(self, tree):
        variable, constraints = self._constrained_concept_collect(tree)
        new_type = self.globals.get()
        tmp = self.locals.get(variable, variable)
        self.locals[variable] = new_type
        variable = tmp
        tree.focus = new_type
        if hasattr(tree, 'mark'):
            del tree.mark
        postcondition = set(self._init(None, None, TYPE, [variable, new_type]))
        self._init_rule(constraints, postcondition)
        tree.concepts = {tree.focus}
        if not hasattr(tree, 'generics'):
            tree.generics = {}
        tree.generics[tree.focus] = self.globals.get()

    def id(self, tree):
        tree.children[0] = str(tree.children[0])

    def string(self, tree):
        tree.value = str(tree.children[0][1:-1])

    def number(self, tree):
        tree.value = float(tree.children[0])

    def constant(self, tree):
        tree.value = {'null': None, 'true': True, 'false': False}[tree.children[0]]

    def list(self, tree):
        tree.value = [c.value for c in tree.children]

    def dict(self, tree):
        tree.value = {str(c.children[0])[1:-1]: c.children[1].value for c in tree.children}

    def value(self, tree):
        tree.value = tree.children[0].value


parser = lark.Lark(ConceptCompiler._grammar, parser='lalr')

to_parse = '''

&o<d/do(you) on(d, &t<t/test()>) quality(d, o/object()) time(d, past)>
request(me, o)
;

brown_dog = (member);
brown(x/dog()) -> type(x, brown_dog);
x/brown_dog() -> cute(x);

sally_and_john = (group)
type(sally, sally_and_john)
type(john, sally_and_john)

<l/like(me, sally_and_john)>

<
	@big_dog<big_dog/dog() big(big_dog)>
	@scared_cat<scared_cat/cat() scared(scared_cat)>
	chase(big_dog, scared_cat)
>;



'''


if __name__ == '__main__':
    i = time.time()
    c = ConceptCompiler()
    p, l, d = c.compile(to_parse)
    print('\nConcepts:')
    for e in p:
        print(e)
    print('\nMetalinks:')
    for e in l:
        print(e)
    print('\nMetadata:')
    for k, v in d.items():
        print(k, ':', v)
    f = time.time()
    print(f'\nElapsed time: {str(f - i)[:9]}')