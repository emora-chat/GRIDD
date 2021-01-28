import pytest
from GRIDD.modules.elit_models import ElitModels
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic, NODES, DP_LABELS
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from os.path import join

@pytest.fixture
def elitmodels():
    return ElitModels()

@pytest.fixture
def elit_to_logic():
    kb = KnowledgeBase(join('GRIDD', 'resources', 'kg_files', 'framework_test.kg'))
    template_starter_predicates = [(n, 'is_type') for n in NODES+DP_LABELS]
    template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
    return ElitDPToLogic(kb, template_starter_predicates, template_file)

def test_svdo_simple(elitmodels, elit_to_logic):
    """ Tests constructions of subject-verb-determiner-object """
    sentence = 'I bought a house'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (bought_sp,) = [span for span in mentions.keys() if span.string == 'bought']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    bought_mg = mentions[bought_sp]
    bought_preds = bought_mg.predicates(predicate_type='buy')
    assert len(bought_preds) == 1
    ((s,t,o,i),) = bought_preds
    assert o is not None
    assert bought_mg.has(i, 'focus')
    assert bought_mg.has(i, 'time', 'past')
    assert bought_mg.has('buy', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s,t,o,i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')

    assert len(merges) == 2
    assert ((bought_sp,'subject'),(i_sp,'self')) in merges
    assert ((bought_sp,'object'), (house_sp,'self')) in merges

def test_sv_simple(elitmodels, elit_to_logic):
    """ Tests constructions of subject-verb """
    sentence = 'I walked'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 2
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (walked_sp,) = [span for span in mentions.keys() if span.string == 'walked']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    walked_mg = mentions[walked_sp]
    walked_preds = walked_mg.predicates(predicate_type='walk')
    assert len(walked_preds) == 1
    ((s,t,o,i),) = walked_preds
    assert o is None
    assert walked_mg.has(i, 'focus')
    assert walked_mg.has(i, 'time', 'past')
    assert walked_mg.has('walk', 'center')

    assert len(merges) == 1
    assert ((walked_sp,'subject'),(i_sp,'self')) in merges

def test_slvo(elitmodels, elit_to_logic):
    """ Tests constructions of subj-light_verb-verb-obj """
    sentence = 'I made a call to you'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (call_sp,) = [span for span in mentions.keys() if span.string == 'call']
    (you_sp,) = [span for span in mentions.keys() if span.string == 'you']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    call_mg = mentions[call_sp]
    call_preds = call_mg.predicates(predicate_type='call')
    assert len(call_preds) == 1
    ((s, t, o, i),) = call_preds
    assert o is not None
    assert call_mg.has(i, 'focus')
    assert call_mg.has(i, 'time', 'past')
    assert call_mg.has('call', 'center')

    you_mg = mentions[you_sp]
    assert you_mg.has('emora', 'center')
    assert you_mg.has('emora', 'focus')

    assert len(merges) == 2
    assert ((call_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((call_sp, 'object'), (you_sp, 'self')) in merges

def test_prepositional_phrases(elitmodels, elit_to_logic):
    """ Tests constructions of prepositional phrases """
    sentence = 'I bought a house in Georgia'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 5
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (bought_sp,) = [span for span in mentions.keys() if span.string == 'bought']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']
    (in_sp,) = [span for span in mentions.keys() if span.string == 'in']
    (georgia_sp,) = [span for span in mentions.keys() if span.string == 'georgia']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    bought_mg = mentions[bought_sp]
    bought_preds = bought_mg.predicates(predicate_type='buy')
    assert len(bought_preds) == 1
    ((s, t, o, i),) = bought_preds
    assert o is not None
    assert bought_mg.has(i, 'focus')
    assert bought_mg.has(i, 'time', 'past')
    assert bought_mg.has('buy', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    
    in_mg = mentions[in_sp]
    in_preds = in_mg.predicates(predicate_type='in')
    assert len(in_preds) == 1
    ((s, t, o, i),) = in_preds
    assert o is not None
    assert in_mg.has(i, 'focus')
    assert in_mg.has('in', 'center')
    
    georgia_mg = mentions[georgia_sp]
    assert georgia_mg.has('georgia', 'center')
    assert georgia_mg.has('georgia', 'focus')

    assert len(merges) == 4
    assert ((bought_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((bought_sp, 'object'), (house_sp, 'self')) in merges
    assert ((in_sp, 'subject'), (bought_sp, 'self')) in merges
    assert ((in_sp, 'object'), (georgia_sp, 'self')) in merges

    sentence = 'I walked to the house'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (walked_sp,) = [span for span in mentions.keys() if span.string == 'walked']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']
    (to_sp,) = [span for span in mentions.keys() if span.string == 'to']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    walked_mg = mentions[walked_sp]
    walked_preds = walked_mg.predicates(predicate_type='walk')
    assert len(walked_preds) == 1
    ((s,t,o,i),) = walked_preds
    assert o is None
    assert walked_mg.has(i, 'focus')
    assert walked_mg.has(i, 'time', 'past')
    assert walked_mg.has('walk', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')

    to_mg = mentions[to_sp]
    to_preds = to_mg.predicates(predicate_type='to')
    assert len(to_preds) == 1
    ((s, t, o, i),) = to_preds
    assert o is not None
    assert to_mg.has(i, 'focus')
    assert to_mg.has('to', 'center')

    assert len(merges) == 3
    assert ((walked_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((to_sp, 'subject'), (walked_sp, 'self')) in merges
    assert ((to_sp, 'object'), (house_sp, 'self')) in merges

def test_comp(elitmodels, elit_to_logic):
    """ Tests constructions with comp attachments where comp structure misses nsbj and obj """
    sentence = 'I like to walk'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    # assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (walk_sp,) = [span for span in mentions.keys() if span.string == 'walk']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    like_mg = mentions[like_sp]
    like_preds = like_mg.predicates(predicate_type='like')
    assert len(like_preds) == 1
    ((s, t, o, i),) = like_preds
    assert o is not None
    assert like_mg.has(i, 'focus')
    assert like_mg.has(i, 'time', 'present')
    assert like_mg.has('like', 'center')
    
    walk_mg = mentions[walk_sp]
    walk_preds = walk_mg.predicates(predicate_type='walk')
    assert len(walk_preds) == 1
    ((s, t, o, i),) = walk_preds
    assert o is None
    assert walk_mg.has(i, 'focus')
    assert walk_mg.has('walk', 'center')

    # assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (walk_sp, 'self')) in merges
    assert ((walk_sp, 'subject'), (i_sp, 'self')) in merges


def test_inner_comp_with_obj(elitmodels, elit_to_logic):
    """ Tests constructions with comp attachments where comp structure has obj but no nsbj """
    sentence = 'I like to buy clothes'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    # assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (buy_sp,) = [span for span in mentions.keys() if span.string == 'buy']
    (clothes_sp,) = [span for span in mentions.keys() if span.string == 'clothes']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    like_mg = mentions[like_sp]
    like_preds = like_mg.predicates(predicate_type='like')
    assert len(like_preds) == 1
    ((s, t, o, i),) = like_preds
    assert o is not None
    assert like_mg.has(i, 'focus')
    assert like_mg.has(i, 'time', 'present')
    assert like_mg.has('like', 'center')

    buy_mg = mentions[buy_sp]
    buy_preds = buy_mg.predicates(predicate_type='buy')
    assert len(buy_preds) == 1
    ((s, t, o, i),) = buy_preds
    assert o is not None
    assert buy_mg.has(i, 'focus')
    assert buy_mg.has('buy', 'center')

    clothes_mg = mentions[clothes_sp]
    assert clothes_mg.has('clothing', 'center')
    assert clothes_mg.has('clothing', 'focus')

    # assert len(merges) == 4
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (buy_sp, 'self')) in merges
    assert ((buy_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((buy_sp, 'object'), (clothes_sp, 'self')) in merges

def test_inner_comp_with_nsbj(elitmodels, elit_to_logic):
    """ Tests constructions with comp attachments where comp structure has nsbj but no obj """
    sentence = 'I like when you walk'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    # assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (you_sp,) = [span for span in mentions.keys() if span.string == 'you']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (walk_sp,) = [span for span in mentions.keys() if span.string == 'walk']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    like_mg = mentions[like_sp]
    like_preds = like_mg.predicates(predicate_type='like')
    assert len(like_preds) == 1
    ((s, t, o, i),) = like_preds
    assert o is not None
    assert like_mg.has(i, 'focus')
    assert like_mg.has(i, 'time', 'present')
    assert like_mg.has('like', 'center')

    walk_mg = mentions[walk_sp]
    walk_preds = walk_mg.predicates(predicate_type='walk')
    assert len(walk_preds) == 1
    ((s, t, o, i),) = walk_preds
    assert o is None
    assert walk_mg.has(i, 'focus')
    assert walk_mg.has('walk', 'center')

    you_mg = mentions[you_sp]
    assert you_mg.has('emora', 'center')
    assert you_mg.has('emora', 'focus')

    # assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (walk_sp, 'self')) in merges
    assert ((walk_sp, 'subject'), (you_sp, 'self')) in merges

def test_inner_comp_with_nsbj_obj(elitmodels, elit_to_logic):
    """ Tests constructions with comp attachments where comp structure has both nsbj and obj """
    sentence = 'I like when you buy clothes'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    # assert len(mentions) == 5
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (you_sp,) = [span for span in mentions.keys() if span.string == 'you']
    (buy_sp,) = [span for span in mentions.keys() if span.string == 'buy']
    (clothes_sp,) = [span for span in mentions.keys() if span.string == 'clothes']

    i_mg = mentions[i_sp]
    assert i_mg.has('user', 'center')
    assert i_mg.has('user', 'focus')

    you_mg = mentions[you_sp]
    assert you_mg.has('emora', 'center')
    assert you_mg.has('emora', 'focus')

    like_mg = mentions[like_sp]
    like_preds = like_mg.predicates(predicate_type='like')
    assert len(like_preds) == 1
    ((s, t, o, i),) = like_preds
    assert o is not None
    assert like_mg.has(i, 'focus')
    assert like_mg.has(i, 'time', 'present')
    assert like_mg.has('like', 'center')

    buy_mg = mentions[buy_sp]
    buy_preds = buy_mg.predicates(predicate_type='buy')
    assert len(buy_preds) == 1
    ((s, t, o, i),) = buy_preds
    assert o is not None
    assert buy_mg.has(i, 'focus')
    assert buy_mg.has('buy', 'center')

    # todo - clothes should be instantiated!
    clothes_mg = mentions[clothes_sp]
    assert clothes_mg.has('clothing', 'center')
    assert clothes_mg.has('clothing', 'focus')

    # assert len(merges) == 4
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (buy_sp, 'self')) in merges
    assert ((buy_sp, 'subject'), (you_sp, 'self')) in merges
    assert ((buy_sp, 'object'), (clothes_sp, 'self')) in merges

def test_ref_det(elitmodels, elit_to_logic):
    """ Tests constructions with referential determiners """
    sentence = 'I like the house'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s,t,o,i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    assert house_mg.has(s, 'referential')

    assert len(merges) == 2
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (house_sp, 'self')) in merges


def test_inst_det(elitmodels, elit_to_logic):
    """ Tests constructions with instantiative determiners """
    sentence = 'I like a house'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    assert house_mg.has(s, 'instantiative')

    assert len(merges) == 2
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (house_sp, 'self')) in merges

def test_poss_pron(elitmodels, elit_to_logic):
    """ Tests constructions with possessives (pronouns and nouns) """
    sentence = 'I like my house'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (my_sp,) = [span for span in mentions.keys() if span.string == 'my']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    my_mg = mentions[my_sp]
    my_insts = my_mg.predicates(predicate_type='possess')
    assert len(my_insts) == 1
    ((s, t, o, i),) = my_insts
    assert o is not None
    assert s == 'user'
    assert my_mg.has(i, 'focus')
    assert my_mg.has('user', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    possess_insts = house_mg.predicates(predicate_type='possess', object=s)
    assert len(possess_insts) == 0

    assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (house_sp, 'self')) in merges
    assert ((my_sp, 'object'), (house_sp, 'self')) in merges

    sentence = "I like John's house"
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (john_sp,) = [span for span in mentions.keys() if span.string == 'john']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    john_mg = mentions[john_sp]
    john_insts = john_mg.predicates(predicate_type='possess')
    assert len(john_insts) == 1
    ((s, t, o, i),) = john_insts
    assert o is not None
    assert s == 'john'
    assert john_mg.has(i, 'focus')
    assert john_mg.has('john', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    possess_insts = house_mg.predicates(predicate_type='possess', object=s)
    assert len(possess_insts) == 0
    
    assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (house_sp, 'self')) in merges
    assert ((john_sp, 'object'), (house_sp, 'self')) in merges

    sentence = "I like Johns house"
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (john_sp,) = [span for span in mentions.keys() if span.string == 'johns']
    (house_sp,) = [span for span in mentions.keys() if span.string == 'house']

    john_mg = mentions[john_sp]
    john_insts = john_mg.predicates(predicate_type='possess')
    assert len(john_insts) == 1
    ((s, t, o, i),) = john_insts
    assert o is not None
    assert s == 'john'
    assert john_mg.has(i, 'focus')
    assert john_mg.has('john', 'center')

    house_mg = mentions[house_sp]
    house_insts = house_mg.predicates(predicate_type='type', object='house')
    assert len(house_insts) == 1
    ((s, t, o, i),) = house_insts
    assert house_mg.has(s, 'focus')
    assert house_mg.has('house', 'center')
    possess_insts = house_mg.predicates(predicate_type='possess', object=s)
    assert len(possess_insts) == 0

    assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (house_sp, 'self')) in merges
    assert ((john_sp, 'object'), (house_sp, 'self')) in merges
    
def test_compound(elitmodels, elit_to_logic):
    """ Tests constructions with compound attachments """
    sentence = 'I like New York'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 4
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (like_sp,) = [span for span in mentions.keys() if span.string == 'like']
    (new_sp,) = [span for span in mentions.keys() if span.string == 'new']
    (york_sp,) = [span for span in mentions.keys() if span.string == 'york']

    new_mg = mentions[new_sp]
    new_insts = new_mg.predicates(predicate_type='compound')
    assert len(new_insts) == 1
    ((s, t, o, i),) = new_insts
    assert o is not None
    assert new_mg.has(i, 'focus')
    assert new_mg.has('new', 'center')

    york_mg = mentions[york_sp]
    assert york_mg.has('york', 'focus')
    assert york_mg.has('york', 'center')

    assert len(merges) == 3
    assert ((like_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((like_sp, 'object'), (york_sp, 'self')) in merges
    assert ((new_sp, 'object'), (york_sp, 'self')) in merges

def test_adv(elitmodels, elit_to_logic):
    """ Tests constructions with adverb attachments """
    sentence = 'I walked quickly'
    tok, pos, dp = elitmodels(sentence)
    mentions, merges = elit_to_logic(tok, pos, dp)

    assert len(mentions) == 3
    (i_sp,) = [span for span in mentions.keys() if span.string == 'i']
    (walked_sp,) = [span for span in mentions.keys() if span.string == 'walked']
    (quickly_sp,) = [span for span in mentions.keys() if span.string == 'quickly']

    quickly_mg = mentions[quickly_sp]
    quick_insts = quickly_mg.predicates(predicate_type='qualifier')
    assert len(quick_insts) == 1
    ((s, t, o, i),) = quick_insts
    assert o is not None
    assert quickly_mg.has(i, 'focus')
    assert quickly_mg.has('quick', 'center')

    assert len(merges) == 2
    assert ((walked_sp, 'subject'), (i_sp, 'self')) in merges
    assert ((quickly_sp, 'subject'), (walked_sp, 'self')) in merges










