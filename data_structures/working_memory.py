from data_structures.concept_graph import ConceptGraph
from data_structures.working_memory_spec import WorkingMemorySpec
import data_structures.infer as pl
from utilities import identification_string, CHARS
from itertools import chain
import networkx as nx
import matplotlib.pyplot as plt

class WorkingMemory(ConceptGraph):

    EXCLUDE_ON_PULL = {'type'}

    def __init__(self, knowledge_base, *filenames_or_logicstrings):
        self.knowledge_base = knowledge_base
        self.span_dict = {}
        super().__init__(namespace='WM')
        self.load(*filenames_or_logicstrings)

    def load(self, *filenames_or_logicstrings):
        for input in filenames_or_logicstrings:
            if input.endswith('.kg'):
                input = open(input, 'r').read()
            if len(input.strip()) > 0:
                tree = self.knowledge_base._knowledge_parser.parse(input)
                additions = self.knowledge_base._knowledge_parser.transform(tree)
                for addition in additions:
                    self.concatenate(addition)

    def pull_ontology(self, concepts=None):
        to_pull = set()
        visited = set()
        stack = list(self.concepts()) if concepts is None else list(self.concepts() & set(concepts))
        for e in stack:
            for e, tr, t, id in self.knowledge_base.predicates(e, predicate_type='type'):
                if e != 'type' and t != 'type':
                    to_pull.add((e, tr, t, id))
                    if t not in visited:
                        stack.append(t)
                        visited.add(t)
        for item in to_pull:
            self.add(*item)

    #todo - may be pulling too much?
    def pull(self, order=1, concepts=None):
        if isinstance(concepts, list):
            concepts = set(concepts)
        pulling = set()
        covered = set()
        pull_set = set(self.concepts()) if concepts is None else set(self.concepts()) & concepts
        for i in range(order, 0, -1):
            to_pull = set()
            for puller in pull_set:
                related = set(self.knowledge_base.predicates(puller)) \
                          | set(self.knowledge_base.predicates(object=puller))
                for pred_type in WorkingMemory.EXCLUDE_ON_PULL:
                    related -= set(self.knowledge_base.predicates(puller, pred_type))
                    related -= set(self.knowledge_base.predicates(predicate_type=pred_type, object=puller))
                for rel in related | {puller}:
                    if self.knowledge_base.has(predicate_id=rel):
                        related.add(self.knowledge_base.predicate(rel))
                to_pull |= related
            covered |= pull_set
            pulling |= to_pull
            pull_set = set(chain(*to_pull)) - covered - {None}
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
                tree = self.knowledge_base._knowledge_parser.parse(input)
                additions = self.knowledge_base._knowledge_parser.transform(tree)
                cg = ConceptGraph(namespace=identification_string(next, CHARS))
                next += 1
                for addition in additions:
                    cg.concatenate(addition)
                file_rules = pl.generate_inference_graphs(cg)
                assert rules_to_run.keys().isdisjoint(file_rules.keys())
                rules_to_run.update(file_rules)

        solutions_dict = pl.infer(self, rules_to_run)
        return solutions_dict

    # todo - move core logic to infer.py
    def implications(self, *types_or_rules):
        imps = []
        solutions_dict = self.inferences(*types_or_rules)
        for rule, solutions in solutions_dict.items():
            post_graph = rule.postcondition
            for solution in solutions:
                cg = ConceptGraph(namespace=post_graph._namespace)
                for s, t, o, i in post_graph.predicates():
                    s = solution.get(s, s)
                    t = solution.get(t, t)
                    o = solution.get(o, o)
                    i = solution.get(i, i)
                    cg.add(s, t, o, i)
                imps.append(cg)
        return imps

    # todo - efficiency check
    #  if multiple paths to same ancestor,
    #  it will pull ancestor's ancestor-chain multiple times
    def supertypes(self, concept):
        types = set()
        for predicate in self.predicates(subject=concept, predicate_type='type'):
            supertype = predicate[2]
            types.add(supertype)
            types.update(self.supertypes(supertype))
        return types

    def rules(self):
        return pl.generate_inference_graphs(self)

    def update_spans(self, span_dict):
        self.span_dict.update(span_dict)

    def display_graph(self, exclusions=None):
        G = nx.Graph() #todo - directed graph
        edge_labels = {}

        for s, t, o, i in self.predicates():
            if exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions):
                if t in {'type', 'time'}:
                    edge_labels[(s, o)] = t
                elif t == 'exprof':
                    edge_labels[(self.span_dict[s], o)] = t
                elif t in {'instantiative', 'referential'}:
                    edge_labels[(s, t)] = ''
                else:
                    edge_labels[(i, s)] = 's'
                    if o is not None:
                        edge_labels[(i, o)] = 'o'
                    edge_labels[(i, t)] = 't'

        G.add_edges_from(edge_labels.keys())
        pos = nx.fruchterman_reingold_layout(G)
        # pos = nx.planar_layout(G)
        plt.figure()
        nx.draw(G, pos, edge_color='black', font_size=7,
                node_size=300, node_color='pink', alpha=0.8,
                labels={node:node for node in G.nodes()})
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                     font_size=7, font_color='red')
        plt.show()



if __name__ == '__main__':
    print(WorkingMemorySpec.verify(WorkingMemory))

    cg1 = ConceptGraph(concepts=['princess', 'hiss', 'fluffy', 'bark', 'friend'], namespace='1')
    a = cg1.add('princess', 'hiss')
    cg1.add(a, 'volume', 'loud')
    cg1.add('fluffy', 'bark')
    cg1.add('princess', 'friend', 'fluffy')
    cg1.add('fluffy', 'friend', 'princess')

    from data_structures.knowledge_base import KnowledgeBase
    wm = WorkingMemory(KnowledgeBase())
    wm.concatenate(cg1)
    wm.display_graph()