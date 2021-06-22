import os
import unittest
dupe_count=0
processed=set()

def process_file(filename):
    f = open(filename, "r")
    global dupe_count
    lines = [line.rstrip() for line in f]
    for l in lines:
        if "=" in l:
            if "[" in l:
                a = l.replace('[', '').replace(']', '').replace(' ', '').split(sep='=')[0].split(sep=',')
                for i in a:
                    if i not in processed:
                        processed.add(i)
                    else:
                        dupe_count+=1
                        print(f"Duplicate \"{i}\" in {filename}")
            else:
                a = l.replace(' ', '').split(sep='=')[0]
                if a not in processed:
                    processed.add(a)
                else:
                    dupe_count+=1
                    print(f"Duplicate \"{a}\" in {filename}")
    f.close()



class TestDupes(unittest.TestCase):
     def test_dupes(self):
        for subdir, dirs, files in os.walk("resources/kg_files/kb"):
            for file in files:

                filepath = subdir + os.sep + file
                if filepath.endswith(".kg"):
                    process_file(filepath)
        assert dupe_count == 0, "Duplicates detected, see log for more info"

if __name__ == '__main__':
    unittest.main()