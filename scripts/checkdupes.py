import os
dupe_count=0
processed=set()

def process_file(filename):
    f = open(filename, "r")
    global dupe_count
    lines = [line.rstrip() for line in f]
   # print(filename)
    for l in lines:
       # print(l)
        if "=" in l:
            if "[" in l:
               # print(l)
                a = l.replace('[', '').replace(']', '').replace(' ', '').split(sep='=')[0].split(sep=',')
               # print(a)
                for i in a:
                    if i not in processed:
                        processed.add(i)
                      #  print(i)
                    else:
                        dupe_count+=1
                        print(f"Duplicate {i} in {filename}")
            else:
                a = l.replace(' ', '').split(sep='=')[0]
             #   print(f"{a}, {filename}")
                if a not in processed:
                    processed.add(a)
                    #print(a)
                else:
                    dupe_count+=1
                    print(f"Duplicate \"{a}\" in {filename}")
    f.close()


    
import os

for subdir, dirs, files in os.walk("GRIDD/resources/kg_files/kb"):
    for file in files:
        #print os.path.join(subdir, file)
        filepath = subdir + os.sep + file
        #print(filepath)
        if filepath.endswith(".kg"):
            process_file(filepath)
print(dupe_count)
