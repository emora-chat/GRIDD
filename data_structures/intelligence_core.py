
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec

from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators, interleave
from itertools import chain, combinations
from GRIDD.data_structures.update_graph import UpdateGraph
from GRIDD.globals import *
from GRIDD.data_structures.assertions import assertions
from GRIDD.data_structures.id_map import IdMap

import GRIDD.data_structures.intelligence_core_operators as intcoreops


class IntelligenceCore:

    def __init__(self, knowledge_base=None, working_memory=None, inference_engine=None):
        self.compiler = ConceptCompiler(namespace='__c__')
        self.nlg_inference_engine = InferenceEngine()
        if inference_engine is None:
            inference_engine = InferenceEngine()
        self.inference_engine = inference_engine
        if isinstance(knowledge_base, ConceptGraph):
            self.knowledge_base = knowledge_base
        else:
            self.knowledge_base = ConceptGraph(namespace=KB)
            self.know(knowledge_base, emora_knowledge=True)
        if isinstance(working_memory, ConceptGraph):
            self.working_memory = working_memory
        else:
            self.working_memory = ConceptGraph(namespace='wm', supports={AND_LINK: False})
            self.consider(working_memory)
        self.operators = operators(intcoreops)
        self.subj_essential_types = {i for i in self.knowledge_base.subtypes_of(SUBJ_ESSENTIAL)
                                if not self.knowledge_base.has(predicate_id=i)}
        self.obj_essential_types = {i for i in self.knowledge_base.subtypes_of(OBJ_ESSENTIAL)
                                if not self.knowledge_base.has(predicate_id=i)}


    def know(self, knowledge, **options):
        cg = ConceptGraph(namespace='_tmp_')
        ConceptGraph.construct(cg, knowledge, compiler=self.compiler)
        self._loading_options(cg, options)
        self._assertions(cg)
        nlg_templates = cg.nlg_templates()
        for rule, (pre, _, vars) in nlg_templates.items():
            for concept in vars:
                cg.remove(concept)
            cg.remove(rule)
        for concept in set(cg.subtypes_of('response_token')):
            cg.remove(concept)
        self.nlg_inference_engine.add(nlg_templates)
        rules = cg.rules()
        for rule, (pre, post, vars) in rules.items():
            for concept in vars:
                cg.remove(concept)
            cg.remove(rule)
        self.inference_engine.add(rules)
        self.knowledge_base.concatenate(cg)

    def consider(self, concepts, namespace=None, associations=None, evidence=None, salience=1, **options):
        if isinstance(concepts, ConceptGraph):
            considered = ConceptGraph(concepts, namespace=concepts._ids)
        else:
            if namespace is None:
                namespace = '_tmp_'
            considered = ConceptGraph(concepts, namespace=namespace)
        updates = {}
        if associations is None and evidence is None:
            updates = {c: {SALIENCE: (salience*SENSORY_SALIENCE)} for c in considered.concepts()}
        elif evidence is None:
            s = min([self.working_memory.features.get(c, {}).get(SALIENCE, 0) for c in associations]) - ASSOCIATION_DECAY
            updates = {c: {SALIENCE: (salience*s)} for c in considered.concepts()}
        elif associations is None:
            s = min([self.working_memory.features.get(c, {}).get(SALIENCE, 0) for c in evidence]) - EVIDENCE_DECAY
            updates = {c: {SALIENCE: (salience*s)} for c in considered.concepts()}
        for c, d in updates.items():
            if c not in considered.features or SALIENCE not in considered.features[c]:
                considered.features[c][SALIENCE] = d[SALIENCE]
        self._loading_options(considered, options)
        mapping = self.working_memory.concatenate(considered)
        return mapping

    def infer(self, rules=None):
        if rules is None:
            solutions = self.inference_engine.infer(self.working_memory)
        else:
            solutions = self.inference_engine.infer(self.working_memory, dynamic_rules=rules)
        return solutions

    def apply_inferences(self, inferences=None):
        """
        :param inferences: {rule: (pre, post, [solution_dict, ...]),
                            ...}
        """
        # todo - think about type-based evidence
        #  (type predicates not found in solutions explicitly right now)
        # todo - evidence is currently the variable solution dictionary
        #  -> thus salience right now is only based on vars in precondition and
        #  if the precondition contains no vars, there is no evidence!
        if inferences is None:
            inferences = self.infer()
        result_dict = self.inference_engine.apply(inferences)
        for rule, results in result_dict.items():
            pre, post = inferences[rule][0], inferences[rule][1] # todo- assign neg conf links
            for evidence, implication in results:
                implication_strengths = {}
                uimplication_strengths = {}
                for n in implication.concepts():
                    if implication.has(predicate_id=n):
                        implication_strengths[n] = implication.features.get(n, {}).get(CONFIDENCE, 1)
                        if n in implication.features and CONFIDENCE in implication.features[n]:
                            del implication.features[n][CONFIDENCE]
                        uimplication_strengths[n] = implication.features.get(n, {}).get(UCONFIDENCE, 1)
                        if n in implication.features and UCONFIDENCE in implication.features[n]:
                            del implication.features[n][UCONFIDENCE]
                # check whether rule has already been applied with the given evidence
                old_solution = False
                current_evidence = set([x for x in evidence.values() if self.working_memory.has(predicate_id=x)])  # AND links only set up from predicate instances
                for node, features in self.working_memory.features.items():
                    if 'origin_rule' in features and features['origin_rule'] == rule:
                        prev_evidence = {s for s, _, l in self.working_memory.metagraph.in_edges(node) if AND_LINK in l}
                        if prev_evidence == current_evidence:
                            old_solution = True
                            break
                if not old_solution:
                    implied_nodes = self.consider(implication, evidence=evidence.values())
                    and_node = self.working_memory.id_map().get()
                    self.working_memory.features[and_node]['origin_rule'] = rule # store the implication rule that resulted in this and_node as metadata
                    for pre_node, evidence_node in evidence.items():
                        if self.working_memory.has(predicate_id=evidence_node):
                            strength = inferences[rule][0].features.get(pre_node, {}).get(CONFIDENCE, 1)
                            self.working_memory.metagraph.add(evidence_node, and_node, (AND_LINK, strength))
                            strength = inferences[rule][0].features.get(pre_node, {}).get(UCONFIDENCE, 1)
                            self.working_memory.metagraph.add(evidence_node, and_node, (UAND_LINK, strength))
                    for imp_node, strength in implication_strengths.items():
                        self.working_memory.metagraph.add(and_node, implied_nodes[imp_node], (OR_LINK, strength))
                    for imp_node, strength in uimplication_strengths.items():
                        self.working_memory.metagraph.add(and_node, implied_nodes[imp_node], (UOR_LINK, strength))

    def update_confidence(self, speaker):
        """
        label_d is a dictionary of label_type to label in order to update confidence w.r.t different populations
        e.g. emora, user, etc.
        label_d must contain a mapping for:
            and
            or
            conf
        """
        mg = self.working_memory.metagraph
        and_links, or_links = [], []
        nodes = {}
        if speaker == 'emora':
            andl = AND_LINK
            orl = OR_LINK
            conf = CONFIDENCE
            base_conf = BASE_CONFIDENCE
            counter = 0
            for s, t, o, i in self.working_memory.predicates():
                convincability = self.working_memory.features.get(i, {}).get(CONVINCABLE, 1.0)
                cnode = f'{counter}__cnode'
                counter += 1
                or_links.append((cnode, i, ('convince_link', convincability)))
                nodes[cnode] = self.working_memory.features.get(i, {}).get(UCONFIDENCE, 0.0)
        elif speaker == 'user':
            andl = UAND_LINK
            orl = UOR_LINK
            conf = UCONFIDENCE
            base_conf = BASE_UCONFIDENCE
        else:
            raise ValueError('speaker parameter must be either `emora` or `user`, not `%s`'%speaker)
        nodes.update({c: mg.features.get(c, {}).get(base_conf, 0) for c in mg.nodes()})
        and_links.extend([edge for edge in mg.edges() if isinstance(edge[2], tuple) and andl == edge[2][0]])
        or_links.extend([edge for edge in mg.edges() if isinstance(edge[2], tuple) and orl == edge[2][0]])
        counter = 0
        for _,_,_,i in self.working_memory.predicates():
            bc = self.working_memory.features.get(i, {}).get(base_conf, None)
            if bc is not None: # nodes with base confidence include themselves in their OR conf calculation
                bnode = f'{counter}__bnode'
                counter += 1
                or_links.append((bnode, i, (orl, 1.0)))
                nodes[bnode] = bc
        types = self.working_memory.types()
        unasserted = {}
        ass_links = set()
        ass_link_edges = list(mg.edges(label=ASS_LINK))
        for s, t, l in ass_link_edges:
            if self.working_memory.has(predicate_id=t):
                ass_links.add((s, t))
                if NONASSERT in types[t]:
                    unasserted.setdefault(s, set()).add(self.working_memory.predicate(t)[2])
            if NONASSERT in types[s]:
                unasserted.setdefault(s, set()).add(self.working_memory.predicate(s)[2])
        for s, t, l in ass_link_edges:
            if t in unasserted.get(s, set()):
                ass_links.discard((s, t))
        for s, t in ass_links:
            if t not in unasserted:
                or_links.append((s, t, (orl, 1.0)))
        def and_fn(node, sources):
            product = 1
            for value, (label, weight) in sources:
                product *= weight * value
            if product >= 0:
                return min(product, 1.0)
            else:
                return max(product, -1.0)
        def or_fn(node, sources):
            convince_links = [s for s in sources if s[1][0] == 'convince_link']
            non_convince_links = [s for s in sources if s[1][0] != 'convince_link']
            conf_calc = 0
            if non_convince_links:
                weight = non_convince_links[0][1][1]
                conf_calc = non_convince_links[0][0] * weight
                product = non_convince_links[0][0] * weight
                for value, (label, weight) in non_convince_links[1:]:
                    conf_calc += value * weight
                    product *= value * weight
                    conf_calc = conf_calc - product
                    product = conf_calc
            weighted_convince = 0
            normalization = 1
            if convince_links:
                weighted_convince = sum([val * convince for val, (_, convince) in convince_links])
                sum_convince = sum([convince for _, (_, convince) in convince_links])
                sum_non_convince = sum([1 - convince for _, (_, convince) in convince_links])
                conf_calc = sum_non_convince * conf_calc
                normalization = sum_convince + sum_non_convince
            final_value = weighted_convince + conf_calc / normalization
            return final_value
        def set_fn(n, v):
            if not (n.endswith('__cnode') or n.endswith('__bnode')): mg.features.setdefault(n, {}).__setitem__(conf, v)
        update_graph = UpdateGraph(
            edges=[*and_links, *or_links],
            nodes=nodes,
            updaters={
                **{n: and_fn for _,n,_ in and_links},
                **{n: or_fn for _,n,_ in or_links}},
            default=0,
            set_fn=set_fn
        )
        update_graph.update(iteration=10, push=True)

    def merge(self, concept_sets):
        sets = {}
        for cs in concept_sets:
            s = set(cs)
            for c in cs:
                if c in sets:
                    s.update(sets[c])
            for c in s:
                sets[c] = s
        sets = uniquify(sets.values())
        for s in sets:
            if s:
                s = list(s)
                a = s[0]
                for i in range(1, len(s)):
                    b = s[i]
                    a = self.working_memory.merge(a, b)

    def convert_metagraph_span_links(self, gather_link, promote_links):
        """
        Convert `gather_link` predicate instances, which point to spans, to new predicate instances
        of types `promote_links` (list of predicate types), which will now point to the predicate components of the span
        """
        node_to_spans = {}
        for s, t, _ in self.working_memory.metagraph.edges(label=gather_link):
            node_to_spans.setdefault(s, []).append(t)
        for node, span in node_to_spans.items():
            constraints = self.gather(node, span)
            for type in promote_links:
                self.working_memory.metagraph.add_links(node, constraints, type)
            for t in span:
                self.working_memory.metagraph.remove(node, t, gather_link)

    def gather(self, reference_node, constraints_as_spans):
        PRIMITIVES = {'focus', 'center', REQ_TRUTH, REQ_ARG, 'var'}
        constraints = set()
        focal_nodes = set()
        for constraint_span in constraints_as_spans:
            if self.working_memory.has(constraint_span):
                foci = self.working_memory.objects(constraint_span, 'ref')
                focus = next(iter(foci))  # todo - could be more than one focal node in disambiguation situation?
                focal_nodes.add(focus)
        # expand constraint spans into constraint predicates
        for focal_node in focal_nodes:
            components = self.working_memory.metagraph.targets(focal_node, COMPS)
            # constraint found if constraint predicate is connected to reference node
            for component in components:
                if (not self.working_memory.has(predicate_id=component) or
                    self.working_memory.type(component) not in PRIMITIVES) and \
                        self.working_memory.graph_component_siblings(component, reference_node):
                    constraints.add(component)
        return list(constraints)

    def resolve(self, references=None):
        if references is None:
            references = self.working_memory.references()
        compatible_pairs = {}
        if len(references) > 0:
            inferences = self.inference_engine.infer(self.working_memory, references, cached=False)
            for reference_node, (pre, matches) in inferences.items():
                compatible_pairs[reference_node] = {}
                for match in matches:
                    if reference_node != match[reference_node]:
                        compatible_pairs[reference_node][match[reference_node]] = []
                        for node in match:
                            if node != reference_node:
                                compatible_pairs[reference_node][match[reference_node]].append((match[node],node))
        return compatible_pairs

    def learn_generics(self, generics=None):
        if generics is None:
            generics = self.working_memory.generics()
        # convert to implication rules
        for group, (def_concepts, prop_concepts) in generics.items():
            imp_node = self.working_memory.id_map().get()
            self.working_memory.add(imp_node, TYPE, 'implication')
            self.working_memory.metagraph.add_links(imp_node, def_concepts, 'pre')
            self.working_memory.metagraph.add_links(imp_node, def_concepts, 'var')
            self.working_memory.metagraph.add_links(imp_node, prop_concepts, 'post')
            self.working_memory.metagraph.add_links(imp_node, prop_concepts, 'var')
            for t in def_concepts:
                self.working_memory.metagraph.remove(group, t, GROUP_DEF)
            for t in prop_concepts:
                self.working_memory.metagraph.remove(group, t, GROUP_PROP)
            self.working_memory.remove(group, TYPE, GROUP)


    def logical_merge(self):
        # Todo: logical merge
        return

    def pull_types(self):
        return set(self.knowledge_base.type_predicates(self.working_memory.concepts()))


    def pull_knowledge(self, limit, num_pullers, association_limit=None, subtype_limit=None, degree=1):
        kb = self.knowledge_base
        wm = self.working_memory
        # only consider concepts that are arguments of non-type/expr/ref/def predicates
        pullers = [c for c in wm.concepts()
                   if not (wm.subjects(c,'type') or wm.objects(c,'expr') or wm.objects(c,'ref') or wm.objects(c,'def'))
                   and (wm.subjects(c) or wm.objects(c))
                   and wm.features.get(c, {}).get(SALIENCE, 0) > 0.0]
        pullers = sorted(pullers,
                         key=lambda c: self.working_memory.features.get(c, {}).get(SALIENCE, 0),
                         reverse=True)
        pullers = pullers[:num_pullers]
        neighbors = {}
        backptrs = {}
        for p in pullers:
            neighborhood = set(kb.related(p, exclusions={'type', 'expr', 'ref', 'def'}, limit=association_limit))
            arguments = set()
            for n in neighborhood:
                if kb.has(predicate_id=n):
                    s, _, o, _ = kb.predicate(n)
                    other_arg = o if s == p else s
                    if other_arg is not None:
                        arguments.add(other_arg)
                        backptrs.setdefault(other_arg, set()).add(n)
            neighborhood.update(arguments)
            neighbors[p] = neighborhood
        wmp = set(self.working_memory.predicates())
        memo = {}
        new_concepts_by_source = {}
        for length in range(2, 0, -1): # todo - inefficient; identify combinations -> empty intersection and ignore in further processing
            combos = combinations(pullers, length)
            for combo in combos:
                related = set(neighbors[combo[0]])
                concepts = [combo[0]]
                for c in combo[1:]:
                    concepts.append(c)
                    tconcepts = tuple(concepts)
                    if tconcepts in memo:
                        related = memo[tconcepts]
                    else:
                        related.intersection_update(neighbors[c])
                        memo[tconcepts] = set(related)
                    if len(related) == 0:
                        break
                for r in related:
                    to_add = set(kb.structure(r,
                                              subj_emodifiers=self.subj_essential_types,
                                              obj_emodifiers=self.obj_essential_types))
                    for inst in backptrs.get(r, r):
                        to_add.update(kb.structure(inst,
                                                   subj_emodifiers=self.subj_essential_types,
                                                   obj_emodifiers=self.obj_essential_types))
                    to_add.difference_update(wmp)
                    if len(to_add) <= limit:
                        limit -= len(to_add)
                        for sig in to_add:
                            new_concepts_by_source.setdefault(sig, set()).update(combo)
                    else:
                        return new_concepts_by_source
        return new_concepts_by_source

    def pull_expressions(self):
        to_add = set()
        for c in self.working_memory.concepts():
            to_add.update(self.knowledge_base.predicates(c, 'expr'))
            to_add.update(self.knowledge_base.predicates(predicate_type='expr', object=c))
        return to_add

    def update_salience(self, iterations=10):
        wm = self.working_memory
        edges = []
        for e in wm.to_graph().edges():
            if e[0] not in SAL_FREE and e[1] not in SAL_FREE:
                if not wm.has(predicate_id=e[0]) or wm.type(e[0]) not in SAL_FREE:
                    edges.append(e)
        redges = [(t, s, l) for s, t, l in edges]
        and_links = [edge for edge in wm.metagraph.edges() if isinstance(edge[2], tuple) and AND_LINK == edge[2][0]]
        for evidence, and_node, _ in and_links:
            or_links = [edge for edge in wm.metagraph.out_edges(and_node) if isinstance(edge[2], tuple) and OR_LINK == edge[2][0]]
            for _, implication, _ in or_links:
                redges.append((evidence, implication, None))
        def moderated_salience(salience, connectivity):
            return salience / connectivity
        def update_instance_salience(val, args):
            in_ms = []
            out_ms = [val[0]]
            for (sal, con), lnk in args:
                if lnk == SALIENCE_IN_LINK:
                    in_ms.append(moderated_salience(sal, con) - ASSOCIATION_DECAY)
                else:
                    out_ms.append(sal)
            avg = sum(in_ms) / len(in_ms) if len(in_ms) > 0 else 0
            return (max(out_ms + [avg]), val[1])
        updater = UpdateGraph(
            [*[(s, t, SALIENCE_OUT_LINK) for s, t, _ in edges],
             *[(s, t, SALIENCE_IN_LINK) for s, t, _ in redges]],
            nodes={
                c: (wm.features.get(c, {}).get(SALIENCE, 0),
                    wm.features.get(c, {}).get(CONNECTIVITY, 1))
                for c in wm.concepts()},
            updaters={c: update_instance_salience for c in wm.concepts()},
            default=(0, 1),
            set_fn=(lambda n, v: wm.features.setdefault(n, {}).__setitem__(SALIENCE, v[0]))
        )
        updater.update(iterations, push=True)

    def decay_salience(self):
        wm = self.working_memory
        for c in wm.concepts():
            if not wm.features.get(c, {}).get(COLDSTART, False) and (not wm.has(predicate_id=c) or wm.type(c) not in SAL_FREE):
                sal = wm.features.setdefault(c, {}).setdefault(SALIENCE, 0)
                wm.features[c][SALIENCE] = max(0, sal - TIME_DECAY)

    def prune_attended(self, keep):
        options = set()
        for s, t, o, i in self.working_memory.predicates():
            if t == 'type':
                if not self.working_memory.features.get(s, {}).get(IS_TYPE, False):
                    preds = {pred for pred in self.working_memory.related(s) if self.working_memory.has(predicate_id=pred) and pred[1] != 'type'}
                    if not preds:
                        options.add(i)
            elif t not in chain(self.subj_essential_types, self.obj_essential_types,PRIM):
                options.add(i)

        sconcepts = sorted(options,
                           key=lambda x: self.working_memory.features.get(x, {}).get(SALIENCE, 0),
                           reverse=True)
        for c in sconcepts[keep:]:
            self.working_memory.remove(c) # todo: uh oh - short term memory loss

    def prune_predicates_of_type(self, types):
        for s, t, o, i in list(self.working_memory.predicates()):
            if t in types:
                self.working_memory.remove(s, t, o, i)

    def operate(self, cg=None):
        if cg is None:
            cg = self.working_memory
        for opname, opfunc in self.operators.items(): # todo - some operators should be run only once and then deleted
            for _, _, _, i in list(cg.predicates(predicate_type=opname)):
                if cg.has(predicate_id=i): # within-loop-mutation check
                    opfunc(cg, i)

    def display(self, verbosity=1):
        s = '#'*30 + ' Working Memory ' + '#'*30
        s += self.working_memory.pretty_print()
        s += '#'*(60+len(' working memory '))
        return s

    def _loading_options(self, cg, options):
        if 'commonsense' in options:
            pass
        if 'attention_shift' in options:
            pass
        if 'emora_knowledge' in options:
            for s, t, o, i in cg.predicates():
                if not cg.has('emora', REQ_TRUTH, i):
                    cg.features[i][CONVINCABLE] = 0.0
                else:
                    cg.features[i][CONVINCABLE] = 1.0
        if 'assert_conf' in options:
            self._assertions(cg)

    def _assertions(self, cg):
        assertions(cg)


if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



