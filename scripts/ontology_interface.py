from GRIDD.data_structures.knowledge_base import KnowledgeBase
import os
from os.path import join

def ancestor_chain(concept, kb, types=None):
    if types is None:
        types = {}
    for predicate in kb._concept_graph.predicates(subject=concept, predicate_type='type'):
        supertype = predicate[2]
        types[supertype] = {}
        ancestor_chain(supertype, kb, types[supertype])
    return types

def recursive_print(ancestor_chain, s = None, strings = None):
    if s is None:
        s = ""
        strings = []
    if len(ancestor_chain) > 0:
        for a in ancestor_chain:
            s += a + ' -> '
            strings = recursive_print(ancestor_chain[a], s, strings)
            s = s[:-1*len(a + ' -> ')]
    else:
        s = s[:-4]
        strings.append(s)
    return strings

def details(concept, kb):
    print()
    print('Ancestors:')
    print('-'*20)
    # for ancestor in kb.supertypes(concept):
    #     print(ancestor, end=', ')
    # print()
    ac = ancestor_chain(concept, kb)
    strings = recursive_print(ac)
    for s in strings:
        print(s)
    print()
    print('Descendants:')
    print('-'*20)
    for descendant in kb.subtypes(concept):
        print(descendant, end=', ')
    print('\n')
    print('Expressions:')
    print('-'*20)
    for expression in kb._concept_graph.subjects(concept, 'expr'):
        print(expression.replace('"', ''), end=', ')
    print('\n')

if __name__ == '__main__':

    print('loading kb...')
    files = [join('gridd_files','kb_test', 'kb', file)
             for file in os.listdir(join('gridd_files', 'kb_test', 'kb'))
             if file.endswith('.kg')]
    kb = KnowledgeBase(*files)

    inp = input('>>> ')

    while inp != 'q':
        inp = inp.strip()
        if '_n_' in inp or '_v_' in inp or '_a_' in inp or '_s_' in inp:
            details(inp, kb)
        else:
            concepts = kb._concept_graph.objects('"%s"'%inp, 'expr')
            for concept in concepts:
                print()
                print('#'*30)
                print(concept)
                print('#'*30)
                details(concept, kb)
        print()
        inp = input('>>> ')