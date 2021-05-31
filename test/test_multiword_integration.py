
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.globals import *
from GRIDD.intcore_chatbot_server import ChatbotServer
from GRIDD import intcore_server_globals
intcore_server_globals.INFERENCE = True
intcore_server_globals.IS_SERIALIZING = False
intcore_server_globals.LOCAL = True

EXCL = {USER_AWARE, SPAN_REF, SPAN_DEF}

def test_simple_integration():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    for=predicate()
    dinner=object()
    pad_thai=object()
    expr("pad thai", pad_thai)
    '''
    s = "I like pad thai for dinner"
    rule = ConceptGraph('''
    time(l/like(user, pad_thai), now)
    for(l, dinner)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()



def test_multiple_multiword():
    kb = '''
    user=object()
    expr("i", user)
    eat=predicate()
    memorial_day=object()
    expr("memorial day", memorial_day)
    pad_thai=object()
    expr("pad thai", pad_thai)
    '''
    s = "I ate pad thai Memorial Day"
    rule = ConceptGraph('''
    time(l/eat(user, pad_thai), past)
    qualifier(l, memorial_day)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()

def test_containment():
    kb = '''
    user=object()
    expr("i", user)
    see=predicate()
    barbie_doll=object()
    expr("barbie doll", barbie_doll)
    barbie_dolls=object()
    expr("the barbie dolls", barbie_dolls)
    '''
    s = "I saw the barbie dolls"
    rule = ConceptGraph('''
    time(l/see(user, barbie_dolls), past)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1

def test_partial_overlap_and_multiparent_dp():
    kb = '''
    user=object()
    expr("i", user)
    see=predicate()
    felix_the_fox=object()
    expr("felix the fox", felix_the_fox)
    fox_trainer=object()
    expr("fox trainer", fox_trainer)
    trainer=object()
    '''
    s = "I saw Felix the fox trainer"
    rule = ConceptGraph('''
    time(l/see(user, felix_the_fox), past)
    appositive(felix_the_fox, trainer())
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1

def test_surface_form_vs_lemma_priority():
    kb = '''
    user=object()
    expr("i", user)
    see=predicate()
    barbie_doll=object()
    expr("barbie doll", barbie_doll)
    barbie_dolls=object()
    expr("barbie dolls", barbie_dolls)
    '''
    s = "I saw the barbie dolls"
    rule = ConceptGraph('''
    time(l/see(user, barbie_dolls()), past)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1

def test_apostrophe_multiword():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    eat=predicate()
    mcdonalds=object()
    expr("mcdonald 's", mcdonalds)
    in=predicate()
    school=object()  
    '''
    s = "I like eating mcdonald's"
    rule = ConceptGraph('''
    time(l/like(user, eat(user, mcdonalds)), now)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1

def test_multiparent_dependency_relations():
    kb = '''
    user=object()
    expr("i", user)
    walk=predicate()
    two=object()
    mile=object()
    behind=object()
    kroger=object()
    two_miles_behind=object()
    expr("two miles behind", two_miles_behind)
    '''
    s = "I walked two miles behind kroger"
    rule = ConceptGraph('''
    time(l/walk(user), past)
    qualifier(l, two_miles_behind)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()
    # currently, multiwords cannot act as predicates so the `behind` relations are lost

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1

def test_hard_multiword():
    kb = '''
    see=predicate()
    felix_the_fox=object()
    expr("felix the fox", felix_the_fox)
    tfath=object()
    expr("the fox and the hound", tfath)
    fox=object()
    felix=object()
    '''
    s = "Felix the fox and the hound saw a fox"
    rule = ConceptGraph('''
    time(see(felix, fox()), past)
    appositive(felix, tfath)
    conjunct(felix, tfath)
    -> is_correct ->
    assert(true)
    ''', namespace='r_').rules()
    # not entirely sure why conjunct is added but conjunct_type is not (something to do with link vs center formulations),
    # but its acceptable

    c = ChatbotServer([kb], [], [])
    c.full_init('cpu')
    wm = c.dialogue_intcore.working_memory.copy()
    wm = c.run_mention_merge(s, wm, {'turn_index': -1})
    i = InferenceEngine()
    results = i.infer(wm, rule)
    print('\n-----------------\n' + s + '\n-----------------')
    print(wm.pretty_print(EXCL))
    print()
    assert 'is_correct' in results and len(results['is_correct'][2]) == 1