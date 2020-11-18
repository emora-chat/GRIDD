from lark import Lark, Transformer
from concept_graph import ConceptGraph

class PredicateTransformer(Transformer):

    def __init__(self, kg):
        self.kg = kg

    def start(self, args):
        pass

    def unnamed_bipredicate(self, args):
        type, subject, object = args
        self.kg._concept_graph.add_bipredicate(type, subject, object)

    def unnamed_monopredicate(self, args):
        type, subject = args
        self.kg._concept_graph.add_bipredicate(type, subject)

    def named_bipredicate(self, args):
        name, type, subject, object = args
        self.kg._concept_graph.add_bipredicate(type, subject, object, predicate_id=name)

    def named_monopredicate(self, args):
        name, type, subject = args
        self.kg._concept_graph.add_bipredicate(type, subject, predicate_id=name)

    def name(self, args):
        return str(args[0])

    def type(self, args):
        return str(args[0])

    def subject(self, args):
        return str(args[0])

    def object(self, args):
        return str(args[0])

    def instance(self, args):
        pass

class KnowledgeGraph:

    def __init__(self, edges=None, nodes=None):
        self._concept_graph = ConceptGraph(edges, nodes)
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

    def add_knowledge(self, input):
        tree = self.parser.parse(input)
        print(tree.pretty())
        # self.predicate_transformer.transform(tree)



if __name__ == '__main__':

    text = """
    test(me, you)
    reason(reason(hu/happy(user_2), gus/go(user_2, store1)), bus/buy(user_2, i/icecream()))
    time(gus, past)
    time(bus, past)
    type(i, chocolate)
    """

    kg = KnowledgeGraph()
    kg.add_knowledge(text)


