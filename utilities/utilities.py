
from math import log
import os
from inspect import getmembers, isfunction

CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _get_digit(x, i, n=10):
    return x // n**i % n

def _get_num_digits(x, n=10):
    if x > 0:
        digits = int(log(x, n)) + 1
    elif x == 0:
        digits = 1
    else:
        digits = int(log(-x, n)) + 2
    return digits

def identification_string(x, chars=None):
    string = ''
    if chars is None:
        chars = '0123456789'
    n = len(chars)
    for i in range(_get_num_digits(x, n)):
        d = _get_digit(x, i, n)
        string = chars[d] + string
    return string

def collect(*files_folders_or_strings, extension=None, directory=None):
    collected = []
    files_or_strings = []
    for ffs in files_folders_or_strings:
        if isinstance(ffs, str) and os.path.isdir(ffs):
            for fs in os.listdir(ffs):
                if not extension or fs.endswith(extension):
                    files_or_strings.append(os.path.join(ffs, fs))
        else:
            files_or_strings.append(ffs)
    for ffs in sorted(files_or_strings):
        if not extension or (isinstance(ffs, str) and ffs.endswith(extension)):
            with open(ffs, 'r') as f:
                collected.append(f.read())
        else:
            collected.append(ffs)
    return collected

class hashabledict(dict):
  def __key(self):
    return tuple((k,self[k]) for k in sorted(self))
  def __hash__(self):
    return hash(self.__key())
  def __eq__(self, other):
    self_id = self.__key()
    other_id = other.__key()
    return self_id == other_id

class Counter:
    def __init__(self, value=0):
        self.value = value
    def __iadd__(self, other):
        self.value += other
        return self
    def __int__(self):
        return self.value

def uniquify(collection):
    ids = {}
    for item in collection:
        ids[id(item)] = item
    return list(ids.values())

def combinations(*itemsets):
    c = [[]]
    for itemset in list(itemsets):
        if itemset:
            cn = []
            for item in list(itemset):
                ce = [list(e) for e in c]
                for sol in ce:
                    sol.append(item)
                cn.extend(ce)
            c = cn
    return c

def operators(module):
    d = dict(getmembers(module, isfunction))
    for v in list(d.values()):
        if hasattr(v, 'aliases'):
            for alias in v.aliases:
                d[alias] = v
    return {k: v for k, v in d.items() if not k.startswith('_')}

class aliases:
    def __init__(self, *aliases):
        self.aliases = aliases
    def __call__(self, fn):
        fn.aliases = self.aliases
        return fn

