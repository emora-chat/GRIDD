
from GRIDD.data_structures.concept_graph import ConceptGraph

PAST_VB = ['vbd', 'vbn']
PRES_VB = ['vbp', 'vbz', 'vbg', 'vb']
ADJ = ['jj', 'jjr', 'jjs']
NOUN = ['nn', 'nns', 'nnp', 'nnps', 'prp']
PRONOUN = ['prp', 'prpds']
ADV = ['rb', 'rbr', 'rbs']
QUEST = ['wdt', 'wp', 'wpds', 'wrb']
INTERJ = ['uh']
ALLOW_SINGLE = ['rp', 'fw', 'cd', 'dt', 'ex', 'adj', 'noun', 'pron', 'adv', 'interj', 'verb', 'question_word']

ADVCL_INDICATOR = ['adv', 'aux', 'mark', 'case']
ACL_INDICATOR = ['aux', 'mark', 'case']
SUBJECTS = ['nsbj', 'csbj']

TENSEFUL_AUX = ['go', 'do', 'be']
PRECEDE_LABELS = ['aux', 'modal', 'obj', 'cop']

POS_MAP = {'in': 'prepo',
           'to': 'pos_to',
           'uh': 'intrj'}

def pos_mapper(n):
    n = n.lower()
    return POS_MAP.get(n, n).replace('$', 'ds')

def generate_elit_dp_ontology():
    cg = ConceptGraph(namespace='o_')
    for n in ['verb', 'noun', 'adj', 'pron', 'adv', 'question_word', 'interj']:
        cg.add(n, 'type', 'pstg')
    for n in ['past_tense', 'present_tense']:
        cg.add(pos_mapper(n), 'type', 'verb')
    for n in PAST_VB:
        cg.add(pos_mapper(n), 'type', 'past_tense')
    for n in PRES_VB:
        cg.add(pos_mapper(n), 'type', 'present_tense')
    for n in ADJ:
        cg.add(pos_mapper(n), 'type', 'adj')
    for n in NOUN:
        cg.add(pos_mapper(n), 'type', 'noun')
    for n in PRONOUN:
        cg.add(pos_mapper(n), 'type', 'pron')
    for n in ADV:
        cg.add(pos_mapper(n), 'type', 'adv')
    for n in QUEST:
        cg.add(pos_mapper(n), 'type', 'question_word')
    for n in INTERJ:
        cg.add(pos_mapper(n), 'type', 'interj')
    for n in ALLOW_SINGLE:
        cg.add(pos_mapper(n), 'type', 'allow_single')
    for n in ADVCL_INDICATOR:
        cg.add(pos_mapper(n), 'type', 'advcl_indicator')
    for n in ACL_INDICATOR:
        cg.add(pos_mapper(n), 'type', 'acl_indicator')
    for n in SUBJECTS:
        cg.add(pos_mapper(n), 'type', 'sbj')
    return cg