from lark import Lark, Transformer
from knowledge_base.concept_graph import ConceptGraph
import time, sys, json
from os.path import join
from pyswip import Prolog

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr', 'pre', 'post', 'var'}

class KnowledgeGraph:

    def __init__(self, filename=None, nodes=None):
        if nodes is None:
            nodes = BASE_NODES
        else:
            nodes.update(BASE_NODES)
        self._concept_graph = ConceptGraph(nodes=nodes)
        self._grammar = r"""
            start: knowledge+
            knowledge: ((bipredicate | monopredicate | instance | ontological | expression )+ ";") | ((anon_rule | named_rule | inference | implication) ";")
            anon_rule: conditions "=>" conditions
            named_rule: conditions "->" type "->" conditions
            inference: conditions "->" type
            implication: type "->" conditions
            conditions: (bipredicate | monopredicate | instance)+
            bipredicate: ((name "/")|(id "="  ))? type "(" subject "," object ")"
            monopredicate: ((name "/")|(id "="  ))? type "(" subject ")"
            instance: ((name "/")|(id "="))? type "(" ")"
            ontological: id "<" (type | types) ">"
            expression: id "[" (alias | aliases) "]"
            name: STRING
            type: STRING 
            types: type ("," type)+
            alias: STRING_WSPACE
            aliases: alias ("," alias)+
            id: STRING
            subject: STRING | bipredicate | monopredicate | instance | ontological
            object: STRING | bipredicate | monopredicate | instance | ontological
            STRING: /[a-z_A-Z0-9]/+
            STRING_WSPACE: /[a-z_A-Z0-9 ]/+
            WHITESPACE: (" " | "\n")+
            %ignore WHITESPACE
        """
        self.parser = Lark(self._grammar, parser="earley")
        self.predicate_transformer = PredicateTransformer(self)

        self._concept_graph.merge(self.add_knowledge(open(join('knowledge_base','kg_files','base.kg'), 'r').read())[0])
        self.predicate_transformer._set_kg_concepts()

        if filename is not None:
            self.add_knowledge(open(filename, 'r').read())

    def add_knowledge(self, input):
        if input.endswith('.kg'):
            input = open(input, 'r').read()
        tree = self.parser.parse(input)
        return self.predicate_transformer.transform(tree)

    def query(self, query_graph):
        prolog = Prolog()
        prolog.assertz("father(michael,john)")
        prolog.assertz("father(michael,gina)")
        assert list(prolog.query("father(michael,X)")) == [{'X': 'john'}, {'X': 'gina'}]
        for soln in prolog.query("father(X,Y)"):
            print(soln["X"], "is the father of", soln["Y"])

        rules = [rule.replace('.','').strip() for rule in
                 """type(like, like).
                    type(positive, positive).
                    type(love, love).
                    type(movie, movie).
                    type(genre, genre).
                    type(reason, reason).
                    type(property, property).
                    type(like, positive).
                    type(love, like).
                    type(love, positive).
                    type(starwars, movie).
                    type(avengers, movie).
                    type(action, genre).
                    type(comedy, genre).
                    predinst(like(john, starwars), ljs).
                    predinst(genre(starwars, action), gsa).
                    predinst(reason(ljs, gsa), rlg).
                    predinst(love(mary, avengers), lma).
                    predinst(genre(avengers, comedy), gac). 
                    predinst(reason(lma, gac), rlh).""".split('\n')]

        for rule in rules:
            prolog.assertz(rule)

        query = "predinst(A, B), functor(A, C, _), arg(1, A, D), arg(2, A, E), type(C, like), type(E, movie), predinst(F, G), functor(F, H, _), arg(1, F, E), arg(2, F, J), type(J, genre), predinst(K, L), functor(K, M, _), arg(1, K, B), arg(2, K, G), type(M, reason)"
        for soln in prolog.query(query):
            print(json.dumps(soln, indent=4))

"""
    def properties(self, concept):
        return self._concept_graph.predicates(concept)

    def types(self, concept):
        return self._concept_graph.predicates_of_subject(concept, predicate_type='type')

    def subtypes(self, concept):
        return self._concept_graph.predicates_of_object(concept, predicate_type='type')

    def instances(self, type_):
        pass

    def implication_rules(self, type_):
        pass

    def save(self, json_filename):
        pass
"""

