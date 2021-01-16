from subframeworks.text_to_logic_model import TextToLogicModel

from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base import KnowledgeBase
import data_structures.knowledge_base as knowledge_base_file
from data_structures.working_memory import WorkingMemory

import os
from os.path import join

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL","ERROR"))

# https://emorynlp.github.io/ddr/doc/pages/overview.html

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



class ElitDPToLogic(TextToLogicModel):

    def text_to_graph(self, turns):
        """
        Given the ELIT Dependency Parse attachment list, transform it into a concept graph
        :return dependency parse cg
        """
        parse_dict = self.model.parse([turns[-1]], models=['tok', 'ner', 'srl', 'dep'])
        cg = ConceptGraph(concepts=list(knowledge_base_file.BASE_NODES) + NODES)
        ewm = WorkingMemory(self.knowledge_base)
        ewm.concatenate(cg)
        self.convert(parse_dict["dep"][0], parse_dict["tok"][0], ewm)
        return ewm

    def convert(self, dependencies, tokens, cg):
        """
        Add dependency parse links into the concept graph being generated
        :param dependencies: list of dependency relations
        :param tokens: list of tokens
        :param cg: the concept graph being created
        """
        pass



if __name__ == '__main__':
    kb = KnowledgeBase(join('data_structures', 'kg_files', 'framework_test.kg'))

    asr_hypotheses = [
        {'text': 'i bought a house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80}
         }
    ]
    turns = [hypo['text'] for hypo in asr_hypotheses]
    print('TURNS: %s \n'%turns)

    from elit.client import Client
    elit_model = Client('http://0.0.0.0:8000')
    template_starter_predicates = [(n, 'is_type') for n in POS_NODES + NODES]
    template_file = join('data_structures', 'kg_files', 'elit_dp_templates.kg')
    ttl = ElitDPToLogic("elit dp", kb, elit_model, template_starter_predicates, template_file)
    mentions,merges = ttl.translate(turns)
    test = 1