
from GRIDD.possible_tasks.trie import SpanMatcher
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.span import Span

class ExpressionMatcher:

    def __init__(self, expressions):
        self.st = SpanMatcher(expressions)

    def match(self, input, remove_subset=False, remove_overlaps=False):
        """
        input:      string to check for expressions
        returns:    matched, overlaps, contains

            matched: dictionary where keys are (start, end) int tuples and
                     values are str representing matched expression
            overlaps: dictionary where keys are (start, end) int tuples and
                      values are sets of (start, end) tuples representing
                      all matches that conflict/overlap with their key
            contains: dictionary where keys are (start, end) int tuples and
                      values are (start, end) tuples representing all matches
                      that are completely contained within their key.
        """

        if isinstance(input, str):
            tokens = input.lower().split()
        else:
            tokens = input

        results = self.st.findall(tokens,remove_subset=False, remove_overlap=False)

        matched, overlaps, contains = {}, {}, {}
        for i in results:
            matched[(i[1],i[2])] = i[0]
        for i in matched.keys():
            overlaps[i] = set()
            contains[i] = set()
            for j in matched.keys():
                if j == i:
                    continue
                if (j[0] <= i[0] and j[1] >= i[0]):
                    overlaps[i].add(j)
                if (j[0] <= i[1] and j[1] >= i[1]):
                    overlaps[i].add(j)
                    #continue
                if (j[0] >= i[0] and j[1] <= i[1]):
                    overlaps[i].add(j)
                    contains[i].add(j)
            if (len(overlaps[i]) is 0):
                overlaps.pop(i)
            if (len(contains[i]) is 0):
                contains.pop(i)
        return matched, overlaps, contains

class MultiwordExpressionMatcher:

    def __init__(self, knowledge_base):
        self.multiword_expressions = {s.replace('"','').lower(): o
                                      for s, _, o, _ in knowledge_base.predicates(predicate_type='expr')
                                      if len(s.split()) > 1 or "'" in s}
        self.matcher = ExpressionMatcher(self.multiword_expressions.keys())
        # print(self.multiword_expressions.keys())

    def __call__(self, elit_results):
        """
        :param elit_results - dictionary of outputs from ELIT models
        """
        tokens = elit_results["tok"]
        mentions = {}
        if len(tokens) > 0:
            surface_form_tokens = [span.string for span in tokens]
            lemma_tokens = [span.expression for span in tokens]
            # todo - ELIT tokens are split on punctuation (e.g. Sally's becomes Sally 's) but expression creation doesn't follow this
            # todo - check hwo punctuation is handled in system so far (is it preserved, does alexa asr reliably add punctuation, etc.)
            matched, overlaps, contains = self.matcher.match(surface_form_tokens, remove_subset=True)
            if surface_form_tokens != lemma_tokens:
                lmatched, loverlaps, lcontains = self.matcher.match(lemma_tokens, remove_subset=True)
                for k,v in lmatched.items():
                    if k not in matched: matched[k] = v
                for k,v in loverlaps.items():
                    if k not in overlaps: overlaps[k] = v
                for k, v in lcontains.items():
                    if k not in contains: contains[k] = v
            # manually remove subsets between surface form and lemma results
            keys = list(matched.keys())
            for i in range(len(keys)):
                for j in range(len(keys)):
                    if i > j:
                        k1 = keys[i]
                        k2 = keys[j]
                        if k1[0] >= k2[0] and k1[1] <= k2[1]:
                            # k1 is contained in k2
                            del matched[k1]
                            if k1 in overlaps: del overlaps[k1]
                            if k1 in contains: del contains[k1]
                        elif k2[0] >= k1[0] and k2[1] <= k1[1]:
                            # k2 is contained in k1
                            del matched[k2]
                            if k2 in overlaps: del overlaps[k2]
                            if k2 in contains: del contains[k2]
            for (sidx, eidx), string in matched.items():
                longest = True
                if (sidx, eidx) in overlaps:
                    for overlap in overlaps[(sidx, eidx)]:
                        if eidx - sidx < overlap[1] - overlap[0]:
                            longest = False
                            break
                if longest:
                    # todo - determine pos_tag of multiword span
                    # todo - if plural, add `group` type
                    span = Span(string, sidx, eidx, tokens[0].sentence, tokens[0].turn, tokens[0].speaker, string, None)
                    cg = ConceptGraph(namespace='multi_')
                    concept = self.multiword_expressions[string]
                    cg.add(concept, 'focus')
                    cg.add(concept, 'center')
                    cg.add(span)
                    cg.features[span.to_string()]["span_data"] = span
                    mentions[span.to_string()] = cg
        return mentions
