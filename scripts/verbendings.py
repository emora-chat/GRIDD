import os
nonpredicates=set(["entity", "unknown", "object"])
predicates=set()
predicates.add("predicate")
initialmap={}
exprsexisting=set()

def process_file(filename, initialmap):
    f = open(filename, "r")
    global dupe_count
    lines = [line.rstrip() for line in f]
    for l in lines:
        if "=" in l:
            rightside=l.replace('[', '').replace(']', '').replace(' ', '').split(sep='=')[1].split(sep=',')[0].replace('(', '').replace(')', '')
            if "[" in l:
                a = l.replace('[', '').replace(']', '').replace(' ', '').split(sep='=')[0].split(sep=',')
                for i in a:
                    if i not in initialmap:
                        initialmap[i]=rightside
            else:
                a = l.replace(' ', '').split(sep='=')[0]
                if a not in initialmap:
                    initialmap[a]=rightside
    f.close()

def process_file_expr(filename):
    f = open(filename, "r")
    global exprsexisting
    lines = [line.strip() for line in f]
    for l in lines:
        if "=" in l:
            if "[" in l:
                a = l.replace('[', '').replace(']', '').split(sep='=')[0].split(sep=',')
                for i in a:
                    if i not in exprsexisting:
                        exprsexisting.add(i.strip())
            else:
                a = l.replace(' ', '').split(sep='=')[0].strip()
                if a not in exprsexisting:
                        exprsexisting.add(a)
        elif "expr" in l:
            strin_g = l.split(sep="\"")
            for i in strin_g[1].split(sep=','):
                if i.strip() not in exprsexisting:
                    exprsexisting.add(i.strip())
    f.close()


## Get Predicate Inheritants  ##
for subdir, dirs, files in os.walk("resources/kg_files/kb"):
            for file in files:

                filepath = subdir + os.sep + file
                if filepath.endswith(".kg"):
                    process_file(filepath, initialmap)

total = len(initialmap)
preds=0
others=0

while True:
    added=False
    for key, value in initialmap.items():
        if value in predicates and key not in predicates:
            predicates.add(key)
            preds+=1
            added=True
        elif value in nonpredicates and key not in predicates:
            nonpredicates.add(key)
            others+=1
    if not added:
        break



#find verbs
import nltk
nltk.download('wordnet')
verbs=set()
from nltk.corpus import wordnet as wn
predicates.remove('predicate')

for w in predicates:
    try:
        tmp = wn.synsets(w)[0].pos()
        if tmp not in "sar":
            verbs.add(w)
    except:
        pass


for subdir, dirs, files in os.walk("resources/kg_files/kb"):
            for file in files:

                filepath = subdir + os.sep + file
                if filepath.endswith(".kg") and  "expressions.kg" != file:
                    process_file_expr(filepath)
print(f"Existing length:{len(exprsexisting)}, Verbs length: {verbs}")
#print(verbs)
from word_forms.lemmatizer import lemmatize
from word_forms.word_forms import get_word_forms

exprs=[]
verbmap={}
for i in verbs:
    try:
        a = get_word_forms(i)
        #print(a['v'])
        for j in a['v']:
            if j not in exprsexisting:
                exprs.append(j)
                verbmap[j]=i
                exprsexisting.add(j)
    except:
        pass

f = open(f"resources{os.sep}kg_files{os.sep}kb{os.sep}expressions.kg", "w")
for i in exprs:
    f.write(f"expr(\"{i}\",{verbmap[i]})\n")
f.close()

