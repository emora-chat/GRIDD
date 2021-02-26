from GRIDD.data_structures.knowledge_parser import KnowledgeParser

def test_parse_metadata():
    with_metadata = '''
    favorite<predicate>
    animal<entity>
    ufa=favorite(user, a=animal())
    ufa{"coldstart": 1, "cover": 1}
    
    like<predicate>
    udc=drive(user,c=car())
    uld=like(user, udc)
    question(uld)
    udc{"cover": 1}
    uld{"coldstart": 1}
    '''
    cg = KnowledgeParser.from_data(with_metadata)
    assert cg.has('user', 'favorite', 'a')
    assert cg.has('a', 'type', 'animal')
    assert 'coldstart' in cg.features['ufa'] and cg.features['ufa']['coldstart'] == 1
    assert 'cover' in cg.features['ufa'] and cg.features['ufa']['cover'] == 1
    assert cg.has('user', 'drive', 'c')
    assert cg.has('user', 'like', 'udc')
    assert 'coldstart' in cg.features['uld'] and cg.features['uld']['coldstart'] == 1
    assert 'cover' in cg.features['udc'] and cg.features['udc']['cover'] == 1
