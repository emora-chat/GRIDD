from lark import Lark, Transformer
from concept_graph import ConceptGraph

class PredicateTransformer(Transformer):

    def __init__(self, kg):
        super().__init__()
        self.kg = kg

    def unnamed_bipredicate(self, args):
        type, subject, object = args
        return self.kg._concept_graph.add_bipredicate(subject, object, type)

    def unnamed_monopredicate(self, args):
        type, subject = args
        return self.kg._concept_graph.add_monopredicate(subject, type)

    def named_bipredicate(self, args):
        name, type, subject, object = args
        return self.kg._concept_graph.add_bipredicate(subject, object, type, predicate_id=name)

    def named_monopredicate(self, args):
        name, type, subject = args
        return self.kg._concept_graph.add_monopredicate(subject, type, predicate_id=name)

    def name(self, args):
        return str(args[0])

    def type(self, args):
        return str(args[0])

    def subject(self, args):
        return str(args[0])

    def object(self, args):
        return str(args[0])

    def named_instance(self, args):
        name, type = args
        self.kg._concept_graph.add_bipredicate(name, type, 'type')
        return name

    def unnamed_instance(self, args):
        type = args[0]
        name = self.kg._concept_graph.get_next_id()
        self.kg._concept_graph.add_bipredicate(name, type, 'type')
        return name

class KnowledgeGraph:

    def __init__(self, filename=None):
        self._concept_graph = ConceptGraph()
        self._grammar = r"""
            start: (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate)+
            unnamed_bipredicate: type "(" subject "," object ")"
            unnamed_monopredicate: type "(" subject ")"
            named_bipredicate: name "/" type "(" subject "," object ")" 
            named_monopredicate: name "/" type "(" subject ")"
            name: STRING
            type: STRING 
            subject: STRING | (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate) | (unnamed_instance | named_instance)
            object: STRING | (unnamed_bipredicate | named_bipredicate | unnamed_monopredicate | named_monopredicate) | (unnamed_instance | named_instance)
            unnamed_instance: type "(" ")"
            named_instance: name "/"  type "(" ")"
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
        # print(tree.pretty())
        self.predicate_transformer.transform(tree)

    def add_entity_type(self, entity_type, supertypes):
        if isinstance(supertypes, list):
            for supertype in supertypes:
                self.kg._concept_graph.add_bipredicate(entity_type, supertype, 'type')
        elif isinstance(supertypes, str):
            self.kg._concept_graph.add_bipredicate(entity_type, supertypes, 'type')
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
            entity_instance = self.kg._concept_graph.get_next_id()
        if isinstance(supertypes, list):
            for supertype in supertypes:
                self.kg._concept_graph.add_bipredicate(entity_instance, supertype, 'type')
        elif isinstance(supertypes, str):
            self.kg._concept_graph.add_bipredicate(entity_instance, supertypes, 'type')
        else:
            raise Exception(":param 'supertypes' must be a list or string!")
        for label, value in properties.items():
            self.kg._concept_graph.add_bipredicate(entity_instance, value, label)
        return entity_instance

if __name__ == '__main__':

    text = """
    test(me, you())
    reason(reason(hu/happy(user_2), gus/go(user_2, store1)), bus/buy(user_2, i0/icecream()))
    time(gus, past)
    time(bus, past)
    type(i0, chocolate)
    """

    kg = KnowledgeGraph()
    kg.add_knowledge(text)


