from subframeworks.text_to_logic_model import TextToLogicModel

from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base import KnowledgeBase
import data_structures.knowledge_base as knowledge_base_file
from data_structures.working_memory import WorkingMemory

from allennlp.predictors.predictor import Predictor
import os
from os.path import join

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL","ERROR"))

POS_NODES = ['verb', 'noun', 'pron', 'det', 'adj', 'adv']
NODES = ['nsubj', 'dobj', 'amod', 'detpred', 'focus', 'center', 'pos', 'exprof', 'ltype']

class CharSpan:

    def __init__(self, string, start, end):
        self.string = string
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%d,%d)'%(self.string, self.start, self.end)

class AllenAIToLogic(TextToLogicModel):

    def text_to_graph(self, turns):
        """
        Given the AllenAI Dependency Parse hierplane dict, transform it into a concept graph
        :return dependency parse cg
        """
        parse_dict = self.model.predict(turns[-1])
        cg = ConceptGraph(concepts=list(knowledge_base_file.BASE_NODES) + NODES)
        ewm = WorkingMemory(self.knowledge_base)
        ewm.concatenate(cg)
        self.add_node_from_dict('root', parse_dict['hierplane_tree']['root'], ewm)
        return ewm

    def add_node_from_dict(self, parent, node_dict, cg):
        """
        Recurvisely add dependency parse links into the concept graph being generated
        :param parent: the parent node of the current focal word
        :param node_dict: the subtree dictionary of the dependency parse corresponding to the focal word
        :param cg: the concept graph being created
        """
        if len(node_dict['attributes']) > 1:
            print('WARNING! dp element %s has more than one attribute'%node_dict['word'])
            print(node_dict['attributes'])

        expression, pos = node_dict['word'], node_dict['attributes'][0].lower()
        if not cg.has(pos):
            cg.add(pos)
            cg.add(pos, 'is_type')
            cg.add(pos, 'type', 'pos')

        span_node = cg.add(cg._get_next_id())
        spans = node_dict['spans']
        if len(spans) > 1:
            print('WARNING! dp element %s has more than one span' % expression)
            print(spans)
        charspan = CharSpan(expression,spans[0]['start'],spans[0]['end'])
        self.span_map[cg][span_node] = charspan

        expression = '"%s"' % expression
        if not cg.has(expression):
            cg.add(expression)
        cg.add(span_node, 'exprof', expression) # todo - (QOL) automate the expression links
        cg.add(span_node, 'type', pos)

        if parent != 'root':
            link = node_dict['link']
            if link == 'det':
                link = 'detpred'
            if not cg.has(link):
                cg.add(link)
            cg.add(parent, link, span_node)

        if 'children' in node_dict:
            for child in node_dict['children']:
                self.add_node_from_dict(span_node, child, cg)


if __name__ == '__main__':
    kb = KnowledgeBase(join('data_structures', 'kg_files', 'framework_test.kg'))

    asr_hypotheses = [
        {'text': 'i bought a red house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'red', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80, 4: 0.80}
         }
    ]
    turns = [hypo['text'] for hypo in asr_hypotheses]
    print('TURNS: %s \n'%turns)

    dependency_parser = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
    template_starter_predicates = [(n, 'is_type') for n in POS_NODES + NODES]
    template_file = join('data_structures', 'kg_files', 'allen_dp_templates.kg')
    ttl = AllenAIToLogic("allen dp", kb, dependency_parser, template_starter_predicates, template_file)
    mentions,merges = ttl.translate(turns)
    test = 1