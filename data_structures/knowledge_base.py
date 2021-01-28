from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base_spec import KnowledgeBaseSpec
from data_structures.knowledge_parser import KnowledgeParser
from utilities import collect
from os.path import join

BASE_NODES = {'object', 'type', 'is_type', 'expression', 'expr', 'pre', 'post', 'var', 'property', 'focus'}


class KnowledgeBase:

    def __init__(self, *filenames_or_logicstrings, namespace='KB', ensure_kb_compatible=True):
        self._concept_graph = ConceptGraph(concepts=BASE_NODES, namespace=namespace)
        self._knowledge_parser = KnowledgeParser(self, BASE_NODES, ensure_kb_compatible=ensure_kb_compatible)
        self.load(join('GRIDD', 'resources', 'kg_files', 'base.kg'))
        self.load(*filenames_or_logicstrings)

    def load(self, *filenames_or_logicstrings):
        strings_or_kbs = collect(*filenames_or_logicstrings, extension='.kg')
        for input in strings_or_kbs:
            if isinstance(input, str):
                if len(input.strip()) > 0:
                    tree = self._knowledge_parser.parse(input)
                    additions = self._knowledge_parser.transform(tree)
                    for addition in additions:
                        self._concept_graph.concatenate(addition)
            elif isinstance(input, KnowledgeBase):
                self._concept_graph.concatenate(input)

    def subtypes(self, concept):
        subtypes = set()
        for predicate in self._concept_graph.predicates(predicate_type='type', object=concept):
            subtype = predicate[0]
            subtypes.add(subtype)
            subtypes.update(self.subtypes(subtype))
        return subtypes

    # todo - efficiency check
    #  if multiple paths to same ancestor,
    #  it will pull ancestor's ancestor-chain multiple times
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