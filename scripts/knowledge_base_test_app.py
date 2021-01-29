
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
import os
from os.path import join
from GRIDD.utilities import collect


if __name__ == '__main__':
    if not os.path.exists('gridd_files'):
        os.mkdir('gridd_files')
    if not os.path.exists(join('gridd_files', 'kb_test')):
        os.mkdir(join('gridd_files', 'kb_test'))
    rules = join('gridd_files', 'kb_test', 'rules')
    if not os.path.exists(rules):
        os.mkdir(rules)
        with open(join(rules, 'rules.kg'), 'w') as f:
            f.write('\n')
    kb = join('gridd_files', 'kb_test', 'kb')
    if not os.path.exists(kb):
        os.mkdir(kb)
        with open(join(kb, 'kb.kg'), 'w') as f:
            f.write('\n')

    kb = KnowledgeBase(kb)
    old_solutions = set()
    mode = 'logic'
    if mode == 'logic':
        wm = WorkingMemory(kb)
        wm.knowledge_base._knowledge_parser._predicate_transformer.ensure_kb_compatible = False
        logic_string = input('>>> ')
        while logic_string != 'q':
            if not logic_string.strip().endswith(';'):
                logic_string += ';'
            wm.load(logic_string)
            wm.pull(2)
            rules = [join('gridd_files', 'kb_test', 'rules', file)
                     for file in os.listdir(join('gridd_files', 'kb_test', 'rules'))
                     if file.endswith('.kg')]
            cgs = wm.implications(*rules)
            for cg in cgs:
                print(cg.pretty_print())
                print('*'*20)
                wm.concatenate(cg)
            logic_string = input('>>> ')



