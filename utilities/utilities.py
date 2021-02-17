
from math import log
import os
from structpy.map import Bimap

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

class IdNamespace(Bimap):

    def __init__(self, items=None, namespace='', chars=None):
        Bimap.__init__(self)
        self.namespace = namespace
        self.chars = chars
        self.counter = 0
        if items is not None:
            for item in items:
                self.get(item)

    def get(self, obj=None):
        if obj is None:
            if self.namespace is not int:
                ident = self.namespace + identification_string(self.counter, self.chars)
            else:
                ident = self.counter
            self.counter += 1
            return ident
        elif obj in self:
            return self[obj]
        else:
            ident = self.get()
            self[obj] = ident
            return ident

    def identify(self, ident):
        rev = self.entries.reverse()
        return rev[ident] if ident in rev else None

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
    for ffs in files_or_strings:
        if not extension or (isinstance(ffs, str) and ffs.endswith(extension)):
            with open(ffs, 'r') as f:
                collected.append(f.read())
        else:
            collected.append(ffs)
    return collected

def map(current_graph, other_concept, other_namespace, id_map):
    if other_concept is None:
        return None
    if other_namespace is None:
        return other_concept
    if other_concept.startswith(other_namespace + '_'):
        if other_concept not in id_map:
            id_map[other_concept] = current_graph._get_next_id()
    else:
        id_map[other_concept] = other_concept

    mapped_concept = id_map[other_concept]
    if not current_graph.has(mapped_concept):
        current_graph.add(mapped_concept)
    return mapped_concept

class hashabledict(dict):
  def __key(self):
    return tuple((k,self[k]) for k in sorted(self))
  def __hash__(self):
    return hash(self.__key())
  def __eq__(self, other):
    self_id = self.__key()
    other_id = other.__key()
    return self_id == other_id

if __name__ == '__main__':
    for i in range(1000):
        print(identification_string(i, 'abcde'), end='  ')