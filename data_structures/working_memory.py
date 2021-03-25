from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_parser import KnowledgeParser, logic_parser
from GRIDD.data_structures.working_memory_spec import WorkingMemorySpec
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.utilities import identification_string, CHARS
from itertools import chain
from collections import deque
# import networkx as nx
# import matplotlib.pyplot as plt


class WorkingMemory(ConceptGraph):

    def __init__(self, knowledge_base, *filenames_or_logicstrings):
        self.knowledge_base = knowledge_base
        super().__init__(namespace='WM')
        if len(filenames_or_logicstrings) > 0:
            self.concatenate(KnowledgeParser.from_data(*filenames_or_logicstrings,
                                                       parser=logic_parser))

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
            self.features.update_from_ontology(item)

    def pull_expressions(self, concepts=None):
        concepts = list(self.concepts()) if concepts is None else list(self.concepts() & set(concepts))
        for c in concepts:
            for item in self.knowledge_base.predicates(predicate_type='expr', object=c):
                self.add(*item)

    def pull(self, order=1, concepts=None, exclude_on_pull=None):
        if isinstance(concepts, list):
            concepts = set(concepts)
        pulling = set()
        covered = set()
        pull_set = set(self.concepts()) if concepts is None else set(self.concepts()) & concepts
        for i in range(order, 0, -1):
            to_pull = set()
            for puller in pull_set:
                related = set(self.knowledge_base.predicates(puller)) | set(self.knowledge_base.predicates(object=puller))

                # remove predicates of types in EXCLUDE_ON_PULL
                if exclude_on_pull is not None and len(related) > 0:
                    for pred_type in exclude_on_pull:
                        related -= set(self.knowledge_base.predicates(puller, pred_type))
                        related -= set(self.knowledge_base.predicates(predicate_type=pred_type, object=puller))

                # add all 1-degree neighbors of predicate instances from related
                predicate_neighbors = set()
                for predicate in related:
                    instance = predicate[3]
                    pred_relations = set(self.knowledge_base.predicates(instance)) | set(self.knowledge_base.predicates(object=instance))
                    if exclude_on_pull is not None and len(pred_relations) > 0:
                        for pred_type in exclude_on_pull:
                            pred_relations -= set(self.knowledge_base.predicates(instance, pred_type))
                            pred_relations -= set(self.knowledge_base.predicates(predicate_type=pred_type, object=instance))
                    predicate_neighbors.update(pred_relations)
                related.update(predicate_neighbors)

                # ensure all predicate instances are fully represented
                for rel in {e for tuple in related for i, e in enumerate(tuple) if i != 3} | {puller}:
                    if self.knowledge_base.has(predicate_id=rel) and not self.has(predicate_id=rel):
                        related.add(self.knowledge_base.predicate(rel))
                to_pull |= related
            covered |= pull_set
            pulling |= to_pull
            pull_set = set(chain(*to_pull)) - covered - {None}
        cg = ConceptGraph(predicates=pulling)
        id_map = self.concatenate(cg)
        self.features.update_from_kb(id_map.values())
        self.pull_ontology()

    # todo - efficiency check
    #  if multiple paths to same ancestor,
    #  it will pull ancestor's ancestor-chain multiple times
    # todo - rename to "types"
    def supertypes(self, concept=None):
        if concept is not None:
            types = set()
            for predicate in self.predicates(subject=concept, predicate_type='type'):
                supertype = predicate[2]
                types.add(supertype)
                types.update(self.supertypes(supertype))
            return types
        else:
            supertypes = {c: set() for c in self.concepts()}
            # Find root type nodes
            roots = [c for c in self.concepts() \
                     if (not any(['type'==x for _, x, _, _ in self.predicates(c)])) \
                     and (not self.has(predicate_id=c))]
            # Propagate types down to leaves
            for root in roots:
                supertypes[root] = set()
                q = deque([root])
                while q:
                    o = q.popleft()
                    for s, t, o, i in self.predicates(predicate_type='type', object=o):
                        q.append(s)
                        supertypes.get(s, set()).update(supertypes[o])
                        supertypes[s].add(o)
            for s, t, o, i in self.predicates():
                supertypes.get(i, set()).add(t)
                supertypes[i].update(supertypes[t])
            return supertypes

    def equivalent(self, ref, target, types=None):
        """
        Checking if two nodes have a merge-compatible property neighborhood.

        The `ref` can have fewer properties than `target` or less-specific types,
        but not the other way around.

        Returns all merged concept pairs for a compatible `(ref, target)`, or the
        empty list if the `ref` and `target` are not compatible.

        Optionally provide `types` dict from calling `working_memory.types()` for efficiency
        (otherwise `types` will be dynamically computed).
        """
        if types is None:
            types = self.supertypes()
        if self.has(ref, 'is_type') or self.has(target, 'is_type'):
            return []
        pairs = []
        confirmed = set()
        visited = set()  # Expanded concepts (ref side)
        tocheck = deque([(ref, target, None)])  # Ref, target, parent to continue comps
        while tocheck:
            a, b, parent = tocheck.popleft()
            if a not in visited:
                visited.add(a)
                compatible = types[a] <= types[b] and not self.is_literal(a) and not self.is_literal(b)
                if a == b:
                    confirmed.add(parent)
                elif (not compatible) and (not any([ref==x for _,_,x in tocheck])):
                    return []
                elif (not compatible):
                    continue
                else:
                    pairs.append((a, b, parent))
                    a_preds = [x for x in self.predicates(a) if x[1] != 'type']
                    b_preds = [x for x in self.predicates(b) if x[1] != 'type']
                    a_rpreds = [x for x in self.predicates(object=a) if x[1] != 'type']
                    b_rpreds = [x for x in self.predicates(object=b) if x[1] != 'type']
                    if len(a_preds) == 0 and len(a_rpreds) == 0:
                        confirmed.add(a)
                        continue
                    for rs, rt, ro, ri in a_preds:
                        for ts, tt, to, ti in b_preds:
                            if ro is None and to is None:
                                tocheck.extend([(rt, tt, a), (ri, ti, a)])
                            elif ro is not None and to is not None:
                                tocheck.extend([(rt, tt, a), (ro, to, a), (ri, ti, a)])
                    for rs, rt, ro, ri in a_rpreds:
                        for ts, tt, to, ti in b_rpreds:
                            tocheck.extend([(rs, ts, a), (rt, tt, a), (ri, ti, a)])
        true_pairs = []
        for x, y, p in reversed(pairs):     # Assumes pairs found in BFS order
            if x in confirmed:
                confirmed.add(p)
                true_pairs.append((x, y))
        return true_pairs

    def is_literal(self, concept):
        """
        Check if the literal is an expression/value (True) or regular concept (False).
        """
        if isinstance(concept, int):
            return True                                         # Value node
        else:
            return concept[0] == '"' and concept[-1] == '"'     # Expression node


    # def display_graph(self, exclusions=None):
    #     G = nx.DiGraph()
    #     edge_labels = {}
    #
    #     for s, t, o, i in self.predicates():
    #         if exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions):
    #             if t in {'type', 'time'}:
    #                 edge_labels[(s, o)] = t
    #             elif t == 'ref':
    #                 edge_labels[(str(s), o)] = t
    #             elif t in {'instantiative', 'referential'}:
    #                 edge_labels[(s, t)] = ''
    #             else:
    #                 edge_labels[(i, s)] = 's'
    #                 if o is not None:
    #                     edge_labels[(i, o)] = 'o'
    #                 edge_labels[(i, t)] = 't'
    #
    #     G.add_edges_from(edge_labels.keys())
    #     pos = nx.spring_layout(G, iterations=500,
    #                            k=10)
    #     plt.figure()
    #     nx.draw(G, pos, edge_color='black', font_size=7,
    #             node_size=300, node_color='pink', alpha=0.8,
    #             labels={node:node for node in G.nodes()})
    #     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
    #                                  font_size=7, font_color='red')
    #     plt.show()


if __name__ == '__main__':
    print(WorkingMemorySpec.verify(WorkingMemory))

    # display_graph() example
    #
    # cg1 = ConceptGraph(concepts=['princess', 'hiss', 'fluffy', 'bark', 'friend'], namespace='1')
    # a = cg1.add('princess', 'hiss')
    # cg1.add(a, 'volume', 'loud')
    # cg1.add('fluffy', 'bark')
    # cg1.add('princess', 'friend', 'fluffy')
    # cg1.add('fluffy', 'friend', 'princess')
    #
    # from GRIDD.data_structures.knowledge_base import KnowledgeBase
    # wm = WorkingMemory(KnowledgeBase())
    # wm.concatenate(cg1)
    # wm.display_graph()
