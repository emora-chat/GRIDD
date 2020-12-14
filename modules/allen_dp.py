from allennlp.predictors.predictor import Predictor
from modules.module import Module
from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_graph import KnowledgeGraph
import knowledge_base.knowledge_graph as kg
from knowledge_base.working_memory import WorkingMemory
from structpy.map.bijective.bimap import Bimap
from os.path import join
from copy import deepcopy

class CharSpan:

    def __init__(self, token, start, end):
        self.token = token
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%d,%d)'%(self.token, self.start, self.end)

class AllenDP(Module):

    def __init__(self, name):
        super().__init__(name)
        self.dependency_parser = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
        # POS tag and dependency parse link CANNOT be the same (causes Prolog solution-finding problems)
        # see det vs detpred for example
        self.pos_nodes = ['verb','noun','pron','det','adj','adv']
        self.nodes = ['nsubj','dobj','amod','detpred','focus','center','pos']
        self.templates = KnowledgeGraph(nodes=self.pos_nodes + self.nodes)
        for n in self.pos_nodes + self.nodes:
            self.templates._concept_graph.add_monopredicate(n, 'is_type')
        self.templates.add_knowledge(join('knowledge_base', 'kg_files', 'allen_dp_templates.txt'))
        self.template_graphs, self.transformation_graphs = self.templates._concept_graph.generate_inference_graph()
        self.dup_id = 1

    def parse_to_cg(self, parse_dict):
        cg = ConceptGraph(nodes=list(kg.BASE_NODES)+self.nodes+self.pos_nodes)
        cg.spans = Bimap()
        for n in self.pos_nodes:
            cg.add_bipredicate(n, 'pos', 'type')
        self.add_node_from_dict('root', parse_dict['hierplane_tree']['root'], cg)
        return cg

    def add_node_from_dict(self, parent, node_dict, cg):
        if len(node_dict['attributes']) > 1:
            print('WARNING! dp element %s has more than one attribute'%node_dict['word'])
            print(node_dict['attributes'])
        word, pos = node_dict['word'], node_dict['attributes'][0].lower()
        word = '"%s"'%word
        if not cg.has(word): # todo - what if there is more than one mention of the same word
            cg.add_node(word)

        if not cg.has(pos):
            cg.add_node(pos)
            cg.add_monopredicate(pos, 'is_type')
        cg.add_bipredicate(word, pos, 'type')

        spans = node_dict['spans']
        if len(spans) > 1:
            print('WARNING! dp element %s has more than one span'%word)
            print(spans)
        charspan = CharSpan(word,spans[0]['start'],spans[0]['end'])
        cg.spans[word] = charspan

        if parent != 'root':
            link = node_dict['link']
            if link == 'det':
                link = 'detpred'
            if not cg.has(link):
                cg.add_node(link)
            cg.add_bipredicate(parent, word, link)

        if 'children' in node_dict:
            for child in node_dict['children']:
                self.add_node_from_dict(word, child, cg)

    def get_implication_maps(self, inference_match, implication, spans_map):
        var_map, match = inference_match
        implication_map = {}
        for solution in match:
            imp_cg = ConceptGraph()
            pred_map = {}
            for (s,o,l), pred_id in implication.bipredicate_instances():
                if s in var_map and 'PyswipVariable' not in solution[var_map[s]]:
                    s = solution[var_map[s]]
                s = self._local_get(pred_map, s, imp_cg)
                if o in var_map and 'PyswipVariable' not in solution[var_map[o]]:
                    o = solution[var_map[o]]
                o = self._local_get(pred_map, o, imp_cg)
                if l in var_map and 'PyswipVariable' not in solution[var_map[l]]:
                    l = solution[var_map[l]]
                l = self._local_get(pred_map, l)
                for item in [s, o, l]:
                    if not imp_cg.has(item):
                        imp_cg.add_node(item)
                if pred_id not in pred_map:
                    new_pred_id = imp_cg.add_bipredicate(s, o, l, merging=True)
                    pred_map[pred_id] = new_pred_id
                else:
                    new_pred_id = imp_cg.add_bipredicate(s, o, l,
                                                         predicate_id=pred_map[pred_id],
                                                         merging=True)
            for (s,l), pred_id in implication.monopredicate_instances():
                if s in var_map and 'PyswipVariable' not in solution[var_map[s]]:
                    s = solution[var_map[s]]
                s = self._local_get(pred_map, s, imp_cg)
                if l in var_map and 'PyswipVariable' not in solution[var_map[l]]:
                    l = solution[var_map[l]]
                l = self._local_get(pred_map, l)
                for item in [s, l]:
                    if not imp_cg.has(item):
                        imp_cg.add_node(item)
                if pred_id not in pred_map:
                    new_pred_id = imp_cg.add_monopredicate(s, l, merging=True)
                    pred_map[pred_id] = new_pred_id
                else:
                    new_pred_id = imp_cg.add_monopredicate(s, l,
                                                         predicate_id=pred_map[pred_id],
                                                         merging=True)
                if l == 'focus':
                    focus = s

            expr_nodes = list(imp_cg.subject_neighbors(focus, 'expr'))
            assert len(expr_nodes) == 1
            expr_node = expr_nodes[0]
            span = spans_map[expr_node]
            implication_map[span] = imp_cg

        return implication_map

    def _local_get(self, dict, item, imp_cg=None):
        to_return = dict.get(item, None)
        if to_return is None:
            if isinstance(item, int):
                # New instance from implication is acting as subject or object, need to convert and store to new id
                id = imp_cg._get_next_id()
                dict[item] = id
                return id
            return item
        return to_return

    def run(self, input, working_memory):
        """
        Get dependency parse of input

        :param input: ASR hypotheses (same format as mention identification input)
        :param working_memory: DSG from last turn
        :return: dict<token span: concept graph>
        """
        dp_parse = [] # list of dicts (one for each hypothesis)
        self.dup_id = 1

        for hypothesis in input:
            parse = self.dependency_parser.predict(
                sentence=hypothesis['text']
            )
            cg = self.parse_to_cg(parse)
            wm_graph_copy = working_memory.graph.copy()
            wm_copy = WorkingMemory(wm=wm_graph_copy, kb=working_memory.knowledge_base)
            wm_copy.graph.merge(cg)
            wm_copy.pull(nodes=['"%s"'%token for token in hypothesis['tokens']], max_depth=2)
            template_implications = {}
            for situation_node, template in self.template_graphs.items():
                matches = wm_copy.graph.infer(template)
                transformation = self.transformation_graphs[situation_node]
                implication_maps = self.get_implication_maps(matches, transformation, cg.spans)
                template_implications.update(implication_maps)
            dp_parse.append(template_implications)
        return dp_parse

if __name__ == '__main__':
    merge = AllenDP('dp merge')
    sentence = "I love math"
    output = merge.run(sentence, {})