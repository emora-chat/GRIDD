from lark import Lark, Transformer
from data_structures.concept_graph import ConceptGraph

class ParserStruct:
    
    def __init__(self, value, pred_instances):
        self.value = value
        self.pred_instances = pred_instances

class KnowledgeParser:

    _grammar = r"""
                start: knowledge+
                knowledge: ((bipredicate | monopredicate | instance | ontological | expression )+ ";") | ((anon_rule | named_rule | inference | implication) ";")
                anon_rule: conditions "=>" conditions
                named_rule: conditions "->" type "->" conditions
                inference: conditions "->" type
                implication: type "->" conditions
                conditions: (bipredicate | monopredicate | instance | ontological)+
                bipredicate: ((name "/")|(id "="  ))? type "(" subject "," object ")"
                monopredicate: ((name "/")|(id "="  ))? type "(" subject ")"
                instance: ((name "/")|(id "="))? type "(" ")"
                ontological: id "<" (type | types) ">"
                expression: id "[" (alias | aliases) "]"
                name: string_term
                type: string_term 
                types: type ("," type)+
                alias: string_wspace_term
                aliases: alias ("," alias)+
                id: string_term
                subject: string_term | bipredicate | monopredicate | instance | ontological
                object: string_term | bipredicate | monopredicate | instance | ontological
                string_term: STRING
                STRING: /[a-z_A-Z0-9]/+
                string_wspace_term: STRING_WSPACE
                STRING_WSPACE: /[a-z_A-Z0-9 ]/+
                WHITESPACE: (" " | "\n")+
                %ignore WHITESPACE
            """
    _parser = Lark(_grammar, parser="earley")

    def __init__(self, kg, base_nodes, loading_kb=True):
        self._predicate_transformer = PredicateTransformer(kg, base_nodes, loading_kb)

    def parse(self, input):
        return KnowledgeParser._parser.parse(input)

    def transform(self, tree):
        return self._predicate_transformer.transform(tree)


