
from GRIDD.modules.text_to_logic_model import ParseToLogic
from GRIDD.data_structures.concept_graph import ConceptGraph
import GRIDD.data_structures.knowledge_base as knowledge_base_file
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.modules.elit_dp_to_logic_spec import ElitDPSpec

import os
from os.path import join

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL","ERROR"))

# https://emorynlp.github.io/ddr/doc/pages/overview.html

PAST_VB = ['vbd', 'vbn']
PRES_VB = ['vbp', 'vbz', 'vbg', 'vb']
ADJ = ['jj', 'jjr', 'jjs']
NOUN = ['nn', 'nns', 'nnp', 'nnps']
PRONOUN = ['prp', 'prpds']
ADV = ['rb', 'rbr', 'rbs']
REF_DET = ['the', 'those', 'these', 'that', 'this']
INST_DET = ['a', 'an']
QUEST = ['wdt', 'wp', 'wpds', 'wrb']
INTERJ = ['uh']
ALLOW_SINGLE = ['dt', 'ex', 'adj', 'noun', 'pron', 'adv', 'interj', 'verb', 'question_word']

NODES = ['focus', 'center', 'pstg', 'ref', 'type', 'ltype']

POS_MAP = {'in': 'prepo',
           'to': 'pos_to',
           'uh': 'intrj'}

PRECEDE_LABELS = ['aux', 'modal', 'obj', 'cop']

# DP_LABELS = [x.strip()
#              for x in open(join('GRIDD', 'resources', 'elit_dp_labels.txt'), 'r').readlines()
#              if len(x.strip()) > 0]

class ElitDPToLogic(ParseToLogic):

    def text_to_graph(self, *args):
        """
        Transform the ELIT Dependency Parse attachment list into a concept graph,
        supported with the token and pos namespace lists
        args[0,1,2] - tok, pos, dp
        :return dependency parse cg
        """
        cg = ConceptGraph(concepts=list(knowledge_base_file.BASE_NODES) + NODES)
        ewm = WorkingMemory(self.knowledge_base)
        ewm.concatenate(cg)

        for n in ['verb', 'noun', 'adj', 'pron', 'adv', 'question_word', 'interj']:
            ewm.add(n, 'type', 'pstg')

        ewm.add('prp', 'type', 'noun')
        for n in ['past_tense', 'present_tense']:
            ewm.add(POS_MAP.get(n, n), 'type', 'verb')
        for n in PAST_VB:
            ewm.add(POS_MAP.get(n, n), 'type', 'past_tense')
        for n in PRES_VB:
            ewm.add(POS_MAP.get(n, n), 'type', 'present_tense')
        for n in ADJ:
            ewm.add(POS_MAP.get(n, n), 'type', 'adj')
        for n in NOUN:
            ewm.add(POS_MAP.get(n, n), 'type', 'noun')
        for n in PRONOUN:
            ewm.add(POS_MAP.get(n, n), 'type', 'pron')
        for n in ADV:
            ewm.add(POS_MAP.get(n, n), 'type', 'adv')
        for n in QUEST:
            ewm.add(POS_MAP.get(n, n), 'type', 'question_word')
        for n in INTERJ:
            ewm.add(POS_MAP.get(n, n), 'type', 'interj')
        for n in ALLOW_SINGLE:
            ewm.add(POS_MAP.get(n, n), 'type', 'allow_single')
        self.convert(*args, ewm)
        return ewm

    # todo - verify that POS tags and DP labels are disjoint
    def convert(self, tokens, pos_tags, dependencies, cg):
        """
        Add dependency parse links into the expression concept graph
        :param dependencies: list of dependency relations
        :param tokens: list of spans
        :param pos_tags: list of part of speech tags
        :param cg: the concept graph being created
        """
        precede_token_idx = [idx for idx, (head_idx, label) in enumerate(dependencies)
                             if label.lower() in PRECEDE_LABELS or pos_tags[idx].lower().replace('$','ds') in QUEST]
        for token_idx in range(len(tokens)):
            span = tokens[token_idx]
            expression = span.string
            pos = pos_tags[token_idx].lower().replace('$','ds')
            pos = POS_MAP.get(pos, pos)
            if 'pstg' not in cg.supertypes(pos): # todo - optimization by dynamic programming
                cg.add(pos, 'type', 'pstg')
            span_node = span.to_string()
            cg.features[span_node]["span_data"] = span
            cg.add(span_node)
            self.spans.append(span_node)
            expression = '"%s"' % expression
            cg.add(span_node, 'ref', expression)
            cg.add(span_node, 'type', pos)
            if token_idx > 0:
                for pti in precede_token_idx:
                    if pti < token_idx:
                        cg.add(tokens[pti].to_string(), 'precede', span_node)

        for token_idx, (head_idx, label) in enumerate(dependencies):
            if head_idx != -1:
                source = tokens[head_idx]
                target = tokens[token_idx]
                if label == 'com': # condense compound relations into single entity
                    original_source = source.to_string()
                    original_target = target.to_string()

                    for tuple in cg.predicates(original_target, 'ref') + cg.predicates(original_source, 'ref'):
                        cg.remove(tuple[2]) # remove non-condensed expressions
                    cg.remove(original_target)
                    self.spans.remove(original_target)
                    original_source_span_idx = self.spans.index(original_source)
                    del cg.features[original_source]
                    del cg.features[original_target]

                    source.string = target.string + ' ' + source.string
                    source.start = target.start
                    new_source = source.to_string()
                    cg.features[new_source]["span_data"] = source
                    self.spans[original_source_span_idx] = new_source
                    cg.add(new_source, 'ref', '"%s"'%source.string) # add updated condensed expression
                    cg.merge(new_source, original_source)
                else:
                    cg.add(source.to_string(), label, target.to_string())


if __name__ == '__main__':
    print(ElitDPSpec.verify(ElitDPToLogic))