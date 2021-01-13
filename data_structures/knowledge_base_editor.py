"""

Knowledge Base folder
Rules file
Interactive console:
    Input: logic string of user utterance
    Outputs: Implications

"""

from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory
import os

def generate_file(name):
    if not os.path.exists(name):
        with open(name, 'w') as f:
            f.write('\n')

if __name__ == '__main__':
    # fido=dog() fluffy=dog() chase(fido,fluffy);

    generate_file('kb.kg')
    generate_file('rules.kg')

    kb = KnowledgeBase('kb.kg')

    logic_string = input('>>> ')
    while logic_string != 'q':
        if not logic_string.strip().endswith(';'):
            logic_string += ';'
        wm = WorkingMemory(kb, logic_string)
        wm.pull(2)
        cgs = wm.implications('rules.kg')
        for cg in cgs:
            for s, t, o, i in cg.predicates():
                if t not in ['var', 'is_type']:
                    if o is not None:
                        print('%s(%s, %s) [%s]'%(t,s,o,i))
                    else:
                        print('%s(%s) [%s]' % (t, s, i))
            print()
        logic_string = input('>>> ')