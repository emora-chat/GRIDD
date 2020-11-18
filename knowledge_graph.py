from lark import Lark

if __name__ == '__main__':

    grammar = r"""
    start: predicate+
 
    predicate: (name "/")? ((type "(" subject "," object ")") | (type "(" subject ")"))
    
    name: STRING
    type: STRING 
    subject: STRING | predicate | instance
    object: STRING | predicate | instance
    instance: (name "/")? type "(" ")"
    STRING: ("a".."z")+
    
    WHITESPACE: (" " | "\n")+
    %ignore WHITESPACE
    """

    text = """
    reason(reason(hu/happy(user), gus/go(user, store)), bus/buy(user, i/icecream()))
    time(gus, past)
    time(bus, past)
    type(i, chocolate)
    """

    parser = Lark(grammar, parser="earley")  # Scannerless Earley is the default

    print(parser.parse(text).pretty())