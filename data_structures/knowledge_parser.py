from lark import Lark, Transformer
import GRIDD.data_structures.concept_graph as cg
from GRIDD.data_structures.knowledge_parser_spec import KnowledgeParserSpec
from GRIDD.utilities import Counter, collect
import os, json
from collections import defaultdict

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
                metadata: id "{" data "}"
                data: /[^{}]+/
                name: string_term
                type: string_term 
                types: type ("," type)+
                alias: string_wspace_term
                aliases: alias ("," alias)+
                id: string_term
                subject: string_wspace_term | bipredicate | monopredicate | instance | ontological
                object: string_wspace_term | bipredicate | monopredicate | instance | ontological
                string_term: STRING
                STRING: /[a-z_A-Z0-9".-]/+
                string_wspace_term: STRING_WSPACE
                STRING_WSPACE: /[a-z_A-Z0-9 ".-]/+
                WHITESPACE: (" " | "\n" | "\t")+
                %ignore WHITESPACE
            """
    _parser = Lark(_grammar, parser="earley")

    def __init__(self, kg=None, base_nodes=None, ensure_kb_compatible=False):
        self._predicate_transformer = PredicateTransformer(kg, base_nodes, ensure_kb_compatible)

    def parse(self, input):
        return KnowledgeParser._parser.parse(input)

    def transform(self, tree):
        return self._predicate_transformer.transform(tree)

    @classmethod
    def from_data(self, *datas, parser=None, namespace='default_'):
        if len(datas) > 0 and not isinstance(datas[0], str):
            return datas[0]
        if parser is None:
            parser = logic_parser
        concept_graph = cg.ConceptGraph(namespace=namespace)
        for data in datas:
            if isinstance(data, str) and (os.path.isdir(data) or os.path.isfile(data)):
                data = collect(data, extension='.kg')
            elif not isinstance(data, str):
                print('WARNING: `ConceptGraph.from_data` expects a single argument, if argument is type ConceptGraph!')
            else:
                data = [data]
            for d in data:
                d = d.strip()
                if len(d) > 0:
                    if d[-1] != ';':
                        d += ';'
                    additions = parser.transform(parser.parse(d))
                    for addition in additions:
                        concept_graph.concatenate(addition)
        return concept_graph

    @classmethod
    def rules(self, *datas):
        rules = {}
        for data in datas:
            if not isinstance(data, str):
                rules.update({rule[2]: (rule[0], rule[1])
                              for rule in KnowledgeParser._extract_rules_from_graph(data, with_names=True)})
            else:
                if isinstance(data, str) and (os.path.isdir(data) or os.path.isfile(data)):
                    data = collect(data, extension='.kg')
                else:
                    data = [data]
                for d in data:
                    d = d.strip()
                    if len(d) > 0:
                        if d[-1] != ';':
                            d += ';'
                        additions = logic_parser.transform(logic_parser.parse(d))
                        for addition in additions:
                            rules.update({rule[2]: (rule[0], rule[1])
                                          for rule in
                                          KnowledgeParser._extract_rules_from_graph(addition, with_names=True)})
        return rules

    @classmethod
    def _extract_rules_from_graph(self, rule, with_names=False):
        inferences, implications = {}, {}
        precondition_adds = defaultdict(set)
        idmap_for_situations = {}
        for situation_node, _, constraint, _ in rule.predicates(predicate_type='pre'):
            precondition_adds[situation_node].add(constraint)
        for situation_node, to_add in precondition_adds.items():
            inferences[situation_node] = cg.ConceptGraph(namespace='rule_', concepts=['var'])
            idmap = inferences[situation_node].concatenate(rule, concepts=to_add)
            idmap_for_situations[situation_node] = idmap

        postcondition_adds = defaultdict(set)
        for situation_node, _, implication, _ in rule.predicates(predicate_type='post'):
            postcondition_adds[situation_node].add(implication)
        for situation_node, to_add in postcondition_adds.items():
            implications[situation_node] = cg.ConceptGraph(namespace=inferences[situation_node].id_map(), concepts=['var'])
            implications[situation_node].concatenate(rule, concepts=to_add, id_map=idmap_for_situations[situation_node])

        rules = [(inferences[situation_node], implications[situation_node]) if not with_names else
                      (inferences[situation_node], implications[situation_node], situation_node)
                      for situation_node in inferences]

        # debugging
        for rule in rules:
            for sig, insts in rule[0]._monopredicate_instances.items():
                if len(insts) == 0:
                    assert False

        return rules


class PredicateTransformer(Transformer):

    def __init__(self, kg, base_nodes, ensure_kb_compatible=True):
        super().__init__()
        self.kg = kg
        self.base_nodes = base_nodes
        self.ensure_kb_compatible = ensure_kb_compatible
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
        situation_id = self.addition_construction.id_map().get()
        self.add_node(situation_id)
        self.add_monopredicate(situation_id, 'is_type')
        pre_inst, post_inst = self.get_condition_instances(preconditions, postconditions)
        self.add_preconditions(pre_inst, situation_id)
        self.add_postconditions(post_inst, situation_id)

    def named_rule(self, args):
        preconditions, type, postconditions = args[0], args[1].value, args[2]
        self._add_type(type)
        pre_inst, post_inst = self.get_condition_instances(preconditions, postconditions)
        self.add_preconditions(pre_inst, type)
        self.add_postconditions(post_inst, type)

    def inference(self, args):
        preconditions, type = args[0], args[1].value
        self._add_type(type)
        pre_inst, post_inst = self.get_condition_instances(preconditions=preconditions)
        self.add_preconditions(pre_inst, type)

    def implication(self, args):
        type, postconditions = args[0].value, args[1]
        self._add_type(type)
        pre_inst, post_inst = self.get_condition_instances(postconditions=postconditions)
        self.add_postconditions(post_inst, type)

    def conditions(self, args):
        return args

    def bipredicate(self, args):
        if len(args) > 3:
            name, id, type, subject, object = self._arg_decoder_bipredicate(args)
        elif len(args) == 3:
            name,id = None,None
            type, subject, object = args[0].value, args[1].value, args[2].value
        else:
            raise Exception('bipredicate must have 3 - 5 arguments')
        if id is None:
            id = self.addition_construction.id_map().get()
        id = self._id_duplication_check(id)
        subject = self._hierarchical_node_check(subject)
        object = self._hierarchical_node_check(object)
        type = self._is_type_check(type)
        id = self.add_bipredicate(subject, object, type, predicate_id=id)
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.add(id)
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def monopredicate(self, args):
        if len(args) > 2:
            id, name, type, subject = self._arg_decoder_monopredicate(args)
        elif len(args) == 2:
            name,id = None,None
            type, subject = args[0].value, args[1].value
        else:
            raise Exception('monopredicate must have 2 - 4 arguments')
        if id is None:
            id = self.addition_construction.id_map().get()
        id = self._id_duplication_check(id)
        subject = self._hierarchical_node_check(subject)
        type = self._is_type_check(type)
        id = self.add_monopredicate(subject, type, predicate_id=id)
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.add(id)
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def instance(self, args):
        if len(args) > 1:
            id, name, type = self._arg_decoder_instance(args)
        elif len(args) == 1:
            name,id = None,None
            type = args[0].value
        else:
            raise Exception('instance must have 1 - 2 arguments')
        if id is None:
            id = self.addition_construction.id_map().get()
        id = self._id_duplication_check(id)
        type = self._is_type_check(type)
        self.add_node(id)
        pred_id = self.add_bipredicate(id, type, 'type', predicate_id=self.addition_construction.id_map().get())
        arg_predicate_instances = self._get_union_of_arg_pred_instance_sets(args)
        arg_predicate_instances.update({id, pred_id})
        to_return = ParserStruct(self._id_encoder(name, id), pred_instances=arg_predicate_instances)
        return to_return

    def ontological(self, args):
        if len(args) == 3:
            id, aliases, types = args[0].value, args[1].value, args[2].value
        elif len(args) == 2:
            id, types = args[0].value, args[1].value
        else:
            raise Exception('ontological addition must have 2 or 3 arguments')
        if not isinstance(types, list):
            types = [types]
        id = self._manual_id_check(id[4:])
        if id is not None and not self.addition_construction.has(id):
            self.add_node(id)
        new_pred_ids = set()
        for type in types:
            type = self._is_type_check(type)
            pi = self.add_bipredicate(id, type, 'type', predicate_id=self.addition_construction.id_map().get())
            new_pred_ids.add(pi)
        mi = self.add_monopredicate(id, 'is_type', predicate_id=self.addition_construction.id_map().get())
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
            if not self.addition_construction.has(alias_node):
                self.add_node(alias_node)
            self.add_bipredicate(alias_node, 'expression', 'type', predicate_id=self.addition_construction.id_map().get())
            self.add_bipredicate(alias_node, id, 'expr', predicate_id=self.addition_construction.id_map().get())
        return id

    def metadata(self, args):
        id, data = args
        id = self._hierarchical_node_check(id)
        data_dict = json.loads(data)
        self.addition_construction.features[id].update(data_dict)

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
        to_return = ParserStruct(str(args[0]).strip(), pred_instances=set())
        return to_return

    def knowledge(self, args):
        self.additions.append(self.addition_construction)
        self.addition_construction = cg.ConceptGraph(concepts=self.base_nodes, namespace='add')
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

    def add_preconditions(self, preconditions, type):
        for pre in preconditions:
            pre = self._hierarchical_node_check(pre)
            self.add_bipredicate(type,pre,'pre',predicate_id=self.addition_construction.id_map().get())
            var_pred_id = self.add_monopredicate(pre,'var',predicate_id=self.addition_construction.id_map().get())
            self.add_bipredicate(type,var_pred_id,'pre',predicate_id=self.addition_construction.id_map().get())

    def add_postconditions(self, postconditions, type):
        for post in postconditions:
            post = self._hierarchical_node_check(post)
            self.add_bipredicate(type, post, 'post',predicate_id=self.addition_construction.id_map().get())

    ############
    #
    # Addition Wrappers
    #
    ############

    def add_bipredicate(self, subject, object, type, predicate_id=None):
        if self.ensure_kb_compatible:
            kg = self.kg._concept_graph
            if not (self.addition_construction.has(subject) or kg.has(subject)):
                raise Exception(":param 'source' error - node %s does not exist!" % subject)
            elif not (self.addition_construction.has(object) or kg.has(object)):
                raise Exception(":param 'target' error - node %s does not exist!" % object)
            elif not (self.addition_construction.has(type) or kg.has(type)):
                raise Exception(":param 'label' error - node %s does not exist!" % type)
            if predicate_id is not None and (self.addition_construction.has(predicate_id=predicate_id) or kg.has(predicate_id=predicate_id)):
                raise Exception("predicate id %s already exists!" % predicate_id)
        return self.addition_construction.add(subject, type, object, predicate_id=predicate_id)

    def add_monopredicate(self, subject, type, predicate_id=None):
        if self.ensure_kb_compatible:
            kg = self.kg._concept_graph
            if not (self.addition_construction.has(subject) or kg.has(subject)):
                raise Exception(":param 'source' error - node %s does not exist!" % subject)
            elif not (self.addition_construction.has(type) or kg.has(type)):
                raise Exception(":param 'target' error - node %s does not exist!" % type)
            if predicate_id is not None and (self.addition_construction.has(predicate_id=predicate_id) or kg.has(predicate_id=predicate_id)):
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

    def _hierarchical_node_check(self, node):
        if isinstance(node, str) and node.startswith('_int_'):
            node = int(node[5:])
        if node not in self.local_names:
            if self.ensure_kb_compatible and '"' not in node and not self.kg.has(node) and not self.addition_construction.has(node):
                # do not include expression nodes in this existence check
                raise Exception("error - node %s does not exist!" % node)
            elif not self.addition_construction.has(node):
                self.add_node(node)
        else:
            node = self.local_names[node]
        return node

    def _node_check(self, type):
        if self.ensure_kb_compatible and not self.kg.has(type) and not self.addition_construction.has(type):
            raise Exception("error - node %s does not exist!" % type)
        elif not self.addition_construction.has(type):
            self.add_node(type)
        return type

    def _is_type_check(self, type):
        if type in self.local_names:
            type = self.local_names[type]
        if self.ensure_kb_compatible and not self.kg.has(type) and not self.addition_construction.has(type):
            raise Exception("error - node %s does not exist!" % type)
        elif not self.addition_construction.has(type):
            if self.ensure_kb_compatible and not self.kg._concept_graph.has(type, 'is_type'):
                raise Exception('%s is not a type!'%type)
            self.add_node(type)
        elif self.ensure_kb_compatible and not self.kg.has(type):
            if not self.addition_construction.has(type, 'is_type'):
                raise Exception('%s is not a type!'%type)
        return type

    def _add_type(self, type):
        if self.ensure_kb_compatible and (not self.kg.has(type) and not self.addition_construction.has(type)):
            self.add_node(type)
            self.add_monopredicate(type,'is_type',predicate_id=self.addition_construction.id_map().get())

    def _manual_id_check(self, id):
        if id.isdigit():
            raise Exception("Manually specified ids cannot be numbers/integers, "
                            "but you are trying to add %s!" % id)
        return id

    def _id_duplication_check(self, id):
        if id is not None and (self.addition_construction.has(id) or (self.ensure_kb_compatible and self.kg.has(id))):
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
        self.addition_construction = cg.ConceptGraph(concepts=self.base_nodes, namespace='add')
        self.local_names = {}


class util:

    @classmethod
    def map(cls, current_graph, other_concept, other_namespace, id_map):
        if other_concept is None:
            return None
        if other_namespace is None:
            return other_concept
        if other_concept.startswith(other_namespace + '_'):
            if other_concept not in id_map:
                id_map[other_concept] = current_graph.id_map().get()
        else:
            id_map[other_concept] = other_concept

        mapped_concept = id_map[other_concept]
        if not current_graph.has(mapped_concept):
            current_graph.add(mapped_concept)
        return mapped_concept


logic_parser = KnowledgeParser()


if __name__ == '__main__':
    print(KnowledgeParserSpec.verify(KnowledgeParser))