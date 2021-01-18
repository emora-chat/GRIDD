
from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory
import os

def generate_file(name):
    if not os.path.exists(name):
        with open(name, 'w') as f:
            f.write('\n')



if __name__ == '__main__':
    generate_file('kb.kg')
    generate_file('rules.kg')

    kb = KnowledgeBase('kb.kg')

    mode = 'logic'
    if mode == 'logic':
        logic_string = input('>>> ')
        while logic_string != 'q':
            if not logic_string.strip().endswith(';'):
                logic_string += ';'
            wm = WorkingMemory(kb, logic_string)
            wm.pull(2)
            cgs = wm.implications('rules.kg')
            for cg in cgs:
                print(cg.pretty_print())
                print()
            logic_string = input('>>> ')
    elif mode == 'lang':
        from main import build_dm
        dm = build_dm(kb, debug=False)

        lang_string = input('>>> ')
        while lang_string != 'q':
            wm = WorkingMemory(kb)
            wm.pull(2)
            dm.run([{'text': lang_string}], wm)
            cgs = wm.implications('rules.kg')
            for cg in cgs:
                print(cg.pretty_print())
                print()
            lang_string = input('>>> ')


