from lark import Lark, Transformer
from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base_spec import KnowledgeBaseSpec
from data_structures.knowledge_parser import KnowledgeParser
import time, sys, json
from os.path import join

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr', 'pre', 'post', 'var', 'property'}


class KnowledgeBase:

    def __init__(self, *filenames, namespace='KB'):
        self._concept_graph = ConceptGraph(concepts=BASE_NODES, namespace=namespace)
        self._knowledge_parser = KnowledgeParser(self, BASE_NODES)
        self.load(join('data_structures','kg_files','base.kg'))
        self._knowledge_parser.initialize()
        for filename in filenames:
            self.load(filename)

    def load(self, *filenames_or_logicstrings):
        for input in filenames_or_logicstrings:
            if input.endswith('.kg'):
                input = open(input, 'r').read()
            tree = self._knowledge_parser.parse(input)
            additions = self._knowledge_parser.transform(tree)
            for addition in additions:
                self._concept_graph.concatenate(addition)

    def subtypes(self, concept):
        subtypes = set()
        for predicate in self._concept_graph.predicates(predicate_type='type', object=concept):
            subtype = predicate[0]
            subtypes.add(subtype)
            subtypes.update(self.subtypes(subtype))
        return subtypes

    def supertypes(self, concept):
        types = set()
        for predicate in self._concept_graph.predicates(subject=concept, predicate_type='type'):
            supertype = predicate[2]
            types.add(supertype)
            types.update(self.supertypes(supertype))
        return types

    def has(self, concept=None, predicate_type=None, object=None, predicate_id=None):
        return self._concept_graph.has(concept, predicate_type, object, predicate_id)

    def subject(self, predicate_id):
        return self._concept_graph.subject(predicate_id)

    def object(self, predicate_id):
        return self._concept_graph.object(predicate_id)

    def type(self, predicate_id):
        return self._concept_graph.type(predicate_id)

    def predicate(self, predicate_id):
        return self._concept_graph.predicate(predicate_id)

    def predicates(self, subject=None, predicate_type=None, object=None):
        return self._concept_graph.predicates(subject, predicate_type, object)

    def subjects(self, concept):
        return self._concept_graph.subjects(concept)

    def objects(self, concept):
        return self._concept_graph.objects(concept)

    def related(self, concept):
        return self._concept_graph.related(concept)

if __name__ == '__main__':
    print(KnowledgeBaseSpec.verify(KnowledgeBase))