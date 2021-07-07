import os
from globals import *

def extract():
    rules = ""
    count = 0
    with open(os.path.join('GRIDD', 'docs', 'parsing_to_logic_graph.md')) as f:
        lines = f.readlines()
        start = False
        for line in lines:
            if '</details>' in line:
                start = False
            if start:
                rules += line.strip() + '\n'
                if '->' in line or '=>' in line:
                    count += 1
            if '<summary>' in line:
                start = True

    with open(os.path.join('GRIDD', 'resources', KB_FOLDERNAME, 'elit_dp_templates.kg'), 'w') as f:
        f.write(rules)

    print('\nWrote %d parse-to-logic rules'%count)

if __name__ == '__main__':
    extract()