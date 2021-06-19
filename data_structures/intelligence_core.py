
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec
from GRIDD.intcore_server_globals import *

from GRIDD.data_structures.concept_graph import ConceptGraph
if INFERENCE:
    from GRIDD.data_structures.graph_matching.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators, interleave, _process_requests
from itertools import chain, combinations
from GRIDD.data_structures.update_graph import UpdateGraph
from GRIDD.globals import *
from GRIDD.data_structures.assertions import assertions
from GRIDD.data_structures.confidence import *
from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.span import Span

from GRIDD.modules.responsegen_by_templates import Template

import GRIDD.data_structures.intelligence_core_universal_operators as intcoreops
import GRIDD.data_structures.intelligence_core_wm_operators as wmintcoreops

from GRIDD.utilities.profiler import profiler as p

from time import time
import os, json

class IntelligenceCore:

    def __init__(self, knowledge_base=None, inference_rules=None, nlg_templates=None, fallbacks=None, working_memory=None, inference_engine=None, device='cpu'):
        """
        knowledge_base is a dict of identifiers (usually filenames) to logicstrings
        """
        self.compiler = ConceptCompiler(namespace='__c__', warn=True)
        self.universal_operators = operators(intcoreops)
        self.wm_operators = operators(wmintcoreops)

        if isinstance(knowledge_base, ConceptGraph):
            self.knowledge_base = knowledge_base
        else:
            self.knowledge_base = ConceptGraph(namespace=KB)
            if USECACHE:
                cached_knowledge, new_knowledge = self.stratify_cached_files(KBCACHE, knowledge_base)
                self.load_kb(cached_knowledge, new_knowledge, knowledge_base, KBCACHE)
            else:
                new_knowledge = knowledge_base.items()
                for k, v in new_knowledge:
                    self.know(v, self.knowledge_base, emora_knowledge=True)

        print('checking kb')
        self._check(self.knowledge_base)

        self.kb_predicate_types = self.knowledge_base.type_predicates()
        self.kb_subj_essentials = {}
        for c in self.knowledge_base.subtypes_of('subj_essential'):
            if self.knowledge_base.has(predicate_id=c):
                self.kb_subj_essentials.setdefault(self.knowledge_base.subject(c), set()).add(c)
        self.kb_obj_essentials = {}
        for c in self.knowledge_base.subtypes_of('obj_essential'):
            if self.knowledge_base.has(predicate_id=c):
                self.kb_obj_essentials.setdefault(self.knowledge_base.object(c), set()).add(c)

        if INFERENCE:
            self.nlg_inference_engine = InferenceEngine(device=device)
            if nlg_templates is not None and not isinstance(nlg_templates, ConceptGraph):
                print('checking templates')
                if USECACHE:
                    cached_knowledge, new_knowledge = self.stratify_cached_files(NLGCACHE, nlg_templates)
                    self.load_templates(cached_knowledge, new_knowledge, nlg_templates, NLGCACHE)
                else:
                    nlg = nlg_templates.items()
                    for k,v in nlg:
                        nlg_templates = ConceptGraph(namespace='t_')
                        self.know(v, nlg_templates, emora_knowledge=True, identify_nonasserts=True)
                        templates = nlg_templates.nlg_templates()
                        self.nlg_inference_engine.add(templates, nlg_templates.id_map().namespace)
                        self._check(nlg_templates, use_kb=True, file=k)
                self.nlg_inference_engine.matcher.process_queries()

            preprocess_queries = True
            if inference_engine is None:
                inference_engine = InferenceEngine(device=device)
            else:
                preprocess_queries = False
            self.inference_engine = inference_engine
            if inference_rules is not None and not isinstance(inference_rules, ConceptGraph):
                print('checking rules')
                if USECACHE:
                    cached_knowledge, new_knowledge = self.stratify_cached_files(INFCACHE, inference_rules)
                    self.load_rules(cached_knowledge, new_knowledge, inference_rules, INFCACHE)
                else:
                    rules = inference_rules.items()
                    for k, v in rules:
                        inference_rules = ConceptGraph(namespace='t_')
                        self.know(v, inference_rules, emora_knowledge=True, identify_nonasserts=True)
                        inferences = inference_rules.rules()
                        self.inference_engine.add(inferences, inference_rules.id_map().namespace)
                        self._check(inference_rules, use_kb=True, file=k)

        self.fallbacks = {}
        if fallbacks is not None:
            if isinstance(fallbacks, ConceptGraph):
                self.fallbacks = fallbacks.nlg_templates()
            else:
                fallback_cg = ConceptGraph(namespace='f_')
                for k, v in fallbacks.items():
                    self.know(v, fallback_cg, emora_knowledge=True, identify_nonasserts=True)
                self.fallbacks = fallback_cg.nlg_templates()
            if INFERENCE:
                fallback_recording_rules = {}
                for rule_id, (pre, post, vars) in self.fallbacks.items():
                    rpre = pre.copy()
                    rpost = ConceptGraph(predicates=[(rule_id, 'rfallback', None)], namespace='t_') #namespace should match inference_rules namespace above
                    rvars = set(vars)
                    truth_requests = rpre.subtypes_of(REQ_TRUTH)
                    arg_requests = rpre.subtypes_of(REQ_ARG)
                    for r in set(chain(truth_requests, arg_requests)) - {REQ_ARG, REQ_TRUTH}:
                        sig = pre.predicate(r)
                        rpre.remove(*sig)
                        rvars.remove(sig[3])
                    rpre.remove(REQ_TRUTH)
                    rpre.remove(REQ_ARG)
                    if len(set(rpre.related('emora'))) == 0:
                        rpre.remove('emora')
                    for s,t,o,i in list(rpre.predicates()):
                        if t != TYPE:
                            p = rpre.add(i, USER_AWARE)
                            rvars.add(p)
                            p2 = rpre.add(i, '_exists')
                            rvars.add(p2)
                    self.operate(self.universal_operators, cg=rpre)
                    fallback_recording_rules[rule_id] = (rpre, rpost, rvars)
                self.inference_engine.add(fallback_recording_rules, namespace='t_') #namespace should match inference_rules namespace above

        if INFERENCE and preprocess_queries:
            self.inference_engine.matcher.process_queries()

        if isinstance(working_memory, ConceptGraph):
            self.working_memory = working_memory
        else:
            self.working_memory = ConceptGraph(namespace='wm', supports={AND_LINK: False})
            self.consider(working_memory)

        self.subj_essential_types = {i for i in self.knowledge_base.subtypes_of(SUBJ_ESSENTIAL)
                                if not self.knowledge_base.has(predicate_id=i)}
        self.obj_essential_types = {i for i in self.knowledge_base.subtypes_of(OBJ_ESSENTIAL)
                                if not self.knowledge_base.has(predicate_id=i)}
        self.obj_essential_types.update({SPAN_REF, SPAN_DEF})

    def stratify_cached_files(self, type, sources):
        if not os.path.exists(type):
            os.mkdir(type)
        cached_files = {f.replace(CACHESEP, os.sep).replace('.json', '') for f in os.listdir(type) if os.path.isfile(os.path.join(type, f))}
        compat_knowledge_files = set(sources.keys())
        cached_knowledge = cached_files.intersection(compat_knowledge_files)
        new_knowledge = compat_knowledge_files.difference(cached_knowledge)

        up_to_date_cached = {c for c in cached_knowledge
                             if os.path.getmtime(os.path.join(type, (c+'.json').replace(os.sep, CACHESEP)))
                             > os.path.getmtime(c)}
        new_knowledge.update(cached_knowledge.difference(up_to_date_cached))
        up_to_date_cached = {(c + '.json').replace(os.sep, CACHESEP) for c in up_to_date_cached}
        return up_to_date_cached, new_knowledge

    def load_kb(self, cached, new_content, source, dir):
        for file in source:
            cache_version = (file + '.json').replace(os.sep, CACHESEP)
            if cache_version in cached:
                with open(os.path.join(dir, cache_version), 'r') as f:
                    d = json.load(f)
                cached_cg = ConceptGraph(namespace=d['namespace'])
                cached_cg.load(d)
                self.know(cached_cg, self.knowledge_base)
            elif file in new_content:
                v = source[file]
                new_cg = self.know(v, self.knowledge_base, emora_knowledge=True)
                savefile = os.path.join(dir, (file + '.json').replace(os.sep, CACHESEP))
                new_cg.save(savefile)
            else:
                raise Exception('File %s not in cached or new'%file)

    def load_templates(self, cached, new_content, source, dir):
        for file in source:
            cache_version = (file + '.json').replace(os.sep, CACHESEP)
            if cache_version in cached:
                with open(os.path.join(dir, cache_version), 'r') as f:
                    d = json.load(f)
                templates = {}
                mega_template_cg = None
                for rule, (pre, post, vars) in d.items():
                    pre_cg = ConceptGraph(namespace=pre['namespace'])
                    pre_cg.load(pre)
                    template_obj = Template(*post)
                    vars = set(vars)
                    templates[rule] = (pre_cg, template_obj, vars)
                    if mega_template_cg is None:
                        mega_template_cg = ConceptGraph(namespace=pre['namespace'])
                    mega_template_cg.concatenate(pre_cg)
                self.nlg_inference_engine.add(templates, pre_cg.id_map().namespace)
                if mega_template_cg is not None:
                    self._check(mega_template_cg, use_kb=True, file=file)
            elif file in new_content:
                v = source[file]
                nlg_templates = ConceptGraph(namespace='t_')
                self.know(v, nlg_templates, emora_knowledge=True, identify_nonasserts=True)
                templates = nlg_templates.nlg_templates()
                savefile = os.path.join(dir, (file + '.json').replace(os.sep, CACHESEP))
                d = {rule: (pre.save(), post.save(), list(vars)) for rule,(pre,post,vars) in templates.items()}
                with open(savefile, 'w') as f:
                    json.dump(d, f, indent=2)
                self.nlg_inference_engine.add(templates, nlg_templates.id_map().namespace)
                self._check(nlg_templates, use_kb=True, file=file)
            else:
                raise Exception('File %s not in cached or new' % file)

    def load_rules(self, cached, new_content, source, dir):
        for file in source:
            cache_version = (file + '.json').replace(os.sep, CACHESEP)
            if cache_version in cached:
                with open(os.path.join(dir, cache_version), 'r') as f:
                    d = json.load(f)
                rules = {}
                mega_rule_cg = None
                for rule, (pre, post, vars) in d.items():
                    pre_cg = ConceptGraph(namespace=pre['namespace'])
                    pre_cg.load(pre)
                    post_cg = ConceptGraph(namespace=post['namespace'])
                    post_cg.load(post)
                    vars = set(vars)
                    rules[rule] = (pre_cg, post_cg, vars)
                    if mega_rule_cg is None:
                        mega_rule_cg = ConceptGraph(namespace=pre['namespace'])
                    mega_rule_cg.concatenate(pre_cg)
                    mega_rule_cg.concatenate(post_cg)
                self.inference_engine.add(rules, pre_cg.id_map().namespace)
                if mega_rule_cg is not None:
                    self._check(mega_rule_cg, use_kb=True, file=file)
            elif file in new_content:
                v = source[file]
                inference_rules = ConceptGraph(namespace='t_')
                self.know(v, inference_rules, emora_knowledge=True, identify_nonasserts=True)
                inferences = inference_rules.rules()
                savefile = os.path.join(dir, (file + '.json').replace(os.sep, CACHESEP))
                d = {rule: (pre.save(), post.save(), list(vars)) for rule,(pre,post,vars) in inferences.items()}
                with open(savefile, 'w') as f:
                    json.dump(d, f, indent=2)
                self.inference_engine.add(inferences, inference_rules.id_map().namespace)
                self._check(inference_rules, use_kb=True, file=file)
            else:
                raise Exception('File %s not in cached or new' % file)

    def _check(self, cg, file=None, use_kb=False):
        for c in cg.concepts():
            if c not in ConceptCompiler._default_predicates \
                and c not in ConceptCompiler._default_types \
                and not cg.has(predicate_id=c):
                if len(cg.objects(c, TYPE)) == 0:
                    if not use_kb:
                        print('\t%s'%(c))
                    else:
                        if len(self.knowledge_base.objects(c, TYPE)) == 0:
                            print('\t%s (%s)'%(c, file))

    def know(self, knowledge, source_cg, **options):
        if not isinstance(knowledge, ConceptGraph):
            cg = ConceptGraph(namespace='_tmp_')
            ConceptGraph.construct(cg, knowledge, compiler=self.compiler)
            self._loading_options(cg, options)
            self._assertions(cg)
        else:
            cg = knowledge
        self.operate(self.universal_operators, cg=cg)
        source_cg.concatenate(cg)
        return cg

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

    def infer(self, aux_state=None, rules=None):
        if rules is None:
            solutions = self.inference_engine.infer(self.working_memory, aux_state)
        else:
            solutions = self.inference_engine.infer(self.working_memory, aux_state, dynamic_rules=rules)
        return solutions

    def apply(self, inferences):
        implications = {}
        for rid, (pre, post, sols) in inferences.items():
            for sol, virtual_preds in sols:
                implied = ConceptGraph(namespace=post._ids)
                for pred in post.predicates():
                    if pred[3] not in sol:
                        # if predicate instance is not in solutions, add to implication; otherwise, it already exists in WM
                        new_pred = []
                        for x in pred:
                            m = sol.get(x, x)
                            if m is not None and m.startswith('__virt_'):
                                m = implied.add(*virtual_preds[m]) # add the virtual type as a new predicate instance, m is the new id in the implied concept_graph
                                sol[x] = m
                            new_pred.append(m)
                        implied.add(*new_pred)
                for concept in post.concepts():
                    concept = sol.get(concept, concept)
                    implied.add(concept)
                for s, t, l in post.metagraph.edges():
                    implied.metagraph.add(sol.get(s, s), sol.get(t, t), l)
                for s in post.metagraph.nodes():
                    implied.metagraph.add(sol.get(s, s))
                features = {sol.get(k, k): v for k, v in post.features.items()}
                implied.features.update(features)
                implications.setdefault(rid, []).append((sol, implied))
        return implications

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
        result_dict = self.apply(inferences)
        for rule, results in result_dict.items():
            pre, post = inferences[rule][0], inferences[rule][1]
            for evidence, implication in results:
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
                    _process_requests(implication)
                    implied_nodes = self.consider(implication, evidence=evidence.values())
                    and_node = self.working_memory.id_map().get()
                    self.working_memory.features[and_node]['origin_rule'] = rule # store the implication rule that resulted in this and_node as metadata
                    for pre_node, evidence_node in evidence.items():
                        if self.working_memory.has(predicate_id=evidence_node):
                            self.working_memory.metagraph.add(evidence_node, and_node, AND_LINK)
                    for imp_node in implication.concepts():
                        if not implication.metagraph.in_edges(imp_node, REF): # add or_link only if imp_node is not part of a reference
                            self.working_memory.metagraph.add(and_node, implied_nodes[imp_node], OR_LINK)

    def _get_excluded_question_links(self, cg):
        constraints = set()
        questions = {*cg.subtypes_of(REQ_TRUTH), *cg.subtypes_of(REQ_ARG)} - {REQ_ARG, REQ_TRUTH}
        signatures = {cg.predicate(x) for x in questions}
        for sub, typ, obj, ins in signatures:
            constraints.add(ins)        # ins is a request predicate
            refs = cg.metagraph.out_edges(obj, REF)
            for sou, tar, lab in refs:
                constraints.add(tar)    # tar is a question constraint
        return constraints

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
        ignore = {'focus', 'center', 'var'}
        if gather_link == REF_SP:
            ignore.update({REQ_TRUTH, REQ_ARG}) # also ignore request predicates when gathering reference constraints
        node_to_spans = {}
        for s, t, _ in self.working_memory.metagraph.edges(label=gather_link):
            node_to_spans.setdefault(s, []).append(t)
        for node, span in node_to_spans.items():
            constraints = self.gather(node, span, ignore)
            for type in promote_links:
                self.working_memory.metagraph.add_links(node, constraints, type)
            for t in span:
                self.working_memory.metagraph.remove(node, t, gather_link)

    def gather(self, reference_node, constraints_as_spans, ignore):
        constraints = set()
        focal_nodes = set()
        for constraint_span in constraints_as_spans:
            if self.working_memory.has(constraint_span):
                foci = self.working_memory.objects(constraint_span, 'ref')
                focus = next(iter(foci))  # todo - could be more than one focal node in disambiguation situation?
                focal_nodes.add(focus)
        # add linking span versions of constraint spans as constraints too, if any
        for c in constraints_as_spans:
            link_c = '__linking__%s'%c
            if self.working_memory.has(link_c):
                foci = self.working_memory.objects(link_c, 'ref')
                focus = next(iter(foci))  # todo - could be more than one focal node in disambiguation situation?
                focal_nodes.add(focus)
        # expand constraint spans into constraint predicates
        for focal_node in focal_nodes:
            components = self.working_memory.metagraph.targets(focal_node, COMPS)
            # constraint found if constraint predicate is connected to reference node
            for component in components:
                if (not self.working_memory.has(predicate_id=component) or
                    self.working_memory.type(component) not in ignore) and \
                        self.working_memory.graph_component_siblings(component, reference_node):
                    constraints.add(component)
        return list(constraints)

    def resolve(self, aux_state, references=None):
        if references is None:
            references = self.working_memory.references()
        compatible_pairs = {}
        if len(references) > 0:
            inferences = self.inference_engine.infer(self.working_memory, aux_state, references, cached=False)
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
        return {c: self.kb_predicate_types[c] for c in self.working_memory.concepts() if c in self.kb_predicate_types}


    def pull_knowledge(self, limit, num_pullers, association_limit=None, subtype_limit=None, degree=1):
        kb = self.knowledge_base
        wm = self.working_memory
        # only consider concepts that are arguments of non-(type/expr/ref/def) predicates
        pullers = [c for c in wm.concepts()
                   if
                   not (wm.subjects(c, 'type') or wm.objects(c, 'expr') or wm.objects(c, 'ref') or wm.objects(c, 'def'))
                   and (wm.subjects(c) or wm.objects(c))
                   and wm.features.get(c, {}).get(SALIENCE, 0) > 0.0
                   and not c.isdigit()
                   and c not in {TIME, 'now', 'past', 'future'}]
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
        for length in range(2, 0,
                            -1):  # todo - inefficient; identify combinations -> empty intersection and ignore in further processing
            combos = combinations(pullers, length)
            for combo in combos:
                if len(combo) == 1 and ('emora' in combo or 'user' in combo):
                    continue
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
                                              subj_essentials=self.kb_subj_essentials,
                                              obj_essentials=self.kb_obj_essentials,
                                              type_predicates=self.kb_predicate_types))
                    for inst in backptrs.get(r, {r}):
                        to_add.update(kb.structure(inst,
                                                   subj_essentials=self.kb_subj_essentials,
                                                   obj_essentials=self.kb_obj_essentials,
                                                   type_predicates=self.kb_predicate_types))
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

    def prune_attended(self, aux_state, num_keep):
        # NOTE: essential predicates AND reference constraints must be maintained for selected concepts that are being kept

        #p.start('setup')
        wm = self.working_memory

        #p.next('select keep')
        options = {i for s,t,o,i in wm.predicates() if t not in chain(self.subj_essential_types, self.obj_essential_types, PRIM, {TYPE})}
        soptions = sorted(options,
                          key=lambda x: wm.features.get(x, {}).get(SALIENCE, 0),
                          reverse=True)
        keep = soptions[:num_keep]

        # delete all user and emora spans that occured SPANTURN turns ago
        #p.next('delete old spans')
        deletions = set()
        current_turn = aux_state.get('turn_index', -1)
        for s,t,o,i in chain(wm.predicates(predicate_type=SPAN_REF, object='user'),
                             wm.predicates(predicate_type=SPAN_REF, object='emora')):
            if '__linking__' in s:
                span_obj = Span.from_string(s[11:])
            else:
                span_obj = Span.from_string(s)
            if int(span_obj.turn) <= current_turn - SPANTURN:
                deletions.add(s)

        #p.next('setup essentials')
        keepers = set()
        type_predicates = self.working_memory.type_predicates()
        subj_essentials = {}
        for pe in self.subj_essential_types:
            for c in wm.subtypes_of(pe):
                if wm.has(predicate_id=c):
                    subj_essentials.setdefault(wm.subject(c), set()).add(c)

        obj_essentials = {}
        for pe in self.obj_essential_types:
            for c in wm.subtypes_of(pe):
                if wm.has(predicate_id=c):
                    obj_essentials.setdefault(wm.object(c), set()).add(c)
        #p.next('identify essentials')
        for k in keep:
            ess = wm.structure(k, subj_essentials, obj_essentials, type_predicates=type_predicates)
            structs = {c for sig in ess for c in sig if c is not None}
            keepers.update(structs)
            refs = wm.metagraph.targets(k, REF)
            keepers.update(refs)

        for k in set(keepers):
            keepers.update({c for sig in type_predicates.get(k, []) for c in sig})

        #p.next('remove not keep')
        to_remove = (wm.concepts() - keepers) | deletions

        for r in to_remove:
            # check if there is a SPAN_REF of the thing being deleted; if yes, delete it too
            span_ref_preds = self.working_memory.predicates(predicate_type=SPAN_REF, object=r)
            for s, t, o, i in span_ref_preds:
                self.working_memory.remove(s)
            wm.remove(r)
        #p.stop()


    def prune_predicates_of_type(self, inst_removals, subj_removals):
        for s, t, o, i in list(self.working_memory.predicates()):
            if t in inst_removals and self.working_memory.has(s, t, o, i):
                self.working_memory.remove(s, t, o, i)
            if t in subj_removals and self.working_memory.has(s):
                self.working_memory.remove(s)

    def operate(self, ops, aux_state=None, cg=None):
        if cg is None:
            cg = self.working_memory
        for opname, opfunc in ops.items():
            for _, _, _, i in list(cg.predicates(predicate_type=opname)):
                if cg.has(predicate_id=i): # within-loop-mutation check
                    opfunc(cg, i, aux_state)

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
            pass
        if 'identify_nonasserts' in options:
            # loading rules and templates separate from KB disassociates the predicates from their types
            # to preserve nonassertion of confidence, need to retrieve nonassert types where appropriate
            for s,t,o,i in list(cg.predicates()):
                if NONASSERT in self.knowledge_base.types(t) and not cg.has(t, 'type', NONASSERT):
                    cg.add(t,'type', NONASSERT)
        if 'assert_conf' in options:
            self._assertions(cg)

    def _assertions(self, cg):
        assertions(cg)


if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



