
from abc import ABC, abstractmethod
from collections import defaultdict
from knowledge_base.concept_graph import ConceptGraph

DEBUG=True

class TextToLogicModel(ABC):

    def __init__(self, knowledge_base, model, template_base, *template_file_names):
        self.knowledge_base = knowledge_base
        self.model = model
        self.templates = template_base
        for fn in template_file_names:
            with open(fn, 'r') as f:
                self.templates.add_knowledge(f.read())
        self.rules = self.templates._concept_graph.generate_inference_graphs()
        for rule in self.rules:
            self._reference_expansion(rule.precondition)

    @abstractmethod
    def text_to_graph(self, turns, knowledge_base):
        """
        turns: list of strings representing dialogue turns.
        return: ConceptGraph representation of the text's surface form.
                For example, a graph of the dependency parse of the last turn.
        """
        pass

    def translate(self, turns):
        egraph = self.text_to_graph(turns, self.knowledge_base)
        self._expression_pull(egraph, self.knowledge_base)
        self._unknown_expression_pull(egraph)
        rule_assignments = self._inference(egraph)
        mentions = self._get_mentions(rule_assignments)
        merges = self._get_merges(rule_assignments)
        if DEBUG:
            self.display_mentions(mentions, egraph)
            self.display_merges(merges, egraph)
        return mentions, merges

    def _expression_pull(self, egraph, kgraph):
        """
        Pull expressions from KB into the expression graph.
        """
        egraph.pull(nodes=['"%s"'%span_obj.string for span_node, span_obj in egraph.spans.items()],
                    kb=kgraph, max_depth=1)

    def _unknown_expression_pull(self, egraph):
        """
        Create "UNK" expression nodes for all nodes with no expr references.
        """
        for span_node, span_object in egraph.spans.items():
            expression = '"%s"' % span_object.string
            references = egraph.object_neighbors(expression, 'expr')
            if len(references) == 0:
                unk_node = egraph.add_node(egraph._get_next_id())
                egraph.add_bipredicate(unk_node, 'unknown', 'type')
                egraph.add_bipredicate(expression, unk_node, 'expr')

    def _reference_expansion(self, pregraph):
        """
        Expand vars in precondition to include expression and reference links.
        """
        for concept in pregraph.concepts():
            if pregraph.type(concept) is None and len(pregraph.monopredicate(concept, 'var')) > 0:
                # found variable entity instance
                found_supertype = False
                for supertype in pregraph.object_neighbors(concept, 'ltype'):
                    found_supertype = True
                    self._expand_references(pregraph, concept, supertype)
                if not found_supertype:
                    self._expand_references(pregraph, concept)

    def _expand_references(self, template_graph, concept, supertype=None):
        expression_var = template_graph._get_next_id()
        exprof = template_graph.add_bipredicate(concept, expression_var, 'exprof')
        concept_var = template_graph._get_next_id()
        expr = template_graph.add_bipredicate(expression_var, concept_var, 'expr')
        new_nodes = [expression_var, exprof, concept_var, expr]
        if supertype is not None:
            concept_type = template_graph.add_bipredicate(concept_var, supertype, 'type')
            template_graph.remove_bipredicate(concept, supertype, 'ltype')
            new_nodes.append(concept_type)
        for n in new_nodes:
            template_graph.add_monopredicate(n, 'var')

    def _inference(self, egraph):
        """
        Apply the specified rules to the current egraph and get the variable assignments of the solutions
        """
        rule_assignments = {}
        for rule in self.rules:
            matches = egraph.infer(rule.precondition)
            var_assignments = self._get_variable_assignments(matches)
            rule_assignments[rule] = var_assignments
        return rule_assignments

    def _get_variable_assignments(self, var_matches):
        var_map, matches = var_matches
        solutions = []
        for match in matches:
            variable_assignments = {}
            for key, value in var_map.items():
                variable_assignments[key] = match[value]
            solutions.append(variable_assignments)
        return solutions

    def _get_mentions(self, assignments):
        """
        Produce dict<mention span: mention graph>.

        assignments: dict<rule: list<assignments>>
        """
        mentions = defaultdict(list)
        for rule, solutions in assignments.items():
            pre, post = rule.precondition, rule.postcondition
            ((sig, center_pred),) = post.predicate_instances('center')
            center_var = post.subject(center_pred)
            for solution in solutions:
                (expression_var,) = pre.object_neighbors(center_var, 'exprof')
                (concept_var,) = pre.object_neighbors(expression_var, 'expr')
                center = solution[center_var]
                m = {}
                cg = ConceptGraph()
                cg.next_id = post.next_id
                for node in post.concepts():
                    if node in solution:
                        if node in [center_var,expression_var,concept_var]:
                            m[node] = solution[node]
                        else:
                            m[node] = cg._get_next_id()
                    else:
                        m[node] = node
                for (subject, object, typ), inst in post.bipredicate_instances():
                    cg.add_bipredicate(m[subject], m[object], m[typ], m[inst])
                for (subject, typ), inst in post.monopredicate_instances():
                    cg.add_monopredicate(m[subject], m[typ], m[inst])
                mentions[center].append(cg)
        return mentions

    def _get_merges(self, assignments):
        """
        Produce scored pairs of (mention span, path).

        assignments: dict<rule: list<assignments>>
        """
        merges = defaultdict(list)
        for rule, solutions in assignments.items():
            pre, post = rule.precondition, rule.postcondition
            ((sig, focus_pred),) = post.predicate_instances('focus')
            ((sig, center_pred),) = post.predicate_instances('center')
            focus = post.subject(focus_pred)
            center = post.subject(center_pred)
            for solution in solutions:
                focus = solution.get(focus, focus)
                center = solution.get(center, center)
                if post.type(focus) is not None:
                    # focus is a predicate instance, need to consider its subj/obj/type
                    if post.subject(focus) in solution and solution[post.subject(focus)] != center:
                        pair = ((center,'subject'),
                                (solution[post.subject(focus)],'self'))
                        merges[rule].append(pair)
                    if post.object(focus) in solution and solution[post.object(focus)] != center:
                        pair = ((center, 'object'),
                                (solution[post.object(focus)], 'self'))
                        merges[rule].append(pair)
                    if post.type(focus) in solution and solution[post.type(focus)] != center:
                        pair = ((center, 'type'),
                                (solution[post.type(focus)], 'self'))
                        merges[rule].append(pair)
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

    def display_mentions(self, mentions, egraph):
        """
        Display the mentions with their concepts instead of spans
        """
        print()
        for span, mention_graphs in mentions.items():
            print('%s MENTIONS:: '%self._get_expression_of_span(span, egraph))
            for graph in mention_graphs:
                for (s,o,t), inst in graph.bipredicate_instances():
                    subj = self._get_concept_of_span(s,egraph)
                    obj = self._get_concept_of_span(o, egraph)
                    typ = self._get_concept_of_span(t, egraph)
                    print('\t[%d]\t-> %s(%s,%s)'%(inst,typ,subj,obj))
                for (s,t), inst in graph.monopredicate_instances():
                    if t != 'var':
                        subj = self._get_concept_of_span(s,egraph)
                        typ = self._get_concept_of_span(t, egraph)
                        print('\t[%d]\t-> %s(%s)'%(inst,typ,subj))
            print()

    def _get_concept_of_span(self, span, egraph):
        expression = self._get_expression_of_span(span, egraph)
        if expression is not None:
            (concept_var,) = egraph.object_neighbors(expression, 'expr')
            if len(egraph.bipredicate(concept_var,'unknown','type')) > 0:
                return '_unk_'
            return concept_var
        return span

    def _get_expression_of_span(self, span, egraph):
        expressions = egraph.object_neighbors(span, 'exprof')
        if len(expressions) == 1:
            return expressions.pop()
        return None

    def display_merges(self, merges, egraph):
        """
        Display the merges with their concepts instead of spans
        """
        print()
        print("MERGES:: ")
        for rule, merge_pairs in merges.items():
            for (span1, pos1), (span2, pos2) in merge_pairs:
                concept1 = self._get_concept_of_span(span1, egraph)
                concept2 = self._get_concept_of_span(span2, egraph)
                print("\t(%s,%s)\t<=> (%s,%s)"%(concept1,pos1,concept2,pos2))
        test = 1


