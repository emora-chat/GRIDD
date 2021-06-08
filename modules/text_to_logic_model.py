
from abc import abstractmethod
from itertools import chain
from GRIDD.data_structures.concept_graph import ConceptGraph
# from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.graph_matching.inference_engine import InferenceEngine
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.data_structures.id_map import IdMap
from GRIDD.utilities import collect
from GRIDD.globals import *
from GRIDD.intcore_server_globals import *
from GRIDD.data_structures.reference_identifier import REFERENCES_BY_RULE, QUESTION_INST_REF, subtree_dependencies, parent_subtree_dependencies

class ParseToLogic:

    # Parse templates are priority-ordered, such that the highest-priority matching template
    # for a specific center is kept and all other templates with the same center are discarded.
    # Affects _get_mentions() and _get_merges()!

    def __init__(self, kb, template_file, device='cpu'):
        if template_file is not None:
            if not isinstance(template_file, dict):
                rules = self.parse_rules_from_file(template_file)
            else:
                rules = template_file
            parse_inference = InferenceEngine(rules, NLU_NAMESPACE, device=device)
            self.intcore = IntelligenceCore(knowledge_base=kb,
                                        inference_engine=parse_inference,
                                        device=device)
        else:
            parse_inference = InferenceEngine(device=device)
            self.intcore = IntelligenceCore(knowledge_base=kb,
                                            inference_engine=parse_inference,
                                            device=device)
        self.spans = []

    def parse_rules_from_file(self, file):
        cg = ConceptGraph(list(collect(file).values()), namespace=NLU_NAMESPACE)
        rules = cg.rules()
        rules = dict(sorted(rules.items(), key=lambda item: cg.features[item[0]]['rindex']))
        for rule_id, rule in rules.items():
            self._reference_expansion(rule[0], rule[2])
        return rules

    def _reference_expansion(self, pregraph, vars):
        """
        Expand vars in precondition to include expression and reference links.

        Vars are expressions of some canonical expression which refers to some concept.

        If var has a logical supertype (denoted by 'ltype' predicate), add a type predicate
        between referred concept and the supertype. And remove the `ltype` predicate from the
        pregraph and from the vars.
        """
        original_vars = set(vars)
        for concept in pregraph.concepts():
            if concept in original_vars and not pregraph.has(predicate_id=concept) \
                and len(list(pregraph.predicates(concept, 'ref'))) == 0 and \
                    len(list(pregraph.predicates(concept, 'expr'))) == 0:
                # found variable entity instance that does not already have expression defined as part of rule
                found_supertype = False
                for supertype in pregraph.objects(concept, 'ltype'):
                    found_supertype = True
                    expression_var = pregraph.id_map().get()
                    ref = pregraph.add(concept, 'ref', expression_var)
                    concept_var = pregraph.id_map().get()
                    expr = pregraph.add(expression_var, 'expr', concept_var)
                    concept_type = pregraph.add(concept_var, 'type', supertype)
                    to_remove = [pred[3] for pred in pregraph.predicates(concept, 'ltype', supertype)]
                    pregraph.remove(concept, 'ltype', supertype)
                    vars.update([expression_var, ref, concept_var, expr, concept_type])
                    vars.difference_update(to_remove)
                    original_vars.difference_update(to_remove) # remove ltype predicate instance from vars; otherwise, it will be added as constraint with ref and expression
                if pregraph.has('ltype'):
                    pregraph.remove('ltype')
                if not found_supertype:
                    expression_var = pregraph.id_map().get()
                    ref = pregraph.add(concept, 'ref', expression_var)
                    concept_var = pregraph.id_map().get()
                    expr = pregraph.add(expression_var, 'expr', concept_var)
                    vars.update([expression_var, ref, concept_var, expr])

    @abstractmethod
    def text_to_graph(self, *args):
        """
        return: ConceptGraph representation of the text, e.g. cg of the dependency parse
        """
        pass

    def __call__(self, *args):
        """
        Run the text to logic algorithm using *args as input to translate()
        """
        self.spans = []
        return self.translate(*args)

    def translate(self, *args):
        wm = self.intcore.working_memory
        self.intcore.working_memory.clear()
        parse_graph = self.text_to_graph(*args)
        if len(parse_graph.concepts()) == 0: # empty utterance
            return {}, []
        self.intcore.consider(parse_graph)
        self._span_to_concepts()
        types = self.intcore.pull_types()
        self.intcore.consider(types)
        # todo - this is just a temporary patch for missing type expression
        for s,_,_,_ in wm.predicates(predicate_type='expr'):
            if not wm.has(s, 'type', 'expression'):
                wm.add(s, 'type', 'expression')
        rule_assignments = self.intcore.infer()
        sorted_assignments = {}
        for k2 in self.intcore.inference_engine.rules:
            for rule, (pre, post, sols) in rule_assignments.items():
                if rule == k2:
                    sorted_assignments[(pre, post, rule)] = [s[0] for s in sols]
        mentions = self._get_mentions(sorted_assignments, wm)
        merges = self._get_merges(sorted_assignments, wm)
        return mentions, merges

    def _span_to_concepts(self):
        wm = self.intcore.working_memory
        kb = self.intcore.knowledge_base
        for span_node in wm.subjects('span', 'type'):
            data = wm.features[span_node]['span_data']
            surface_form = data.string
            lemma = data.expression
            sf_concepts = kb.objects(f'"{surface_form}"', 'expr')
            if len(sf_concepts) > 0:
                c = next(iter(sf_concepts))
                wm.add(span_node, 'ref', f'"{surface_form}"')
                wm.add(f'"{surface_form}"', 'expr', c)
            l_concepts = None
            if len(sf_concepts) == 0:
                l_concepts = kb.objects(f'"{lemma}"', 'expr')
                if len(l_concepts) > 0:
                    c = next(iter(l_concepts))
                    wm.add(span_node, 'ref', f'"{lemma}"')
                    wm.add(f'"{lemma}"', 'expr', c)
            if not sf_concepts and not l_concepts:
                # Create "UNK" expression nodes for all nodes with no expr references.
                unk_node = wm.add(wm.id_map().get())
                types = wm.types(span_node)
                pos_type = 'other'
                for n in ['verb', 'noun', 'pron', 'adj', 'adv']:
                    if n in types:
                        pos_type = n
                        break
                wm.add(unk_node, 'type', 'unknown_%s' % pos_type)
                if not wm.has('unknown_%s' % pos_type, 'type', 'object'):
                    wm.add('unknown_%s' % pos_type, 'type', 'object')
                wm.add(span_node, 'ref', f'"{surface_form}"')
                wm.add(f'"{surface_form}"', 'expr', unk_node)

    def _update_centers(self, centers_handled, post, center, solution):
        centers_handled.add(center)
        covered = list(post.predicates(predicate_type='cover'))
        if len(covered) > 0:
            for cover_var, _, _, _ in covered:
                centers_handled.add(solution[cover_var])

    def _get_mentions(self, assignments, ewm):
        """
        Produce dict<mention span: mention graph>.
        assignments: dict<rule: list<assignments>>
        """
        centers_handled = set()
        mentions = {}
        mention_ids = IdMap(namespace='ment_')
        time_promotions = set()
        for rule, solutions in assignments.items():
            link = False
            pre, post, rule_name = rule[0], rule[1], rule[2]
            center_pred = list(post.predicates(predicate_type='center'))
            if len(center_pred) > 0:
                ((center_var, _, _, _),) = center_pred
                (expression_var,) = pre.objects(center_var, 'ref')
                (concept_var,) = pre.objects(expression_var, 'expr')
                maintain_in_mention_graph = [center_var, expression_var, concept_var]
            else: # center-less parse2logic rules specify linking structures but are not defining a specific token mention
                ((center_var, _, _, _),) = list(post.predicates(predicate_type='link'))
                link = True
                maintain_in_mention_graph = []
            for solution in solutions:
                center = solution.get(center_var, center_var)
                if link : # and center not in centers_handled: # if current linking span is already used as a centered span, skip it as a linker
                    center = '__linking__%s' % center
                if center not in centers_handled:
                    self._update_centers(centers_handled, post, center, solution)
                    post_to_ewm_map = {node: self._get_concept_of_span(solution[node], ewm)
                                       for node in post.concepts()
                                       if node in solution and node in maintain_in_mention_graph}
                    mention_cg = ConceptGraph(namespace=mention_ids, concepts={center})
                    post_to_cg_map = mention_cg.concatenate(post)
                    for post_node, ewm_node in post_to_ewm_map.items():
                        cg_node = post_to_cg_map[post_node]
                        mention_cg.add(ewm_node)
                        if ewm_node.startswith(ewm.id_map().namespace):
                            mention_cg.merge(cg_node, ewm_node, strict_order=True)
                        else:
                            mention_cg.merge(ewm_node, cg_node, strict_order=True)
                        self._add_unknowns_to_cg(ewm_node, ewm, cg_node, mention_cg)
                    self._get_span_links(rule_name, mention_cg, center, ewm)
                    mentions[center] = mention_cg
                    if not center.startswith('__linking__'):
                        post_to_ewm_map = {node: self._get_concept_of_span(solution[node], ewm)
                                           for node in post.concepts()
                                           if node in solution and node in maintain_in_mention_graph}
                        if len(list(mention_cg.predicates(predicate_type='p_time'))) > 0:
                            time_promotions.add(center)
                        for post_node, ewm_node in post_to_ewm_map.items():
                            cg_node = post_to_cg_map[post_node]
                            mention_cg.add(ewm_node)
                            if ewm_node.startswith(ewm.id_map().namespace):
                                mention_cg.merge(cg_node, ewm_node, strict_order=True)
                            else:
                                mention_cg.merge(ewm_node, cg_node, strict_order=True)
                            self._add_unknowns_to_cg(ewm_node, ewm, cg_node, mention_cg)
                        mention_cg.features.update(ewm.features, concepts={center})
                    else:
                        mention_cg.features[center]["span_data"] = ewm.features[center.replace('__linking__','')]["span_data"]
        self._promote_time(time_promotions, ewm, mentions)
        return mentions

    def _add_unknowns_to_cg(self, source_node, source, cg_node, cg):
        for n in ['verb', 'noun', 'pron', 'adj', 'adv', 'other']:
            unknown_type = 'unknown_%s' % n
            if source.has(source_node, 'type', unknown_type) and not cg.has(cg_node, 'type', unknown_type):
                cg.add(cg_node, 'type', unknown_type)
                break

    def _get_comps(self, rule_name, focus_node, mention_cg):
        """
        Gathers the components of the mention as determined by the origin rule.
        Components are all predicates and entities that fully define the structure of the focus node.
        """
        # All predicates are components
        comps = [pred[3] for pred in mention_cg.predicates() if pred[1] not in {'focus', 'center', 'cover'}]
        # For argument questions, add the question object
        if rule_name in {'q_aux_adv', 'q_adv', 'qdet_copula_present', 'qdet_copula_past', 'dat_question', 'qw_copula_past', 'qw_copula_present'}:
            preds = list(mention_cg.predicates(predicate_type=REQ_ARG))
            if preds:
                ((_, _, o, _),) = preds
            else:
                ((_, _, o, _),) = list(mention_cg.predicates(predicate_type=REQ_TRUTH))
            comps.append(o)
        # For various rules, the focal node is not a predicate instance so it needs to be added manually
        if rule_name in {'obj_question', 'sbj_question', 'q_aux_det', 'q_det',
                         'ref_concept_determiner', 'inst_concept_determiner',
                         'other_concept_determiner', 'he_pron', 'she_pron', 'determiner',
                         'obj_of_possessive', 'ref_pron', 'single_word'}:
            comps.append(focus_node)
        return comps

    def _get_span_links(self, rule_name, mention_cg, center, ewm):
        ((focus_node, _, _, _),) = list(mention_cg.predicates(predicate_type='focus'))

        if rule_name in REFERENCES_BY_RULE:  # identify reference spans
            if rule_name in QUESTION_INST_REF:
                # some questions have focus node as the question predicate instance,
                # but the reference links should attach to the target of the question predicate instance
                ref_inst = mention_cg.predicate(focus_node)[2]
            else:
                ref_inst = focus_node
            mention_cg.metagraph.add_links(ref_inst, REFERENCES_BY_RULE[rule_name](center, ewm) + [center], REF_SP)

        comps = self._get_comps(rule_name, focus_node, mention_cg)
        mention_cg.metagraph.add_links(focus_node, comps, COMPS)

        if ewm.has(center, ASSERT):  # if center is asserted, add assertion to focus node
            mention_cg.add('user', ASSERT, focus_node)
            mention_cg.metagraph.add_links(focus_node, subtree_dependencies(center, ewm) + [center], DP_SUB)

    def _promote_time(self, promotions, ewm, mentions):
        for p in promotions: # replaces obj of `time` of head predicate of promotion with obj of `p_time`
            heads = chain(ewm.subjects(p, 'aux'), ewm.subjects(p, 'raise'))
            for head in heads:
                promotion_cg = mentions[p]
                preds = list(promotion_cg.predicates(predicate_type='p_time'))
                if len(preds) > 0:
                    (promotion_time_pred,) = preds
                    head_cg = mentions[head]
                    preds = list(head_cg.predicates(predicate_type='time'))
                    if len(preds) > 0:
                        ((s,t,o,i), ) = preds
                        head_cg.remove(s,t,o,i)
                    else:
                        ((s,_,_,_), ) = list(head_cg.predicates(predicate_type='focus'))
                        i = head_cg.id_map().get()
                    head_cg.add(s, TIME, promotion_time_pred[2], i)
                    head_cg.metagraph.add(s, i, COMPS)
                    promotion_cg.remove(*promotion_time_pred)
            if not list(mentions[p].predicates(predicate_type='focus')):
                del mentions[p]

    def _get_merges(self, assignments, ewm):
        """
        Produce scored pairs of (mention span, path).
        assignments: dict<rule: list<assignments>>
        """
        centers_handled = set()
        merges = []
        for rule, solutions in assignments.items():
            pre, post = rule[0], rule[1]
            link = False
            ((focus_var,t,o,i),) = list(post.predicates(predicate_type='focus'))
            center_pred = list(post.predicates(predicate_type='center'))
            if len(center_pred) > 0:
                ((center_var, t, o, i),) = center_pred
            else:
                ((center_var, _, _, _),) = list(post.predicates(predicate_type='link'))
                link = True
            for solution in solutions:
                focus = solution.get(focus_var, focus_var)
                center = solution.get(center_var, center_var)
                if link:
                    center = '__linking__%s' % center
                if center not in centers_handled:
                    self._update_centers(centers_handled, post, center, solution)
                    if post.has(predicate_id=focus):
                        # focus is a predicate instance, need to consider its subj/obj/type
                        if post.subject(focus) in solution and solution[post.subject(focus)] != center:
                            pair = ((center,'subject'),
                                    (solution[post.subject(focus)],'self'))
                            merges.append(pair)
                        if post.object(focus) in solution and solution[post.object(focus)] != center:
                            pair = ((center, 'object'),
                                    (solution[post.object(focus)], 'self'))
                            merges.append(pair)
                        if post.type(focus) in solution and solution[post.type(focus)] != center:
                            pair = ((center, 'type'),
                                    (solution[post.type(focus)], 'self'))
                            merges.append(pair)
                        # if focus has attachments with variables, need to consider them too
                        # for _, t, o, i in post.predicates(focus):
                        #     if t not in {'focus', 'cover', 'center', 'assert'} and o in solution and solution[o] != center:
                        #         pair = ((center, 'subject'),
                        #                 (solution[o], 'self'))
                        #         merges.append(pair)
                        # for s, t, _, i in post.predicates(object=focus):
                        #     if t not in {'focus', 'cover', 'center', 'assert'} and s in solution and solution[o] != center:
                        #         pass
        return merges

    def _get_concept_of_span(self, span, ewm):
        expression = self._get_expression_of_span(span, ewm)
        if expression is not None:
            # todo - disambiguation between multiple concepts per expression (for now, selecting first)
            expressions = ewm.objects(expression, 'expr')
            concept_var = next(iter(expressions))
            return concept_var
        return span

    def _get_expression_of_span(self, span, ewm):
        expressions = ewm.objects(span, 'ref')
        if len(expressions) == 1:
            return expressions.pop()
        return None

