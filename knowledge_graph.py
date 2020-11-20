from lark import Lark, Transformer
from concept_graph import ConceptGraph

class KnowledgeGraph:

    def __init__(self, filename=None, nodes=None):
        self._concept_graph = ConceptGraph(nodes=nodes)
        self._grammar = r"""
            start: knowledge+
            knowledge: (bipredicate | monopredicate | instance)+ ";"
            bipredicate: ((name "/")|(id "="))? type "(" subject "," object ")"
            monopredicate: ((name "/")|(id "="))? type "(" subject ")"
            instance: ((name "/")|(id "="))? type "(" ")"
            name: STRING
            type: STRING 
            id: STRING
            subject: STRING | bipredicate | monopredicate | instance
            object: STRING | bipredicate | monopredicate | instance
            STRING: /[a-z_A-Z0-9]/+
            WHITESPACE: (" " | "\n")+
            %ignore WHITESPACE
        """
        self.parser = Lark(self._grammar, parser="earley")
        self.predicate_transformer = PredicateTransformer(self)

        if filename is not None:
            self.add_knowledge(open(filename, 'r').read())

    def add_knowledge(self, input):
        tree = self.parser.parse(input)
        return self.predicate_transformer.transform(tree)

    # def add_entity_type(self, entity_type, supertypes):
    #     if isinstance(supertypes, list):
    #         for supertype in supertypes:
    #             self._concept_graph.add_bipredicate(entity_type, supertype, 'type')
    #     elif isinstance(supertypes, str):
    #         self._concept_graph.add_bipredicate(entity_type, supertypes, 'type')
    #     else:
    #         raise Exception(":param 'supertypes' must be a list or string!")
    #
    # def add_predicate_type(self, predicate_type, supertypes, arg0_types, arg1_types=None):
        # if isinstance(supertypes, list):
        #     for supertype in supertypes:
        #         self.kg._concept_graph.add_bipredicate(predicate_type, supertype, 'type')
        # elif isinstance(supertypes, str):
        #     self.kg._concept_graph.add_bipredicate(predicate_type, supertypes, 'type')
        # else:
        #     raise Exception(":param 'supertypes' must be a list or string!")
        #
        # arg0_instance = self.add_entity_instance(arg0_types, {})
        # if arg1_types is not None:
        #     arg1_instance = self.add_entity_instance(arg1_types, {})
        #     self.kg._concept_graph.add_bipredicate(arg0_instance, arg1_instance, predicate_type)
        # else:
        #     arg1_instance
    #
    #
    # def add_property(self, type_, property_dict):
    #     pass
    #
    # # todo - enforce that parameter 'properties' satisfies all supertype properties (need inference?)
    # # todo - if supertypes is None, just add a single unspecified node?
    # def add_entity_instance(self, supertypes, properties, entity_instance=None):
    #     if entity_instance is None:
    #         entity_instance = self._concept_graph._get_next_id()
    #     if isinstance(supertypes, list):
    #         for supertype in supertypes:
    #             self._concept_graph.add_bipredicate(entity_instance, supertype, 'type')
    #     elif isinstance(supertypes, str):
    #         self._concept_graph.add_bipredicate(entity_instance, supertypes, 'type')
    #     else:
    #         raise Exception(":param 'supertypes' must be a list or string!")
    #     for label, value in properties.items():
    #         self._concept_graph.add_bipredicate(entity_instance, value, label)
    #     return entity_instance


class PredicateTransformer(Transformer):

    def __init__(self, kg):
        super().__init__()
        self.kg = kg
        self.kg_concepts = self.kg._concept_graph.concepts()
        self.additions = []
        self.addition_construction = ConceptGraph()
        self.local_names = {}

    def bipredicate(self, args):
        name, id = None, None
        new_concepts = self.addition_construction.concepts()
        if len(args) == 4:
            if args[0].startswith('_id_'):
                id, type, subject, object = args
                id = id[4:]
            else:
                name, type, subject, object = args
        elif len(args) == 3:
            type, subject, object = args
        else:
            raise Exception('bipredicate must have 3 or 4 arguments')
        subject = self._hierarchical_node_check(subject, new_concepts)
        object = self._hierarchical_node_check(object, new_concepts)
        type = self._node_check(type, new_concepts)
        id = self.addition_construction.add_bipredicate(subject, object, type, predicate_id=id)
        if name is not None:
            self.local_names[name] = id
        return id

    def monopredicate(self, args):
        name, id = None, None
        new_concepts = self.addition_construction.concepts()
        if len(args) == 3:
            if args[0].startswith('_id_'):
                id, type, subject = args
                id = id[4:]
            else:
                name, type, subject = args
        elif len(args) == 2:
            type, subject = args
        else:
            raise Exception('monopredicate must have 2 or 3 arguments')

        subject = self._hierarchical_node_check(subject, new_concepts)
        type = self._node_check(type, new_concepts)
        id = self.addition_construction.add_monopredicate(subject, type, predicate_id=id)
        if name is not None:
            self.local_names[name] = id
        return id

    def instance(self, args):
        name, id = None, None
        new_concepts = self.addition_construction.concepts()
        if len(args) == 2:
            if args[0].startswith('_id_'):
                id, type = args
                id = id[4:]
            else:
                name, type = args
        elif len(args) == 1:
            type = args[0]
        else:
            raise Exception('instance must have 1 or 2 arguments')
        if id is None:
            id = self.kg._concept_graph._get_next_id()
        type = self._node_check(type, new_concepts)
        label = self._node_check('type', new_concepts)
        self.addition_construction.add_node(id)
        self.addition_construction.add_bipredicate(id, type, label)
        if name is not None:
            self.local_names[name] = id
        return id

    def _hierarchical_node_check(self, node, new_concepts):
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
            raise Exception("predicate_type error - node %s does not exist!" % type)
        elif type not in new_concepts:
            self.addition_construction.add_node(type)
        return type

    def name(self, args):
        return str(args[0])

    def id(self, args):
        return '_id_' + str(args[0])

    def type(self, args):
        return str(args[0])

    def subject(self, args):
        return str(args[0])

    def object(self, args):
        return str(args[0])

    def knowledge(self, args):
        self.additions.append(self.addition_construction)
        self.addition_construction = ConceptGraph()
        self.local_names = {}

    def start(self, args):
        return self.additions

if __name__ == '__main__':

    # text = """
    # test(me, you())
    # reason(reason(hu/happy(user_2), gus/go(user_2, store1)), bus/buy(user_2, i0/icecream()))
    # time(gus, past)
    # time(bus, past)
    # type(i0, chocolate)
    # """

    text = """
        gps/go(person,store)
        go(person,store)
        buy(person,store)
        reason(happy,gps);
        t/time(person)
        time(person);
    """

    text = """
        sally=person()
        sally_happy=happy(sally)
        reason(sally_happy,icecream);
    """

    kg = KnowledgeGraph(nodes=['person','store','icecream',
                               'go','buy','happy','reason','time','type'])
    additions = kg.add_knowledge(text)

    test = 1

