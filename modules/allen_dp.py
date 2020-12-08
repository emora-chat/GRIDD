from allennlp.predictors.predictor import Predictor
from modules.module import Module
from knowledge_base.concept_graph import ConceptGraph

class AllenDP(Module):

    def __init__(self, name):
        super().__init__(name)
        self.dependency_parser = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
        self.dup_id = 1

    def add_node_from_dict(self, parent, node_dict, cg):
        if len(node_dict['attributes']) > 1:
            print('WARNING! dp element %s has more than one attribute'%node_dict['word'])
            print(node_dict['attributes'])
        word, pos = node_dict['word'], node_dict['attributes'][0].lower()
        if cg.has(word):
            word = word+'_%d'%self.dup_id
            self.dup_id += 1
        cg.add_node(word)

        if not cg.has(pos):
            cg.add_node(pos)
            cg.add_monopredicate(pos, 'is_type')
        cg.add_bipredicate(word, pos, 'type')

        spans = node_dict['spans']
        span_node = '%d,%d'%(spans[0]['start'],spans[0]['end'])
        cg.add_node(span_node)
        cg.add_bipredicate(word, span_node, 'span')

        if parent != 'root':
            if not cg.has(node_dict['link']):
                cg.add_node(node_dict['link'])
            cg.add_bipredicate(parent, word, node_dict['link'])

        if 'children' in node_dict:
            for child in node_dict['children']:
                self.add_node_from_dict(word, child, cg)

    def parse_to_cg(self, parse_dict):
        cg = ConceptGraph(nodes=['type', 'is_type', 'span'])
        self.add_node_from_dict('root', parse_dict['hierplane_tree']['root'], cg)
        return cg

    def run(self, input, graph):
        """
        Get dependency parse of input

        :param input: ASR hypotheses (same format as mention identification input)
        :param graph: DSG from last turn
        :return: dict<token span: concept graph>
        """
        dp_parse = {}

        for hypothesis in input:
            parse = self.dependency_parser.predict(
                sentence=hypothesis['text']
            )
            cg = self.parse_to_cg(parse)

        return dp_parse

if __name__ == '__main__':
    merge = AllenDP('dp merge')
    sentence = "I love math"
    output = merge.run(sentence, {})