
from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory
import os
from os.path import join
from utilities import collect


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
        logic_string = input('>>> ')
        while logic_string != 'q':
            if not logic_string.strip().endswith(';'):
                logic_string += ';'
            wm = WorkingMemory(kb, logic_string)
            wm.pull(2)
            rules = collect(join('gridd_files', 'kb_test', 'rules'), extension='.kg')
            sols = wm.inferences(*rules)
            unique_sols = {}
            for r, ss in sols.items():
                for s in ss:
                    s = frozenset(s.items())
                    if (r, s) not in old_solutions:
                        old_solutions.add((r, s))
                        if r not in unique_sols:
                            unique_sols[r] = set()
                        unique_sols[r].add(s)
            unique_sols = {r: [{a: b for a, b in s} for s in ss] for r, ss in unique_sols.items()}
            cgs = wm.implications(solutions=unique_sols)
            for cg in cgs:
                print(cg.pretty_print())
                print('\n' + '*'*20 + '\n')
                wm.concatenate(cg)
            logic_string = input('>>> ')

    elif mode == 'lang':
        from chatbot import Chatbot
        chatbot = Chatbot(kb)

        lang_string = input('>>> ')
        while lang_string != 'q':
            wm = WorkingMemory(kb)
            wm.pull(2)
            chatbot.run([{'text': lang_string}], wm)
            cgs = wm.implications('rules.kg')
            for cg in cgs:
                print(cg.pretty_print())
                print()
            lang_string = input('>>> ')


