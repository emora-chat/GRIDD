from lark import Lark, Transformer
from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base_spec import KnowledgeBaseSpec
from data_structures.knowledge_parser import KnowledgeParser
import time, sys, json
from os.path import join

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr', 'pre', 'post', 'var', 'property'}


class KnowledgeBase:

    def __init__(self, *filenames):
        self._concept_graph = ConceptGraph(concepts=BASE_NODES)
        self._knowledge_parser = KnowledgeParser(self, BASE_NODES)
        self.load(open(join('data_structures','kg_files','base.kg'), 'r').read())
        self._knowledge_parser.initialize()
        for filename in filenames:
            self.load(open(filename, 'r').read())

    def load(self, *filenames_or_logicstrings):
        for input in filenames_or_logicstrings:
            if input.endswith('.kg'):
                input = open(input, 'r').read()
            tree = self._knowledge_parser.parse(input)
            additions = self._knowledge_parser.transform(tree)
            for addition in additions:
                self._concept_graph.concatenate(addition)



if __name__ == '__main__':
    print(KnowledgeBaseSpec.verify(KnowledgeBase))