from data_structures.concept_graph import ConceptGraph
from data_structures.working_memory_spec import WorkingMemorySpec
import data_structures.prolog as pl
from utilities import identification_string, CHARS
from itertools import chain

class WorkingMemory(ConceptGraph):

    def __init__(self, knowledge_base, *filenames_or_logicstrings):
        self.knowlege_base = knowledge_base
        super().__init__(namespace='WM')
        self.load(*filenames_or_logicstrings)

    def load(self, *filenames_or_logicstrings):
        for input in filenames_or_logicstrings:
            if input.endswith('.kg'):
                input = open(input, 'r').read()
            if len(input.strip()) > 0:
                tree = self.knowlege_base._knowledge_parser.parse(input)
                additions = self.knowlege_base._knowledge_parser.transform(tree)
                for addition in additions:
                    self.concatenate(addition)

    def pull_ontology(self):
        to_pull = set()
        visited = set()
        stack = list(self.concepts())
        for e in stack:
            for e, tr, t, id in self.knowlege_base.predicates(e, predicate_type='type'):
                to_pull.add((e, tr, t, id))
                if t not in visited:
                    stack.append(t)
                    visited.add(t)
        for item in to_pull:
            self.add(*item)

    def pull(self, order=1, concepts=None):
        pulling = set()
        covered = set()
        pull_set = set(self.concepts()) if concepts is None else set(self.concepts()) & concepts
        for i in range(order, 0, -1):
            to_pull = set()
            for puller in pull_set:
                related = set(self.knowlege_base.predicates(puller)) \
                          | set(self.knowlege_base.predicates(object=puller))
                for rel in related | {puller}:
                    if self.knowlege_base.has(predicate_id=rel):
                        related.add(self.predicate(rel))
                to_pull |= related
            covered |= pull_set
            pulling |= to_pull
            pull_set = set(chain(*to_pull)) - covered
        cg = ConceptGraph(predicates=pulling)
        self.concatenate(cg)
        self.pull_ontology()

    def inferences(self, *types_or_rules):
        next = 0
        wm_rules = pl.generate_inference_graphs(self)
        rules_to_run = {}
        for identifier in types_or_rules:
            if self.has(identifier):      # concept id
                rules_to_run[identifier] = wm_rules[identifier]
            else:                         # logic string or file
                input = identifier
                if input.endswith('.kg'):  # file
                    input = open(input, 'r').read()
                tree = self.knowlege_base._knowledge_parser.parse(input)
                additions = self.knowlege_base._knowledge_parser.transform(tree)
                cg = ConceptGraph(namespace=identification_string(next, CHARS))
                next += 1
                for addition in additions:
                    cg.concatenate(addition)
                file_rules = pl.generate_inference_graphs(cg)
                assert rules_to_run.keys().isdisjoint(file_rules.keys())
                rules_to_run.update(file_rules)

        solutions_dict = pl.infer(self, rules_to_run)
        return solutions_dict

    def implications(self, *types_or_rules):
        imps = []
        solutions_dict = self.inferences(*types_or_rules)
        for rule, solutions in solutions_dict.items():
            post_graph = rule.postcondition
            for solution in solutions:
                cg = ConceptGraph(namespace='IMP')
                for s, t, o, i in post_graph.predicates():
                    s = solution.get(s, s)
                    t = solution.get(t, t)
                    o = solution.get(o, o)
                    i = solution.get(i, i)
                    cg.add(s, t, o, i)
                imps.append(cg)
        return imps



if __name__ == '__main__':
    print(WorkingMemorySpec.verify(WorkingMemory))