class PredicateTransformer(Transformer):

    def __init__(self, kg, base_nodes, loading_kb=True):
        super().__init__()
        self.kg = kg
        self.base_nodes = base_nodes
        self.loading_kb = loading_kb
        self._reset()

    def get_condition_instances(self, preconditions=None, postconditions=None):
        pre_inst, post_inst = set(), set()
        if preconditions is not None:
            pre_inst = self._get_union_of_arg_pred_instance_sets(preconditions)
        if postconditions is not None:
            post_inst = self._get_union_of_arg_pred_instance_sets(postconditions)
        return pre_inst, post_inst

    def anon_rule(self, args):
        preconditions, postconditions = args
        situation_id = self.addition_construction._get_next_id()
        self.add_node(situation_id)
        self.add_monopredicate(situation_id, 'is_type')
        new_concepts = self.addition_construction.concepts()
        pre_inst, post_inst = self.get_condition_instances(preconditions, postconditions)
        self.add_preconditions(pre_inst, situation_id, new_concepts)
        self.add_postconditions(post_inst, situation_id, new_concepts)

    def named_rule(self, args):
        preconditions, type, postconditions = args[0], args[1].value, args[2]
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        new_concepts = self.addition_construction.concepts()
        pre_inst, post_inst = self.get_condition_instances(preconditions, postconditions)
        self.add_preconditions(pre_inst, type, new_concepts)
        self.add_postconditions(post_inst, type, new_concepts)

    def inference(self, args):
        preconditions, type = args[0], args[1].value
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        new_concepts = self.addition_construction.concepts()
        pre_inst, post_inst = self.get_condition_instances(preconditions=preconditions)
        self.add_preconditions(pre_inst, type, new_concepts)

    def implication(self, args):
        type, postconditions = args[0].value, args[1]
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        new_concepts = self.addition_construction.concepts()
        pre_inst, post_inst = self.get_condition_instances(postconditions=postconditions)
        self.add_postconditions(post_inst, type, new_concepts)

    def conditions(self, args):
        return args

    def bipredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 3:
            name, id, type, subject, object = self._arg_decoder_bipredicate(args)
        elif len(args) == 3:
            name,id = None,None
            type, subject, object = args[0].value, args[1].value, args[2].value
        else:
            raise Exception('bipredicate must have 3 - 5 arguments')
        if id is None:
            id = self.addition_construction._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        subject = self._hierarchical_node_check(subject, new_concepts)
        object = self._hierarchical_node_check(object, new_concepts)
        type = self._is_type_check(type, new_concepts)
        id = self.add_bipredicate(subject, object, type, predicate_id=id)
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.add(id)
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def monopredicate(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 2:
            id, name, type, subject = self._arg_decoder_monopredicate(args)
        elif len(args) == 2:
            name,id = None,None
            type, subject = args[0].value, args[1].value
        else:
            raise Exception('monopredicate must have 2 - 4 arguments')
        if id is None:
            id = self.addition_construction._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        subject = self._hierarchical_node_check(subject, new_concepts)
        type = self._is_type_check(type, new_concepts)
        id = self.add_monopredicate(subject, type, predicate_id=id)
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.add(id)
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def instance(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) > 1:
            id, name, type = self._arg_decoder_instance(args)
        elif len(args) == 1:
            name,id = None,None
            type = args[0].value
        else:
            raise Exception('instance must have 1 - 2 arguments')
        if id is None:
            id = self.addition_construction._get_next_id()
        id = self._id_duplication_check(id, new_concepts)
        type = self._is_type_check(type, new_concepts)
        self.add_node(id)
        pred_id = self.add_bipredicate(id, type, 'type', predicate_id=self.addition_construction._get_next_id())
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.update({id, pred_id})
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def ontological(self, args):
        new_concepts = self.addition_construction.concepts()
        if len(args) == 3:
            id, aliases, types = args[0].value, args[1].value, args[2].value
        elif len(args) == 2:
            id, types = args[0].value, args[1].value
        else:
            raise Exception('ontological addition must have 2 or 3 arguments')
        if not isinstance(types, list):
            types = [types]
        id = self._manual_id_check(id[4:])
        if id is not None and id not in new_concepts:
            self.add_node(id)
        new_pred_ids = set()
        for type in types:
            type = self._is_type_check(type, new_concepts)
            pi = self.add_bipredicate(id, type, 'type', predicate_id=self.addition_construction._get_next_id())
            new_pred_ids.add(pi)
        mi = self.add_monopredicate(id, 'is_type', predicate_id=self.addition_construction._get_next_id())
        new_pred_ids.add(mi)
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.update(new_pred_ids)
        arg_predicate_instances.add(mi)
        to_return = ParserStruct(id, pred_instances=arg_predicate_instances)
        return to_return

    def expression(self, args):
        id, aliases = args[0].value, args[1].value
        id = self._manual_id_check(id[4:])
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            alias_node = '"%s"' % alias
            self.add_node(alias_node)
            self.add_bipredicate(alias_node, 'expression', 'type', predicate_id=self.addition_construction._get_next_id())
            self.add_bipredicate(alias_node, id, 'expr', predicate_id=self.addition_construction._get_next_id())
        return id

    def name(self, args):
        to_return = ParserStruct(str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def id(self, args):
        to_return = ParserStruct('_id_' + str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def _get_union_of_arg_pred_instance_sets(self, args):
        pis = set()
        for arg in args:
            pis.update(arg.pred_instances)
        return pis

    def types(self, args):
        return_arg_list = [arg.value for arg in args]
        pis = self._get_union_of_arg_pred_instance_sets(args)
        to_return = ParserStruct(return_arg_list, pred_instances=pis)
        return to_return

    def type(self, args):
        to_return = ParserStruct(str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def aliases(self, args):
        return_arg_list = [arg.value for arg in args]
        pis = self._get_union_of_arg_pred_instance_sets(args)
        to_return = ParserStruct(return_arg_list, pred_instances=pis)
        return to_return

    def alias(self, args):
        to_return = ParserStruct(str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def subject(self, args):
        to_return = ParserStruct(str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def object(self, args):
        to_return = ParserStruct(str(args[0].value), pred_instances=args[0].pred_instances)
        return to_return

    def string_term(self, args):
        to_return = ParserStruct(str(args[0]), pred_instances=set())
        return to_return

    def string_wspace_term(self, args):
        to_return = ParserStruct(str(args[0]), pred_instances=set())
        return to_return

    def knowledge(self, args):
        self.additions.append(self.addition_construction)
        self.addition_construction = ConceptGraph(concepts=self.base_nodes, namespace='add')
        self.local_names = {}

    def start(self, args):
        to_return = self.additions
        self._reset()
        return to_return

    ############
    #
    # KG Updates
    #
    ############

    def add_preconditions(self, preconditions, type, new_concepts):
        for pre in preconditions:
            pre = self._hierarchical_node_check(pre, new_concepts)
            self.add_bipredicate(type,pre,'pre',predicate_id=self.addition_construction._get_next_id())
            var_pred_id = self.add_monopredicate(pre,'var',predicate_id=self.addition_construction._get_next_id())
            self.add_bipredicate(type,var_pred_id,'pre',predicate_id=self.addition_construction._get_next_id())

    def add_postconditions(self, postconditions, type, new_concepts):
        for post in postconditions:
            post = self._hierarchical_node_check(post, new_concepts)
            self.add_bipredicate(type, post, 'post',predicate_id=self.addition_construction._get_next_id())

    ############
    #
    # Addition Wrappers
    #
    ############

    def add_bipredicate(self, subject, object, type, predicate_id=None):
        if self.loading_kb:
            concepts = self.addition_construction.concepts()
            if subject not in concepts:
                raise Exception(":param 'source' error - node %s does not exist!" % subject)
            elif object not in concepts:
                raise Exception(":param 'target' error - node %s does not exist!" % object)
            elif type not in concepts:
                raise Exception(":param 'label' error - node %s does not exist!" % type)
            if predicate_id in concepts:
                raise Exception("predicate id %s already exists!" % predicate_id)
        return self.addition_construction.add(subject, type, object, predicate_id=predicate_id)

    def add_monopredicate(self, subject, type, predicate_id=None):
        if self.loading_kb:
            concepts = self.addition_construction.concepts()
            if subject not in concepts:
                raise Exception(":param 'source' error - node %s does not exist!" % subject)
            elif type not in concepts:
                raise Exception(":param 'label' error - node %s does not exist!" % type)
            if predicate_id in concepts:
                raise Exception("predicate id %s already exists!" % predicate_id)
        return self.addition_construction.add(subject, type, predicate_id=predicate_id)

    def add_node(self, node):
        if self.addition_construction._bipredicates_graph.has(node):
            raise Exception('node %s already exists in bipredicates'%node)
        if node in self.addition_construction._monopredicates_map:
            raise Exception('node %s already exists in monopredicates'%node)
        self.addition_construction.add(node)

    ############
    #
    # Helpers
    #
    ############

    def _hierarchical_node_check(self, node, new_concepts):
        if isinstance(node, str) and node.startswith('_int_'):
            node = int(node[5:])
        if node not in self.local_names:
            if self.loading_kb and not self.kg.has(node) and node not in new_concepts:
                raise Exception("error - node %s does not exist!" % node)
            elif node not in new_concepts:
                self.add_node(node)
        else:
            node = self.local_names[node]
        return node

    def _node_check(self, type, new_concepts):
        if self.loading_kb and not self.kg.has(type) and type not in new_concepts:
            raise Exception("error - node %s does not exist!" % type)
        elif type not in new_concepts:
            self.add_node(type)
        return type

    def _is_type_check(self, type, new_concepts):
        if type in self.local_names:
            type = self.local_names[type]
        if self.loading_kb and not self.kg.has(type) and type not in new_concepts:
            raise Exception("error - node %s does not exist!" % type)
        elif type not in new_concepts:
            if self.loading_kb and not self.kg._concept_graph.has(type, 'is_type'):
                raise Exception('%s is not a type!'%type)
            self.add_node(type)
        elif not self.kg.has(type):
            if not self.addition_construction.has(type, 'is_type'):
                raise Exception('%s is not a type!'%type)
        return type

    def _add_type(self, type, new_concepts):
        if not self.kg.has(type) and type not in new_concepts:
            self.add_node(type)
            self.add_monopredicate(type,'is_type',predicate_id=self.addition_construction._get_next_id())

    def _manual_id_check(self, id):
        if id.isdigit():
            raise Exception("Manually specified ids cannot be numbers/integers, "
                            "but you are trying to add %s!" % id)
        return id

    def _id_duplication_check(self, id, new_concepts):
        if id is not None and (id in new_concepts or self.kg.has(id)):
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
            if args[0].value.startswith('_id_'):
                id, type = args[0].value, args[1].value
                id = self._manual_id_check(id[4:])
            else:
                name, type = args[0].value, args[1].value
        return id, name, type

    def _arg_decoder_monopredicate(self, args):
        name, id, type, subject = None, None, None, None
        if len(args) == 3:
            if args[0].value.startswith('_id_'):
                id, type, subject = args[0].value, args[1].value, args[2].value
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject = args[0].value, args[1].value, args[2].value
        return id, name, type, subject

    def _arg_decoder_bipredicate(self, args):
        name, id, type, subject, object = None, None, None, None, None
        if len(args) == 4:
            if args[0].value.startswith('_id_'):
                id, type, subject, object = args[0].value, args[1].value, args[2].value, args[3].value
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject, object = args[0].value, args[1].value, args[2].value, args[3].value
        return name, id, type, subject, object

    def _reset(self):
        self.additions = []
        self.addition_construction = ConceptGraph(concepts=self.base_nodes, namespace='add')
        self.local_names = {}