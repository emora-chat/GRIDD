from modules.parsing_model import ParsingModel, Span

from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base import KnowledgeBase
import data_structures.knowledge_base as knowledge_base_file
from data_structures.working_memory import WorkingMemory

import os
from os.path import join

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL","ERROR"))

# https://emorynlp.github.io/ddr/doc/pages/overview.html

PAST_VB = ['vbd', 'vbn']
PRES_VB = ['vbp', 'vbg', 'vbz']
ADJ = ['jj', 'jjr', 'jjs']
NOUN = ['nn', 'nns', 'nnp', 'nnps']
PRONOUN = ['prp', 'prpds']
ADV = ['rb', 'rbr', 'rbs']
NODES = ['focus', 'center', 'pos', 'exprof', 'type', 'ltype']

class ElitDPToLogic(ParsingModel):

    def text_to_graph(self, turns):
        """
        Given the ELIT Dependency Parse attachment list, transform it into a concept graph
        :return dependency parse cg
        """
        parse_dict = self.model.parse([turns[-1]], models=['tok', 'pos', 'ner', 'srl', 'dep'])
        cg = ConceptGraph(concepts=list(knowledge_base_file.BASE_NODES) + NODES)
        ewm = WorkingMemory(self.knowledge_base)
        ewm.concatenate(cg)
        for n in ['past_tense', 'present_tense']:
            ewm.add(n, 'type', 'verb')
        for n in ['verb', 'noun', 'adj', 'pron', 'adv']:
            ewm.add(n, 'type', 'pos')
        ewm.add('pron', 'type', 'noun')
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
        self.convert(parse_dict["dep"][0], parse_dict["tok"][0], parse_dict["pos"][0], ewm)
        return ewm

    # todo - verify that POS tags and DP labels are disjoint
    def convert(self, dependencies, tokens, pos_tags, cg):
        """
        Add dependency parse links into the expression concept graph
        :param dependencies: list of dependency relations
        :param tokens: list of tokens
        :param pos_tags: list of part of speech tags
        :param cg: the concept graph being created
        """
        print(tokens)
        print(pos_tags)
        print(dependencies)
        print()
        token_to_span_node = {}
        for token_idx in range(len(tokens)):
            expression = tokens[token_idx]
            pos = pos_tags[token_idx].lower().replace('$','ds')
            if not cg.has(pos):
                cg.add(pos, 'type', 'pos')
            span_node = cg.add(cg._get_next_id())
            self.span_map[cg][span_node] = Span(expression, token_idx, token_idx+1)
            token_to_span_node[token_idx] = span_node
            expression = '"%s"' % expression
            cg.add(span_node, 'exprof', expression)
            cg.add(span_node, 'type', pos)

        for token_idx, (head_idx, label) in enumerate(dependencies):
            if head_idx != -1:
                source = token_to_span_node[head_idx]
                target = token_to_span_node[token_idx]
                cg.add(source, label, target)


if __name__ == '__main__':
    kb = KnowledgeBase(join('data_structures', 'kg_files', 'framework_test.kg'))
    from elit.client import Client
    elit_model = Client('http://0.0.0.0:8000')
    template_starter_predicates = [(n, 'is_type') for n in NODES]
    template_file = join('data_structures', 'kg_files', 'elit_dp_templates.kg')
    ttl = ElitDPToLogic("elit dp", kb, elit_model, template_starter_predicates, template_file)

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