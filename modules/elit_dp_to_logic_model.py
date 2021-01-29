
from GRIDD.modules.text_to_logic_model import ParseToLogic
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_base import KnowledgeBase
import GRIDD.data_structures.knowledge_base as knowledge_base_file
from GRIDD.data_structures.working_memory import WorkingMemory

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

NODES = ['focus', 'center', 'pos', 'ref', 'type', 'ltype']
DP_LABELS = [x.strip()
             for x in open(join('GRIDD', 'resources', 'elit_dp_labels.txt'), 'r').readlines()
             if len(x.strip()) > 0]


class ElitDPToLogic(ParseToLogic):

    def text_to_graph(self, *args):
        """
        Transform the ELIT Dependency Parse attachment list into a concept graph,
        supported with the token and pos tag lists
        args[0,1,2] - tok, pos, dp
        :return dependency parse cg
        """
        cg = ConceptGraph(concepts=list(knowledge_base_file.BASE_NODES) + NODES)
        ewm = WorkingMemory(self.knowledge_base)
        ewm.concatenate(cg)

        for n in ['verb', 'noun', 'adj', 'pron', 'adv', 'question_word', 'interj']:
            ewm.add(n, 'type', 'pos')

        ewm.add('prp', 'type', 'noun')
        for n in ['past_tense', 'present_tense']:
            ewm.add(n, 'type', 'verb')
        for n in PAST_VB:
            ewm.add(n, 'type', 'past_tense')
        for n in PRES_VB:
            ewm.add(n, 'type', 'present_tense')
        for n in ADJ:
            ewm.add(n, 'type', 'adj')
        for n in NOUN:
            ewm.add(n, 'type', 'noun')
        for n in PRONOUN:
            ewm.add(n, 'type', 'pron')
        for n in ADV:
            ewm.add(n, 'type', 'adv')
        for n in QUEST:
            ewm.add(n, 'type', 'question_word')
        for n in INTERJ:
            ewm.add(n, 'type', 'interj')
        self.convert(*args, ewm)
        return ewm

    # todo - verify that POS tags and DP labels are disjoint
    def convert(self, tokens, pos_tags, dependencies, cg):
        """
        Add dependency parse links into the expression concept graph
        :param dependencies: list of dependency relations
        :param tokens: list of tokens
        :param pos_tags: list of part of speech tags
        :param cg: the concept graph being created
        """
        token_to_span_node = {}
        for token_idx in range(len(tokens)):
            expression = tokens[token_idx]
            pos = pos_tags[token_idx].lower().replace('$','ds')
            if not cg.has(pos):
                cg.add(pos, 'type', 'pos')
            span_node = Span(expression, token_idx, token_idx+1) #todo - add sentence id
            self.spans.append(span_node)
            cg.add(span_node)
            token_to_span_node[token_idx] = span_node
            expression = '"%s"' % expression
            cg.add(span_node, 'ref', expression)
            cg.add(span_node, 'type', pos)

        for token_idx, (head_idx, label) in enumerate(dependencies):
            if head_idx != -1:
                source = token_to_span_node[head_idx]
                target = token_to_span_node[token_idx]
                cg.add(source, label, target)


if __name__ == '__main__':
    kb = KnowledgeBase(join('data_structures', 'kg_files', 'framework_test.kg'))
    template_starter_predicates = [(n, 'is_type') for n in NODES]
    template_file = join('data_structures', 'kg_files', 'elit_dp_templates.kg')
    ttl = ElitDPToLogic("elit dp", kb, template_starter_predicates, template_file)

    sentence = input('Sentence: ')
    while sentence != 'q':
        mentions,merges = ttl.translate([sentence])
        for mention, cg in mentions.items():
            print('#'*30)
            print(mention)
            print('#' * 30)
            print(cg.pretty_print())
        print()
        for merge in merges:
            print(merge)
        print()
        sentence = input('Sentence: ')
    test = 1