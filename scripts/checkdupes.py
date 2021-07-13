import os
from pprint import pprint
import unittest
import copy
dupe_count=0
exprdupe_count=0
processed=set()
exprs=set()
og=set()
def process_file(filename):
    f = open(filename, "r")
    global dupe_count
    global exprdupe_count
    lines = [line.strip() for line in f]
    for l in lines:
        if "=" in l:
            if "[" in l:
                a = l.replace('[', '').replace(']', '').split(sep='=')[0].split(sep=',')
                for i in a:
                    if i not in processed:
                        processed.add(i.strip())
                    else:
                        dupe_count+=1
                        print(f"Duplicate \"{i}\" in {filename}")
                    if i not in exprs:
                        exprs.add(i.strip())
                        og.add(i.strip())
                    else:
                        exprdupe_count+=1
                        print(f"Duplicate (expression) \"{i}\" in {filename}")
            else:
                a = l.replace(' ', '').split(sep='=')[0].strip()
                if a not in processed:
                    processed.add(a)
                else:
                    dupe_count+=1
                    print(f"Duplicate \"{a}\" in {filename}")
                if a not in exprs:
                        exprs.add(a)
                        og.add(a)
                else:
                    exprdupe_count+=1
                    print(f"Duplicate (expression) \"{a}\" in {filename}")
        elif "expr" in l:
            strin_g = l.split(sep="\"")
            for i in strin_g[1].split(sep=','):
                if i.strip() not in exprs:
                    exprs.add(i.strip())
                #elif i.strip() != strin_g[2].split(sep=',')[-1].replace(')', '').strip():
                elif i.strip() not in og:
                    exprdupe_count+=1
                    print(f"Duplicate (expression) \"{i.strip()}\" in {filename}")


    f.close()



class TestDupes(unittest.TestCase):
     def test_dupes(self):
        for subdir, dirs, files in os.walk("resources/kg_files/kb"):
            for file in files:

                filepath = subdir + os.sep + file
                if filepath.endswith(".kg"):
                    process_file(filepath)
        assert dupe_count == 0, "Duplicates detected, see log for more info"
        assert exprdupe_count == 0, "Duplicates detected, see log for more info"

if __name__ == '__main__':
    unittest.main()
