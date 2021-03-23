
from structpy import specification


@specification
class KnowledgeParserSpec:

    @specification.init
    def KNOWLEDGE_PARSER(KnowledgeParser):
        parser = KnowledgeParser()
        return parser

    def parse(parser, logic_string):
        test = '''
        
        animal = (entity)
        pet = (entity)
        dog = (animal, pet);
        
        [amphibian, reptile, bird] = (animal, pet) /* this is a comment */
        
        
        /* Here is another comment */
        fido/dog(){"name": "fido", "attrs": {"x": [2, 3], "y": true}}
        
        c/chase(fido, fluffy=pet())
        
        expr("fido, doggo, puppy dog, pooch", fido)
        expr(["fluffy", "fluffers"], fluffy)
        
        reason(c, excited(fido))
        
        g/group()
        
        members(g, [mary, dave=person(), sue:<sue/person() happy(sue)>])
        
        heppy([mary, [dave, sue]])
        
        s/something()
            
        '''
        parser.parse(test)