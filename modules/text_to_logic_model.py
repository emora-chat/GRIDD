
from abc import abstractmethod
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.utilities import Span

LOCALDEBUG=False

"""
Notes:
    predicate_types in post cannot match predicate_types in pre (other than `type`)
"""

class ParseToLogic:

    def __init__(self, knowledge_base, template_starter_predicates, *template_file_names):
        self.knowledge_base = knowledge_base
        self.inference_engine = InferenceEngine()
        self.templates = ConceptGraph(predicates=template_starter_predicates)
        self._template_parser = KnowledgeParser(kg=self.templates, base_nodes=self.templates.concepts(), ensure_kb_compatible=False)
        self.ordered_rule_ids = self.load_templates(*template_file_names)
        self.rules = self.inference_engine.generate_rules_from_graph(self.templates, with_names=True)
        for rule in self.rules:
            self._reference_expansion(rule[0])
        self.spans = []

    def load_templates(self, *filenames_or_logicstrings):
        ordered_rule_ids = []
        for input in filenames_or_logicstrings:
            if input.endswith('.kg'):
                input = open(input, 'r').read()
            if len(input.strip()) > 0:
                tree = self._template_parser.parse(input)
                additions = self._template_parser.transform(tree)
                for addition in additions:
                    id_map = self.templates.concatenate(addition)
                    s = addition.predicates(predicate_type='post')[0][0]
                    ordered_rule_ids.append(id_map.get(s,s))
        return ordered_rule_ids

    def _reference_expansion(self, pregraph):
        """
        Expand vars in precondition to include expression and reference links.

        Vars are expressions of some canonical expression which refers to some concept.

        If var has a logical supertype (denoted by 'ltype' predicate), add a type predicate
        between referred concept and the supertype.
        """
        for concept in pregraph.concepts():
            if pregraph.has(concept, 'var') and not pregraph.has(predicate_id=concept) \
                and len(pregraph.predicates(concept, 'exprof')) == 0 and len(pregraph.predicates(concept, 'expr')) == 0:
                # found variable entity instance that does not already have expression defined as part of rule
                found_supertype = False
                for supertype in pregraph.objects(concept, 'ltype'):
                    found_supertype = True
                    self._expand_references(pregraph, concept, supertype)
                if not found_supertype:
                    self._expand_references(pregraph, concept)

    def _expand_references(self, pregraph, concept, supertype=None):
        expression_var = pregraph._get_next_id()
        exprof = pregraph.add(concept, 'exprof', expression_var)
        concept_var = pregraph._get_next_id()
        expr = pregraph.add(expression_var, 'expr', concept_var)
        new_nodes = [expression_var, exprof, concept_var, expr]
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
        rule_assignments = self._inference(ewm)
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
        ewm.pull(order=1, concepts=['"%s"'%span_node.string for span_node in self.spans])

    def _unknown_expression_identification(self, ewm):
        """
        Create "UNK" expression nodes for all nodes with no expr references.
        """
        for span_node in self.spans:
            expression = '"%s"' % span_node.string
            references = ewm.objects(expression, 'expr')
            if len(references) == 0:
                unk_node = ewm.add(ewm._get_next_id())
                types = ewm.supertypes(span_node)
                pos_type = 'other'
                for n in ['verb', 'noun', 'pron', 'adj', 'adv']:
                    if n in types:
                        pos_type = n
                        break
                ewm.add(unk_node, 'type', 'unknown_%s'%pos_type)
                ewm.add(expression, 'expr', unk_node)

    def _inference(self, ewm):
        """
        Apply the template rules to the current expression working_memory
        and get the variable assignments of the solutions
        """
        return self.inference_engine.run(ewm, *self.rules, ordered_rule_ids=self.ordered_rule_ids)

        # Parse templates are priority-ordered, such that the highest-priority matching template
        # for a specific center is kept and all other templates with the same center are discarded.
        # Affects _get_mentions() and _get_merges()!

    def _get_mentions(self, assignments, ewm):
        """
        Produce dict<mention span: mention graph>.

        assignments: dict<rule: list<assignments>>
        """
        centers_handled = set() # `markcover` predicates also used here
        mentions = {}
        for rule, solutions in assignments.items():
            pre, post = rule[0], rule[1]
            ((center_var,t,o,i),) = post.predicates(predicate_type='center')
            for solution in solutions:
                (expression_var,) = pre.objects(center_var, 'exprof')
                (concept_var,) = pre.objects(expression_var, 'expr')
                center = solution[center_var]
                if center not in centers_handled:
                    centers_handled.add(center)
                    m = {}
                    cg = ConceptGraph(namespace=post._namespace)
                    cg._next_id = post._next_id
                    for node in post.concepts():
                        if node in solution:
                            if node in [center_var,expression_var,concept_var]:
                                m[node] = self._get_concept_of_span(solution[node], ewm)
                            else:
                                m[node] = cg._get_next_id()
                        else:
                            m[node] = node
                    for subject, typ, object, inst in post.predicates():
                        if object is not None:
                            cg.add(m[subject], m[typ], m[object], predicate_id=m[inst])
                        else:
                            cg.add(m[subject], m[typ], predicate_id=m[inst])
                    mentions[center] = cg
        return mentions

    def _get_merges(self, assignments, ewm):
        """
        Produce scored pairs of (mention span, path).

        assignments: dict<rule: list<assignments>>
        """
        centers_handled = set()
        merges = []
        for rule, solutions in assignments.items():
            pre, post = rule[0], rule[1]
            ((focus_var,t,o,i),) = post.predicates(predicate_type='focus')
            ((center_var,t,o,i),) = post.predicates(predicate_type='center')
            for solution in solutions:
                focus = solution.get(focus_var, focus_var)
                center = solution.get(center_var, center_var)
                if center not in centers_handled:
                    centers_handled.add(center)
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
            (concept_var,) = ewm.objects(expression, 'expr')
            unknown_type = None
            for n in ['verb', 'noun', 'pron', 'adj', 'adv', 'other']:
                if ewm.has(concept_var,'type','unknown_%s' % n):
                    unknown_type = n
            if unknown_type is not None:
                return 'unk_%s'%unknown_type
            return concept_var
        return span

    def _get_expression_of_span(self, span, ewm):
        expressions = ewm.objects(span, 'exprof')
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

