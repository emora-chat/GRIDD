from lark import Lark, Transformer
from knowledge_base.concept_graph import ConceptGraph
import time
from os.path import join

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr'}

class KnowledgeGraph:

    def __init__(self, filename=None, nodes=None):
        if nodes is None:
            nodes = BASE_NODES
        else:
            nodes.update(BASE_NODES)
        self._concept_graph = ConceptGraph(nodes=nodes)
        self._grammar = r"""
            start: knowledge+
            knowledge: (bipredicate | monopredicate | instance | ontological)+ ";"
            bipredicate: ((name "/")|(id ("[" (alias | aliases) "]")? "="  ))? type "(" subject "," object ")"
            monopredicate: ((name "/")|(id ("[" (alias | aliases) "]")? "="  ))? type "(" subject ")"
            instance: ((name "/")|(id ("[" (alias | aliases) "]")? "="))? type "(" ")"
            ontological: id ("[" (alias | aliases) "]")? "<" (type | types) ">"
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
        self.parser = Lark(self._grammar, parser="lalr")
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


class PredicateTransformer(Transformer):

    def __init__(self, kg):
        super().__init__()
        self.kg = kg
        self.kg_concepts = None
        self._set_kg_concepts()
        self.additions = []
        self.addition_construction = ConceptGraph(nodes=BASE_NODES)
        self.local_names = {}

    def _set_kg_concepts(self):
        self.kg_concepts = self.kg._concept_graph.concepts()

    def bipredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 3:
            name, id, aliases, type, subject, object = self._arg_decoder_bipredicate(args)
        elif len(args) == 3:
            name,id,aliases = None,None,None
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
        self._add_aliases(aliases, id, new_concepts)
        return self._id_encoder(name, id)

    def monopredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 2:
            id, name, aliases, type, subject = self._arg_decoder_monopredicate(args)
        elif len(args) == 2:
            name,id,aliases = None,None,None
            type, subject = args
        else:
            raise Exception('monopredicate must have 2 - 4 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        subject = self._hierarchical_node_check(subject, new_concepts)
        type = self._is_type_check(type, new_concepts)
        id = self.addition_construction.add_monopredicate(subject, type, predicate_id=id)
        self._add_aliases(aliases, id, new_concepts)
        return self._id_encoder(name, id)

    def instance(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 1:
            id, name, aliases, type = self._arg_decoder_instance(args)
        elif len(args) == 1:
            name,id,aliases = None,None,None
            type = args[0]
        else:
            raise Exception('instance must have 1 or 2 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        type = self._is_type_check(type, new_concepts)
        self.addition_construction.add_node(id)
        self.addition_construction.add_bipredicate(id, type, 'type',
                                                   predicate_id=self.kg._concept_graph._get_next_id())
        self._add_aliases(aliases, id, new_concepts)
        return self._id_encoder(name, id)

    def ontological(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) == 3:
            id, aliases, types = args
        elif len(args) == 2:
            aliases = None
            id, types = args
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
        self._add_aliases(aliases, id, new_concepts)
        return id

    def _add_aliases(self, aliases, node_id, new_concepts):
        if aliases is not None:
            if isinstance(aliases, str):
                aliases = [aliases]
            for alias in aliases:
                alias_node = '"%s"'%alias
                self.addition_construction.add_node(alias_node)
                expression_type = self._is_type_check('expression', new_concepts)
                self.addition_construction.add_bipredicate(alias_node, expression_type, 'type')
                self.addition_construction.add_bipredicate(alias_node, node_id, 'expr')

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
        name, id, aliases, type = None, None, None, None
        if len(args) == 3:
            if args[0].startswith('_id_'):
                id, aliases, type = args
                id = self._manual_id_check(id[4:])
            else:
                name, aliases, type = args
        elif len(args) == 2:
            if args[0].startswith('_id_'):
                id, type = args
                id = self._manual_id_check(id[4:])
            else:
                name, type = args
        return id, name, aliases, type

    def _arg_decoder_monopredicate(self, args):
        name, id, aliases, type, subject = None, None, None, None, None
        if len(args) == 4:
            if args[0].startswith('_id_'):
                id, aliases, type, subject = args
                id = self._manual_id_check(id[4:])
            else:
                name, aliases, type, subject = args
        elif len(args) == 3:
            if args[0].startswith('_id_'):
                id, type, subject = args
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject = args
        return id, name, aliases, type, subject

    def _arg_decoder_bipredicate(self, args):
        name, id, aliases, type, subject, object = None, None, None, None, None, None
        if len(args) == 5:
            if args[0].startswith('_id_'):
                id, aliases, type, subject, object = args
                id = self._manual_id_check(id[4:])
            else:
                name, aliases, type, subject, object = args
        elif len(args) == 4:
            if args[0].startswith('_id_'):
                id, type, subject, object = args
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject, object = args
        return name, id, aliases, type, subject, object

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

    def knowledge(self, args):
        self.additions.append(self.addition_construction)
        self.addition_construction = ConceptGraph(nodes=BASE_NODES)
        self.local_names = {}

    def start(self, args):
        to_return = self.additions
        self.additions = []
        self.addition_construction = ConceptGraph(nodes=BASE_NODES)
        self.local_names = {}
        return to_return

if __name__ == '__main__':

    s = time.time()
    print('starting...')
    kg = KnowledgeGraph()
    print('base KG loaded...')
    additions = kg.add_knowledge(join('knowledge_base','kg_files','example.kg'))
    print('additions loaded...')
    print('Elapsed: %.2f sec'%(time.time()-s))

    test = 1

