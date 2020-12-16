from subframeworks.text_to_logic_model import TextToLogicModel

from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_graph import KnowledgeGraph
import knowledge_base.knowledge_graph as kg
from knowledge_base.working_memory import WorkingMemory

from structpy.map.bijective.bimap import Bimap
from allennlp.predictors.predictor import Predictor
from os.path import join

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

    def text_to_graph(self, turns, knowledge_base):
        """
        Given the AllenAI Dependency Parse hierplane dict, transform it into a concept graph
        :return dependency parse cg
        """
        parse_dict = self.model.predict(turns[-1])
        cg = ConceptGraph(nodes=list(kg.BASE_NODES) + NODES)
        cg.spans = Bimap()
        self.add_node_from_dict('root', parse_dict['hierplane_tree']['root'], cg)
        return cg

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
            cg.add_node(pos)
            cg.add_monopredicate(pos, 'is_type')
            cg.add_bipredicate(pos, 'pos', 'type')

        span_node = cg.add_node(cg._get_next_id())
        spans = node_dict['spans']
        if len(spans) > 1:
            print('WARNING! dp element %s has more than one span' % expression)
            print(spans)
        charspan = CharSpan(expression,spans[0]['start'],spans[0]['end'])
        cg.spans[span_node] = charspan

        expression = '"%s"' % expression
        if not cg.has(expression):
            cg.add_node(expression)
        cg.add_bipredicate(span_node, expression, 'exprof') # todo - (QOL) automate the expression links
        cg.add_bipredicate(span_node, pos, 'type')

        if parent != 'root':
            link = node_dict['link']
            if link == 'det':
                link = 'detpred'
            if not cg.has(link):
                cg.add_node(link)
            cg.add_bipredicate(parent, span_node, link)

        if 'children' in node_dict:
            for child in node_dict['children']:
                self.add_node_from_dict(span_node, child, cg)


if __name__ == '__main__':
    kb = KnowledgeGraph(join('knowledge_base', 'kg_files', 'framework_test.kg'))
    wm = ConceptGraph(nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)

    asr_hypotheses = [
        {'text': 'i bought a red house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'red', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80, 4: 0.80}
         }
    ]
    turns = [hypo['text'] for hypo in asr_hypotheses]

    template_base = KnowledgeGraph(nodes=POS_NODES + NODES, loading_kb=False)
    for n in POS_NODES + NODES:
        template_base._concept_graph.add_monopredicate(n, 'is_type')

    dependency_parser = Predictor.from_path(
        "https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
    template_file = join('knowledge_base', 'kg_files', 'allen_dp_templates.txt')
    output = AllenAIToLogic(kb, dependency_parser, template_base, template_file).translate(turns)