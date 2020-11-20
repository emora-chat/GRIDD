from lark import Lark, Transformer
from concept_graph import ConceptGraph

class PredicateTransformer(Transformer):

    def __init__(self, kg):
        super().__init__()
        self.kg = kg
        self.kg_concepts = self.kg._concept_graph.concepts()
        self.additions = ConceptGraph()
        self.local_names = {}

    def bipredicate(self, args):
        name = None
        new_concepts = self.additions.concepts()
        if len(args) == 4:
            name, type, subject, object = args
        elif len(args) == 3:
            type, subject, object = args
        else:
            raise Exception('bipredicate must have 3 or 4 arguments')
        subject = self._check_subject(subject, new_concepts)
        object = self._check_object(object, new_concepts)
        type = self._check_type(type, new_concepts)
        id = self.additions.add_bipredicate(subject, object, type)
        if name is not None:
            self.local_names[name] = id
        return id

    def monopredicate(self, args):
        name = None
        new_concepts = self.additions.concepts()
        if len(args) == 3:
            name, type, subject = args
        elif len(args) == 2:
            type, subject = args
        else:
            raise Exception('monopredicate must have 2 or 3 arguments')

        subject = self._check_subject(subject, new_concepts)
        type = self._check_type(type, new_concepts)
        id = self.additions.add_monopredicate(subject, type)
        if name is not None:
            self.local_names[name] = id
        return id


    def instance(self, args):
        name = None
        new_concepts = self.additions.concepts()
        if len(args) == 2:
            name, type = args
        elif len(args) == 1:
            type = args[0]
        else:
            raise Exception('instance must have 1 or 2 arguments')
        id = self.kg._concept_graph._get_next_id()
        type = self._check_type(type, new_concepts)
        self.additions.add_node(id)
        self.additions.add_bipredicate(id, type, 'type')
        if name is not None:
            self.local_names[name] = id
        return id

    def _check_subject(self, subject, new_concepts):
        if subject not in self.local_names:
            if subject not in self.kg_concepts and subject not in new_concepts:
                raise Exception("subject error - node %s does not exist!" % subject)
            elif subject not in new_concepts:
                self.additions.add_node(subject)
        else:
            subject = self.local_names[subject]
        return subject

    def _check_object(self, object, new_concepts):
        if object not in self.local_names:
            if object not in self.kg_concepts and object not in new_concepts:
                raise Exception("object error - node %s does not exist!" % object)
            elif object not in new_concepts:
                self.additions.add_node(object)
        else:
            object = self.local_names[object]
        return object

    def _check_type(self, type, new_concepts):
        if type not in self.kg_concepts and type not in new_concepts:
            raise Exception("predicate_type error - node %s does not exist!" % type)
        elif type not in new_concepts:
            self.additions.add_node(type)
        return type

    def name(self, args):
        return str(args[0])

    def type(self, args):
        return str(args[0])

    def subject(self, args):
        return str(args[0])

    def object(self, args):
        return str(args[0])

    def start(self, args):
        return self.additions

class KnowledgeGraph:

    def __init__(self, filename=None, nodes=None):
        self._concept_graph = ConceptGraph(nodes=nodes)
        # self._grammar = r"""
        #     start: (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate)+
        #     unnamed_bipredicate: type "(" subject "," object ")"
        #     unnamed_monopredicate: type "(" subject ")"
        #     named_bipredicate: name "/" type "(" subject "," object ")"
        #     named_monopredicate: name "/" type "(" subject ")"
        #     name: STRING
        #     type: STRING
        #     subject: STRING | (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate) | (unnamed_instance | named_instance)
        #     object: STRING | (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate) | (unnamed_instance | named_instance)
        #     unnamed_instance: type "(" ")"
        #     named_instance: name "/"  type "(" ")"
        #     STRING: /[a-z_A-Z0-9]/+
        #     WHITESPACE: (" " | "\n")+
        #     %ignore WHITESPACE
        # """
        self._grammar = r"""
            start: (bipredicate | monopredicate)+
            bipredicate: (name "/")? type "(" subject "," object ")"
            monopredicate: (name "/")? type "(" subject ")"
            instance: (name "/")? type "(" ")"
            name: STRING
            type: STRING 
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

    def add_entity_type(self, entity_type, supertypes):
        if isinstance(supertypes, list):
            for supertype in supertypes:
                self._concept_graph.add_bipredicate(entity_type, supertype, 'type')
        elif isinstance(supertypes, str):
            self._concept_graph.add_bipredicate(entity_type, supertypes, 'type')
        else:
            raise Exception(":param 'supertypes' must be a list or string!")

    def add_predicate_type(self, predicate_type, supertypes, arg0_types, arg1_types=None):
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
        pass


    def add_property(self, type_, property_dict):
        pass

    # todo - enforce that parameter 'properties' satisfies all supertype properties (need inference?)
    # todo - if supertypes is None, just add a single unspecified node?
    def add_entity_instance(self, supertypes, properties, entity_instance=None):
        if entity_instance is None:
            entity_instance = self._concept_graph._get_next_id()
        if isinstance(supertypes, list):
            for supertype in supertypes:
                self._concept_graph.add_bipredicate(entity_instance, supertype, 'type')
        elif isinstance(supertypes, str):
            self._concept_graph.add_bipredicate(entity_instance, supertypes, 'type')
        else:
            raise Exception(":param 'supertypes' must be a list or string!")
        for label, value in properties.items():
            self._concept_graph.add_bipredicate(entity_instance, value, label)
        return entity_instance

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
        buy(person,store)
        reason(happy,gps)
        t/time(person)
    """

    kg = KnowledgeGraph(nodes=['person','store','icecream',
                               'go','buy','happy','reason','time','type'])
    addition_graph = kg.add_knowledge(text)

    test = 1