class PredicateTransformer(Transformer):

    def __init__(self, kg):
        super().__init__()
        self.kg = kg
        self.kg_concepts = None
        self._set_kg_concepts()
        self._reset()

    def _reset(self):
        self.additions = []
        self.addition_construction = ConceptGraph(nodes=BASE_NODES)
        self.local_names = {}
        self.new_instances = set()

    def _set_kg_concepts(self):
        self.kg_concepts = self.kg._concept_graph.concepts()

    def anon_rule(self, args):
        preconditions, postconditions = args
        new_concepts = self.addition_construction.concepts()
        situation_id = self.kg._concept_graph._get_next_id()
        self.addition_construction.add_node(situation_id)
        self.addition_construction.add_monopredicate(situation_id, 'is_type')
        self._add_preconditions(preconditions, situation_id, new_concepts)
        self._add_postconditions(postconditions, situation_id, new_concepts)
        self._add_ontology_instance_tags()

    def named_rule(self, args):
        preconditions, type, postconditions = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self._add_preconditions(preconditions, type, new_concepts)
        self._add_postconditions(postconditions, type, new_concepts)
        self._add_ontology_instance_tags()

    def inference(self, args):
        preconditions, type = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self._add_preconditions(preconditions, type, new_concepts)
        self._add_ontology_instance_tags()

    def implication(self, args):
        type, postconditions = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self._add_postconditions(postconditions, type, new_concepts)
        self._add_ontology_instance_tags()

    def bipredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 3:
            name, id, type, subject, object = self._arg_decoder_bipredicate(args)
        elif len(args) == 3:
            name,id = None,None
            type, subject, object = args
        else:
            raise Exception('bipredicate must have 3 - 5 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        subject = self._hierarchical_node_check(subject, new_concepts)
        object = self._hierarchical_node_check(object, new_concepts)
        type = self._is_type_check(type, new_concepts)
        id = self.addition_construction.add_bipredicate(subject, object, type, predicate_id=id)
        self.new_instances.update({id})
        return self._id_encoder(name, id)

    def monopredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 2:
            id, name, type, subject = self._arg_decoder_monopredicate(args)
        elif len(args) == 2:
            name,id = None,None
            type, subject = args
        else:
            raise Exception('monopredicate must have 2 - 4 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        subject = self._hierarchical_node_check(subject, new_concepts)
        type = self._is_type_check(type, new_concepts)
        id = self.addition_construction.add_monopredicate(subject, type, predicate_id=id)
        self.new_instances.update({id})
        return self._id_encoder(name, id)

    def instance(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 1:
            id, name, type = self._arg_decoder_instance(args)
        elif len(args) == 1:
            name,id = None,None
            type = args[0]
        else:
            raise Exception('instance must have 1 - 2 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        type = self._is_type_check(type, new_concepts)
        self.addition_construction.add_node(id)
        pred_id = self.addition_construction.add_bipredicate(id, type, 'type',
                                                   predicate_id=self.kg._concept_graph._get_next_id())
        self.new_instances.update({id, pred_id})
        return self._id_encoder(name, id)

    def ontological(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) == 3:
            id, aliases, types = args
        elif len(args) == 2:
            id, types = args
        else:
            raise Exception('ontological addition must have 2 or 3 arguments')
        if not isinstance(types, list):
            types = [types]
        id = self._manual_id_check(id[4:])
        # id = self._id_duplication_check(id, new_concepts)
        if id is not None and id not in new_concepts and id not in self.kg_concepts:
            self.addition_construction.add_node(id)
        for type in types:
            type = self._is_type_check(type, new_concepts)
            self.addition_construction.add_bipredicate(id, type, 'type',
                                                       predicate_id=self.kg._concept_graph._get_next_id())
        self.addition_construction.add_monopredicate(id, 'is_type',
                                                     predicate_id=self.kg._concept_graph._get_next_id())
        return id

    def expression(self, args):
        id, aliases = args
        id = self._manual_id_check(id[4:])
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            alias_node = '"%s"' % alias
            self.addition_construction.add_node(alias_node)
            self.addition_construction.add_bipredicate(alias_node, 'expression', 'type')
            self.addition_construction.add_bipredicate(alias_node, id, 'expr')
        return id

    def _add_preconditions(self, preconditions, type, new_concepts):
        for pre in preconditions:
            pre = self._hierarchical_node_check(pre, new_concepts)
            self.addition_construction.add_bipredicate(type,pre,'pre')

    def _add_postconditions(self, postconditions, type, new_concepts):
        for post in postconditions:
            post = self._hierarchical_node_check(post, new_concepts)
            self.addition_construction.add_bipredicate(type, post, 'post')

    def _add_ontology_instance_tags(self):
        for id in self.new_instances:
            self.addition_construction.add_monopredicate(id, 'var')
        self.new_instances = {}

    def _hierarchical_node_check(self, node, new_concepts):
        if node.startswith('_int_'):
            node = int(node[5:])
        if node not in self.local_names:
            if node not in self.kg_concepts and node not in new_concepts:
                raise Exception("error - node %s does not exist!" % node)
            elif node not in new_concepts:
                self.addition_construction.add_node(node)
        else:
            node = self.local_names[node]
        return node

    def _node_check(self, type, new_concepts):
        if type not in self.kg_concepts and type not in new_concepts:
            raise Exception("error - node %s does not exist!" % type)
        elif type not in new_concepts:
            self.addition_construction.add_node(type)
        return type

    def _is_type_check(self, type, new_concepts):
        if type not in self.kg_concepts and type not in new_concepts:
            raise Exception("error - node %s does not exist!" % type)
        elif type not in new_concepts:
            if (type,'is_type') not in self.kg._concept_graph.monopredicates(type):
                raise Exception('%s is not a type!'%type)
            self.addition_construction.add_node(type)
        elif type not in self.kg_concepts:
            if (type,'is_type') not in self.addition_construction.monopredicates(type):
                raise Exception('%s is not a type!'%type)
        return type

    def _add_type(self, type, new_concepts):
        if type not in self.kg_concepts and type not in new_concepts:
            self.addition_construction.add_node(type)
            self.addition_construction.add_monopredicate(type,'is_type')

    def _manual_id_check(self, id):
        if id.isdigit():
            raise Exception("Manually specified ids cannot be numbers/integers, "
                            "but you are trying to add %s!" % id)
        return id

    def _id_duplication_check(self, id, new_concepts):
        if id is not None and (id in new_concepts or id in self.kg_concepts):
            raise Exception("id %s already exists!" % id)
        return id

    def _id_encoder(self, name, id):
        if name is not None:
            self.local_names[name] = id
        if isinstance(id, int):
            id = '_int_%d'%id
        return id

    def _arg_decoder_instance(self, args):
        name, id, type = None, None, None
        if len(args) == 2:
            if args[0].startswith('_id_'):
                id, type = args
                id = self._manual_id_check(id[4:])
            else:
                name, type = args
        return id, name, type

    def _arg_decoder_monopredicate(self, args):
        name, id, type, subject = None, None, None, None
        if len(args) == 3:
            if args[0].startswith('_id_'):
                id, type, subject = args
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject = args
        return id, name, type, subject

    def _arg_decoder_bipredicate(self, args):
        name, id, type, subject, object = None, None, None, None, None
        if len(args) == 4:
            if args[0].startswith('_id_'):
                id, type, subject, object = args
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject, object = args
        return name, id, type, subject, object

    def name(self, args):
        return str(args[0])

    def id(self, args):
        return '_id_' + str(args[0])

    def types(self, args):
        return args

    def type(self, args):
        return str(args[0])

    def aliases(self, args):
        return args

    def alias(self, args):
        return str(args[0])

    def subject(self, args):
        return str(args[0])

    def object(self, args):
        return str(args[0])

    def conditions(self, args):
        return args

    def knowledge(self, args):
        self.additions.append(self.addition_construction)
        self.addition_construction = ConceptGraph(nodes=BASE_NODES)
        self.local_names = {}
        self.new_instances = set()

    def start(self, args):
        to_return = self.additions
        self._reset()
        return to_return

if __name__ == '__main__':

    s = time.time()
    print('starting...')
    kg = KnowledgeGraph()
    print('base KG loaded...')
    # additions = kg.add_knowledge(join('knowledge_base','kg_files','example.kg'))
    additions = kg.add_knowledge(join('knowledge_base', 'kg_files', 'inferences.kg'))
    print('additions loaded...')
    print('Elapsed: %.2f sec'%(time.time()-s))

    kg.query(None)

    test = 1

