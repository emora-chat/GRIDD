
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.globals import *
from GRIDD.intcore_chatbot_server import ChatbotServer
from GRIDD import intcore_server_globals
intcore_server_globals.INFERENCE = True
intcore_server_globals.IS_SERIALIZING = False
intcore_server_globals.LOCAL = True

EXCL = {USER_AWARE, SPAN_REF, SPAN_DEF}

def test_no_overlap_no_decomposition():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    '''
    s = "I like Barack Obama"
    rule = ConceptGraph('''
    time(l/like(user, person_ner()), now)
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

def test_yes_overlap_no_decomposition():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    cheesecake_factory=entity()
    expr("cheesecake factory", cheesecake_factory)
    '''
    s = "I like The Cheesecake Factory"
    rule = ConceptGraph('''
    time(l/like(user, cheesecake_factory()), now)
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

def test_no_overlap_yes_decomposition():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    the=object()
    cheesecake=entity()
    factory=entity()
    '''
    s = "I like The Cheesecake Factory"
    rule = ConceptGraph('''
    time(l/like(user, f/factory()), now)
    cheesecake(f)
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

def test_yes_overlap_yes_decomposition():
    kb = '''
    user=object()
    expr("i", user)
    like=predicate()
    cheesecake_factory=entity()
    expr("cheesecake factory", cheesecake_factory)
    cheesecake=entity()
    factory=entity()
    '''
    s = "I like The Cheesecake Factory"
    rule = ConceptGraph('''
    time(l/like(user, cheesecake_factory()), now)
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
