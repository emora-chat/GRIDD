
from structpy import specification


@specification
class ConceptCompilerSpec:

    @specification.init
    def CONCEPT_COMPILER(ConceptCompiler):
        parser = ConceptCompiler(set(), {'predicate', 'object', 'type', 'expression', 'imp_rule'}, {'predicate', 'type'})
        return parser

    def compile(compiler, logic_string):
        test = '''
        entity = (object)
        animal = (entity)
        pet = (entity)
        dog = (animal, pet)
        person = (entity)
        group = (entity)
        something = (entity)
        scared = (predicate)
        ;
        
        mary=person()
        chase = (predicate)
        expr = (predicate)
        [excited, happy, heppy] = (predicate)
        [reason, members] = (predicate)
        
        [amphibian, reptile, bird] = (animal, pet) /* this is a comment */
        
        
        /* Here is another comment */
        fido/dog(){"name": "fido", "attrs": {"x": [2, 3], "y": true}}
        
        c=chase(fido, fluffy=pet())
        
        expr("fido, doggo, puppy dog, pooch", fido)
        expr(["fluffy", "fluffers"], fluffy)
        
        reason(c, excited(fido))
        
        g/group()
        
        members(g, [mary, dave=person(), sue:<sue/person() happy(sue)>])
        
        heppy([mary, [dave, sue]])
        
        s/something()
        ;
        
        x/dog() chase(x, y/dog())
        =>
        happy(x) scared(y)
        ;
            
        '''
        rules = '''
        [chase, happy, scared] = (predicate)
        dog = (object)
        fido = dog()
        ;
        

        
        chase(fido, x/dog())
        =>
        scared(fido)
        ;
        
        '''
        # preds, metas = compiler.compile(test)
        preds, metas = compiler.compile(rules)
        for pred in preds:
            print(pred)
        for k, v in metas.items():
            print(k, ':', v)
