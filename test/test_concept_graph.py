from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.globals import *

def test_parse_metadata():
    with_metadata = '''
    favorite<predicate>
    animal<entity>
    ufa=favorite(user, a=animal())
    ufa{"coldstart": 1, "test": 1}
    
    like<predicate>
    udc=drive(user,c=car())
    uld=like(user, udc)
    question(user, uld)
    udc{"test": 1}
    uld{"coldstart": 1}
    '''
    cg = KnowledgeParser.from_data(with_metadata)
    assert cg.has('user', 'favorite', 'a')
    assert cg.has('a', 'type', 'animal')
    assert COLDSTART in cg.features['ufa'] and cg.features['ufa'][COLDSTART] == 1
    assert 'test' in cg.features['ufa'] and cg.features['ufa']['test'] == 1
    assert cg.has('user', 'drive', 'c')
    assert cg.has('user', 'like', 'udc')
    assert COLDSTART in cg.features['uld'] and cg.features['uld'][COLDSTART] == 1
    assert 'test' in cg.features['udc'] and cg.features['udc']['test'] == 1
