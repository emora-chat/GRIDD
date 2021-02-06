
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
import os
from os.path import join
from collections import defaultdict

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

    print('loading kb...')
    kb = KnowledgeBase(kb)
    print('initializing wm...')
    wm = WorkingMemory(kb)
    wm.knowledge_base._knowledge_parser._predicate_transformer.ensure_kb_compatible = False
    print('loading rules...')
    rules = []
    for file in os.listdir(join('gridd_files', 'kb_test', 'rules')):
        if file.endswith('.kg'):
            rules.extend(wm.load_rules_from_file(join('gridd_files', 'kb_test', 'rules', file)))
    print()
    old_solutions = defaultdict(list)
    mode = 'logic'
    if mode == 'logic':
        logic_string = input('>>> ').lower()
        while logic_string != 'q':
            if not logic_string.strip().endswith(';'):
                logic_string += ';'
            wm.load_logic(logic_string)
            wm.pull(1, exclude_on_pull={'type', 'expr'})
            inference_dict = wm.inferences(*rules)

            new_solutions = defaultdict(list)
            for rule, solutions in inference_dict.items():
                for solution in solutions:
                    repeat = False
                    for old in old_solutions[rule]:
                        if solution == old:
                            repeat = True
                            break
                    if not repeat:
                        new_solutions[rule].append(solution)
                        old_solutions[rule].append(solution)

            cgs = wm.apply_implications(new_solutions)
            for cg in cgs:
                wm.concatenate(cg)

            print('*'*20)
            output = wm.ugly_print(exclusions={'is_type', 'object', 'predicate', 'entity', 'post', 'pre'})
            print(output)
            print('*'*20)
            logic_string = input('>>> ')



