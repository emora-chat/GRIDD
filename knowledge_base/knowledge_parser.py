from lark import Lark, Transformer
from knowledge_base.concept_graph import ConceptGraph

class ParserStruct:
    
    def __init__(self, value, pred_instances):
        self.value = value
        self.pred_instances = pred_instances

class PredicateTransformer(Transformer):

    def __init__(self, kg, base_nodes):
        super().__init__()
        self.kg = kg
        self.base_nodes = base_nodes
        self.kg_concepts = None
        self._set_kg_concepts()
        self._reset()

    def anon_rule(self, args):
        preconditions, postconditions = args
        new_concepts = self.addition_construction.concepts()
        situation_id = self.kg._concept_graph._get_next_id()
        self.addition_construction.add_node(situation_id)
        self.addition_construction.add_monopredicate(situation_id, 'is_type')
        self.add_preconditions(self._get_union_of_arg_pred_instance_sets(preconditions), situation_id, new_concepts)
        self.add_postconditions(self._get_union_of_arg_pred_instance_sets(postconditions), situation_id, new_concepts)
        self.add_ontology_instance_tags()

    def named_rule(self, args):
        preconditions, type, postconditions = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self.add_preconditions(self._get_union_of_arg_pred_instance_sets(preconditions), type, new_concepts)
        self.add_postconditions(self._get_union_of_arg_pred_instance_sets(postconditions), type, new_concepts)
        self.add_ontology_instance_tags()

    def inference(self, args):
        preconditions, type = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self.add_preconditions(self._get_union_of_arg_pred_instance_sets(preconditions), type, new_concepts)
        self.add_ontology_instance_tags()

    def implication(self, args):
        type, postconditions = args
        new_concepts = self.addition_construction.concepts()
        self._add_type(type, new_concepts)
        self.add_postconditions(self._get_union_of_arg_pred_instance_sets(postconditions), type, new_concepts)
        self.add_ontology_instance_tags()

    def conditions(self, args):
        return args

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
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.add(pred_id)
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

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
        if id is not None and id not in new_concepts:
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
        self.addition_construction = ConceptGraph(nodes=self.base_nodes)
        self.local_names = {}
        self.new_instances = set()

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
            self.addition_construction.add_bipredicate(type,pre,'pre')

    def add_postconditions(self, postconditions, type, new_concepts):
        for post in postconditions:
            post = self._hierarchical_node_check(post, new_concepts)
            self.addition_construction.add_bipredicate(type, post, 'post')

    def add_ontology_instance_tags(self):
        for id in self.new_instances:
            self.addition_construction.add_monopredicate(id, 'var')
        self.new_instances = {}

    ############
    #
    # Helpers
    #
    ############

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
                id, type = args[0].value, args[1].value
                id = self._manual_id_check(id[4:])
            else:
                name, type = args[0].value, args[1].value
        return id, name, type

    def _arg_decoder_monopredicate(self, args):
        name, id, type, subject = None, None, None, None
        if len(args) == 3:
            if args[0].startswith('_id_'):
                id, type, subject = args[0].value, args[1].value, args[2].value
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject = args[0].value, args[1].value, args[2].value
        return id, name, type, subject

    def _arg_decoder_bipredicate(self, args):
        name, id, type, subject, object = None, None, None, None, None
        if len(args) == 4:
            if args[0].startswith('_id_'):
                id, type, subject, object = args[0].value, args[1].value, args[2].value, args[3].value
                id = self._manual_id_check(id[4:])
            else:
                name, type, subject, object = args[0].value, args[1].value, args[2].value, args[3].value
        return name, id, type, subject, object

    def _reset(self):
        self.additions = []
        self.addition_construction = ConceptGraph(nodes=self.base_nodes)
        self.local_names = {}
        self.new_instances = set()

    def _set_kg_concepts(self):
        self.kg_concepts = self.kg._concept_graph.concepts()