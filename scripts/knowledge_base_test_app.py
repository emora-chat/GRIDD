
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.inference_engine import InferenceEngine
import os, time
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
    st = time.time()
    kb = KnowledgeBase(kb)
    print('\tElapsed: %.3f'%(time.time()-st))
    print('initializing wm...')
    wm = WorkingMemory(kb)
    print('initializing inference engine...')
    inference_engine = InferenceEngine(join('gridd_files', 'kb_test', 'rules'))

    old_solutions = defaultdict(list)
    mode = 'logic'
    if mode == 'logic':
        logic_string = input('>>> ').lower()
        while logic_string != 'q':
            logic_graph = KnowledgeParser.from_data(logic_string)
            wm.concatenate(logic_graph)
            wm.pull(1, exclude_on_pull={'type', 'expr'})
            inference_dict = inference_engine.infer(wm)

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

            implications = inference_engine.apply(solutions=new_solutions)
            for rule, cgs in implications.items():
                for cg in cgs:
                    wm.concatenate(cg)

            print('*'*20)
            output = wm.ugly_print(exclusions={'is_type', 'object', 'predicate', 'entity', 'post', 'pre'})
            print(output)
            print('*'*20)
            logic_string = input('>>> ')



