
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import re

def to_new(old_filename, new_filename):
    with open(old_filename) as f:
        s = f.read()
    lines = [line.strip() for line in s.split('\n')]
    newlines = []
    for line in lines:
        typedef = re.match(r'(.*?)<(.*?)>', line)
        exprdef = re.match(r'(.*?)\[(.*?)]', line)
        if typedef:
            declared = typedef.group(1)
            supertypes = typedef.group(2)
            newlines.append(f'{declared} = ({supertypes})')
        elif exprdef:
            declared = exprdef.group(1)
            expressions = exprdef.group(2)
            expressions = ', '.join([f'"{e.strip()}"' for e in expressions.split(',')])
            newlines.append(f'expr([{expressions}], {declared})')
        else:
            newlines.append(line)
    with open(new_filename, 'w') as f:
        f.write('\n'.join(newlines))
    return newlines

if __name__ == '__main__':
    Tk().withdraw()
    filename = askopenfilename()
    new_filename = asksaveasfilename()
    to_new(filename, new_filename)
