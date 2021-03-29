
from abc import abstractmethod
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.inference_engine import InferenceEngine
import torch, gc
from GRIDD.utilities import collect

LOCALDEBUG = False

class ParseToLogic:

    def __init__(self, knowledge_base, *template_file_names, device='cpu'):
        self.knowledge_base = knowledge_base
        rules = KnowledgeParser.rules(*template_file_names)
        for rule_id, rule in rules.items():
            self._reference_expansion(rule[0])
        self.inference_engine = InferenceEngine(*[(*rule, rule_id) for rule_id, rule in rules.items()], device=device)
        self.spans = []

    def _reference_expansion(self, pregraph):
        """
        Expand vars in precondition to include expression and reference links.

        Vars are expressions of some canonical expression which refers to some concept.

        If var has a logical supertype (denoted by 'ltype' predicate), add a type predicate
        between referred concept and the supertype.
        """
        for concept in pregraph.concepts():
            if pregraph.has(concept, 'var') and not pregraph.has(predicate_id=concept) \
                and len(pregraph.predicates(concept, 'ref')) == 0 and len(pregraph.predicates(concept, 'expr')) == 0:
                # found variable entity instance that does not already have expression defined as part of rule
                found_supertype = False
                for supertype in pregraph.objects(concept, 'ltype'):
                    found_supertype = True
                    self._expand_references(pregraph, concept, supertype)
                if not found_supertype:
                    self._expand_references(pregraph, concept)

    def _expand_references(self, pregraph, concept, supertype=None):
        expression_var = pregraph.id_map().get()
        ref = pregraph.add(concept, 'ref', expression_var)
        concept_var = pregraph.id_map().get()
        expr = pregraph.add(expression_var, 'expr', concept_var)
        new_nodes = [expression_var, ref, concept_var, expr]
        if supertype is not None:
            concept_type = pregraph.add(concept_var, 'type', supertype)
            pregraph.remove(concept, 'ltype', supertype)
            new_nodes.append(concept_type)
        for n in new_nodes:
            pregraph.add(n, 'var')

    @abstractmethod
    def text_to_graph(self, *args):
        """
        return: ConceptGraph representation of the text's surface form.
                For example, a graph of the dependency parse of the last turn.
        """
        pass

    def __call__(self, *args, **kwargs):
        """
        Run the text to logic algorithm using *args as input to translate()
        """
        self.spans = []
        return self.translate(*args)

    def translate(self, *args):
        ewm = self.text_to_graph(*args)
        self._expression_pull(ewm)
        self._unknown_expression_identification(ewm)
        rule_assignments = {(pre, post, rule): sols for rule, (pre, post, sols) in self._inference(ewm).items()}
        mentions = self._get_mentions(rule_assignments, ewm)
        merges = self._get_merges(rule_assignments, ewm)
        if LOCALDEBUG:
            self.display_mentions(mentions, ewm)
            self.display_merges(merges, ewm)
        return mentions, merges

    def _expression_pull(self, ewm):
        """
        Pull expressions from KB into the expression working_memory
        """
        ewm.pull(order=1,
                 concepts=['"%s"'%ewm.features[span_node]["span_data"].expression for span_node in self.spans],
                 exclude_on_pull={'type'})

    def _unknown_expression_identification(self, ewm):
        """
        Create "UNK" expression nodes for all nodes with no expr references.
        """
        for span_node in self.spans:
            expression = '"%s"' % ewm.features[span_node]["span_data"].expression
            references = ewm.objects(expression, 'expr')
            if len(references) == 0:
                unk_node = ewm.add(ewm.id_map().get())
                types = ewm.types(span_node)
                pos_type = 'other'
                for n in ['verb', 'noun', 'pron', 'adj', 'adv']:
                    if n in types:
                        pos_type = n
                        break
                ewm.add(unk_node, 'type', 'unknown_%s'%pos_type)
                if not ewm.has('unknown_%s'%pos_type, 'type', 'object'):
                    ewm.add('unknown_%s' % pos_type, 'type', 'object')
                ewm.add(expression, 'expr', unk_node)

    def _inference(self, ewm, retry=None):
        """
        Apply the template rules to the current expression working_memory
        and get the variable assignments of the solutions
        """
        try:
            solutions = self.inference_engine.infer(ewm)
            return solutions
        except RuntimeError as e:
            print('\n' + str(e))
            if retry == 4:
                return {}
            gc.collect()
            torch.cuda.empty_cache()
            return self._inference(ewm, retry=retry+1 if retry is not None else 1)


        # Parse templates are priority-ordered, such that the highest-priority matching template
        # for a specific center is kept and all other templates with the same center are discarded.
        # Affects _get_mentions() and _get_merges()!

    def _update_centers(self, centers_handled, post, center, solution):
        centers_handled.add(center)
        covered = post.predicates(predicate_type='cover')
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
        auxes = set()
        for rule, solutions in assignments.items():
            link = False
            pre, post = rule[0], rule[1]
            center_pred = post.predicates(predicate_type='center')
            if len(center_pred) > 0:
                ((center_var, _, _, _),) = center_pred
                (expression_var,) = pre.objects(center_var, 'ref')
                (concept_var,) = pre.objects(expression_var, 'expr')
                maintain_in_mention_graph = [center_var, expression_var, concept_var]
            else: # center-less parse2logic rules specify linking structures but are not defining a specific token mention
                ((center_var, _, _, _),) = post.predicates(predicate_type='link')
                link = True
                maintain_in_mention_graph = []
            for solution in solutions:
                center = solution.get(center_var, center_var)
                if link:
                    center = '__linking__%s' % center
                if center not in centers_handled:
                    cg = ConceptGraph(namespace='ment_')
                    post_to_cg_map = cg.concatenate(post)
                    self._update_centers(centers_handled, post, center, solution)
                    mentions[center] = cg
                    if not center.startswith('__linking__'):
                        post_to_ewm_map = {node: self._get_concept_of_span(solution[node], ewm)
                                           for node in post.concepts()
                                           if node in solution and node in maintain_in_mention_graph}
                        if ewm.has(center, 'assert'):
                            # if center is asserted, add assertion to focus node
                            ((focus, _, _, _),) = cg.predicates(predicate_type='focus')
                            cg.add(focus, 'assert')
                        if len(cg.predicates(predicate_type='aux_time')) > 0:
                            auxes.add(center)
                        for post_node, ewm_node in post_to_ewm_map.items():
                            cg_node = post_to_cg_map[post_node]
                            cg.add(ewm_node)
                            if ewm_node.startswith(ewm.id_map().namespace):
                                cg.merge(cg_node, ewm_node, strict_order=True)
                            else:
                                cg.merge(ewm_node, cg_node, strict_order=True)
                            self._add_unknowns_to_cg(ewm_node, ewm, cg_node, cg)
                        cg.add(center)
                        cg.features.update(ewm.features, concepts={center})

        for aux in auxes: # replaces `time` of head predicate of aux-span with `aux_time`
            heads_of_aux = ewm.subjects(aux, 'aux')
            for head in heads_of_aux:
                aux_cg = mentions[aux]
                preds = aux_cg.predicates(predicate_type='aux_time')
                if len(preds) > 0:
                    ((_, _, aux_time, _), ) = preds
                    head_cg = mentions[head]
                    preds = head_cg.predicates(predicate_type='time')
                    if len(preds) > 0:
                        ((s,t,o,i), ) = preds
                        head_cg.remove(s,t,o,i)
                    else: #todo - update comps/reference links???
                        ((s,_,_,_), ) = head_cg.predicates(predicate_type='focus')
                        i = head_cg.id_map().get()
                    head_cg.add(s, 'time', aux_time, i)
            del mentions[aux]
        return mentions

    def _add_unknowns_to_cg(self, source_node, source, cg_node, cg):
        for n in ['verb', 'noun', 'pron', 'adj', 'adv', 'other']:
            unknown_type = 'unknown_%s' % n
            if source.has(source_node, 'type', unknown_type) and not cg.has(cg_node, 'type', unknown_type):
                cg.add(cg_node, 'type', unknown_type)
                break

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
            ((focus_var,t,o,i),) = post.predicates(predicate_type='focus')
            center_pred = post.predicates(predicate_type='center')
            if len(center_pred) > 0:
                ((center_var, t, o, i),) = center_pred
            else:
                ((center_var, _, _, _),) = post.predicates(predicate_type='link')
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
                    # for (_,o,t) in post.bipredicates_of_subject(focus):
                    #     if o in solution:
                    #         pass
                    #     if t in solution:
                    #         pass
                    #     for inst in post.bipredicate(focus,o,t):
                    #         if inst in solution:
                    #             pass
                    # for (_,t) in post.monopredicates_of_subject(focus):
                    #     if t in solution:
                    #         pass
                    #     for inst in post.bipredicate(focus,t):
                    #         if inst in solution:
                    #             pass
                    # for (s,_,t) in post.bipredicates_of_object(focus):
                    #     if s in solution:
                    #         pass
                    #     if t in solution:
                    #         pass
                    #     for inst in post.bipredicate(s,focus,t):
                    #         if inst in solution:
                    #             pass
                    # for tuple, inst in post.get_instances_of_type(focus):
                    #     # get all predicates that use focus as type, if applicable
                    #     if len(tuple) == 3:
                    #         s,o,_ = tuple
                    #         if s in solution:
                    #             pass
                    #         if o in solution:
                    #             pass
                    #     elif len(tuple) == 2:
                    #         s,_ = tuple
                    #         if s in solution:
                    #             pass

        return merges

    def display_mentions(self, mentions, ewm):
        """
        Display the mentions with their concepts instead of spans
        """
        print()
        for span, mention_graph in mentions.items():
            print('%s MENTION GRAPH:: '%span)
            for s,t,o,inst in mention_graph.predicates():
                if o is not None:
                    subj = self._get_concept_of_span(s,ewm)
                    obj = self._get_concept_of_span(o, ewm)
                    typ = self._get_concept_of_span(t, ewm)
                    print('\t[%s]\t-> %s(%s,%s)'%(inst,typ,subj,obj))
                else:
                    if t != 'var':
                        subj = self._get_concept_of_span(s, ewm)
                        typ = self._get_concept_of_span(t, ewm)
                        print('\t[%s]\t-> %s(%s)' % (inst, typ, subj))
            print()

    def _get_concept_of_span(self, span, ewm):
        expression = self._get_expression_of_span(span, ewm)
        if expression is not None:
            # todo - disambiguation between multiple concepts per expression (for now, selecting first)
            expressions = ewm.objects(expression, 'expr')
            concept_var = next(iter(expressions))
            # unknown_type = None
            # for n in ['verb', 'noun', 'pron', 'adj', 'adv', 'other']:
            #     if ewm.has(concept_var,'type','unknown_%s' % n):
            #         unknown_type = n
            # if unknown_type is not None:
            #     return 'unknown_%s'%unknown_type
            return concept_var
        return span

    def _get_expression_of_span(self, span, ewm):
        expressions = ewm.objects(span, 'ref')
        if len(expressions) == 1:
            return expressions.pop()
        return None

    def display_merges(self, merges, ewm):
        """
        Display the merges with their concepts instead of spans
        """
        print()
        print("MERGES:: ")
        for (span1, pos1), (span2, pos2) in merges:
            concept1 = self._get_concept_of_span(span1, ewm)
            concept2 = self._get_concept_of_span(span2, ewm)
            print("\t(%s,%s)\t<=> (%s,%s)"%(concept1,pos1,concept2,pos2))

