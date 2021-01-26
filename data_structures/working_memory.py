from data_structures.concept_graph import ConceptGraph
from data_structures.working_memory_spec import WorkingMemorySpec
import data_structures.infer as pl
from utilities import identification_string, CHARS
from itertools import chain
from collections import deque
import utilities as util

class WorkingMemory(ConceptGraph):

    EXCLUDE_ON_PULL = {'type'}

    def __init__(self, knowledge_base, *filenames_or_logicstrings):
        self.knowledge_base = knowledge_base
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
                    related -= set(self.knowledge_base.predicates(puller, pred_type)) \
                            - set(self.knowledge_base.predicates(predicate_type=pred_type, object=puller))
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
    def implications(self, *types_or_rules, solutions=None):
        imps = []
        if solutions is not None:
            solutions_dict = {**solutions, **self.inferences(*types_or_rules)}
        else:
            solutions_dict = self.inferences(*types_or_rules)
        for rule, solutions in solutions_dict.items():
            post_graph = rule.postcondition
            for solution in solutions:
                id_map = {}
                cg = ConceptGraph(namespace='IMP')
                for s, t, o, i in post_graph.predicates():
                    if t != 'var':
                        s = util.map(cg, solution.get(s, s), post_graph._namespace, id_map)
                        t = util.map(cg, solution.get(t, t), post_graph._namespace, id_map)
                        o = util.map(cg, solution.get(o, o), post_graph._namespace, id_map)
                        i = util.map(cg, solution.get(i, i), post_graph._namespace, id_map)
                        cg.add(s, t, o, i)
                imps.append(cg)
        return imps

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

    def rules(self):
        return pl.generate_inference_graphs(self)

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



if __name__ == '__main__':
    print(WorkingMemorySpec.verify(WorkingMemory))