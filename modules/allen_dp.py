from allennlp.predictors.predictor import Predictor
from modules.module import Module
from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_graph import KnowledgeGraph
import knowledge_base.knowledge_graph as kg
from knowledge_base.working_memory import WorkingMemory
from structpy.map.bijective.bimap import Bimap
from os.path import join

class CharSpan:

    def __init__(self, string, start, end):
        self.string = string
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%d,%d)'%(self.string, self.start, self.end)

class AllenDP(Module):

    def __init__(self, name):
        super().__init__(name)
        self.dependency_parser = Predictor.from_path("https://storage.googleapis.com/allennlp-public-models/biaffine-dependency-parser-ptb-2020.04.06.tar.gz")
        # POS tag and dependency parse link CANNOT be the same (causes Prolog solution-finding problems)
        # see det vs detpred for example
        self.pos_nodes = ['verb','noun','pron','det','adj','adv']
        self.nodes = ['nsubj','dobj','amod','detpred','focus','center','pos','exprof','ltype']
        self.templates = KnowledgeGraph(loading_kb=False)
        for n in self.pos_nodes + self.nodes:
            self.templates._concept_graph.add_monopredicate(n, 'is_type')
        self.templates.add_knowledge(join('knowledge_base', 'kg_files', 'allen_dp_templates.txt'))
        self.template_graphs, self.transformation_graphs = self.templates._concept_graph.generate_inference_graphs()
        self.inference_reference_expansion()

    def parse_to_cg(self, parse_dict):
        """
        Given the AllenAI Dependency Parse hierplane dict, transform it into a concept graph
        :return dependency parse cg
        """
        cg = ConceptGraph(nodes=list(kg.BASE_NODES)+self.nodes+self.pos_nodes)
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
            print('WARNING! dp element %s has more than one span'%expression)
            print(spans)
        charspan = CharSpan(expression,spans[0]['start'],spans[0]['end'])
        cg.spans[span_node] = charspan

        expression = '"%s"'%expression
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

    def get_unknown_references(self, parse_cg):
        for span_node,span_object in parse_cg.spans.items():
            expression = '"%s"'%span_object.string
            references = parse_cg.object_neighbors(expression, 'expr')
            if len(references) == 0:
                unk_node = parse_cg.add_node(parse_cg._get_next_id())
                parse_cg.add_bipredicate(unk_node, 'unknown', 'type')
                parse_cg.add_bipredicate(expression, unk_node, 'expr')

    def inference_reference_expansion(self):
        """
        x -t-> y ==> x -exprof-> a -expr-> b -t-> y if x has TYPE_PREDICATE
                 ==> x -exprof-> a -expr-> b        if x does not have TYPE_PREDICATE
        :return:
        """
        for situation_node, template_graph in self.template_graphs.items():
            for concept in template_graph.concepts():
                if template_graph.type(concept) is None and \
                len(template_graph.monopredicate(concept, 'var')) > 0:
                    # found variable entity instance
                    found_supertype = False
                    for supertype in template_graph.object_neighbors(concept, 'ltype'):
                        found_supertype = True
                        self._expand_references(template_graph, concept, supertype)
                    if not found_supertype:
                        self._expand_references(template_graph, concept)

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

    def get_variable_assignments(self, var_matches):
        var_map, matches = var_matches
        solutions = []
        for match in matches:
            variable_assignments = {}
            for key,value in var_map.items():
                variable_assignments[key] = match[value]
            solutions.append(variable_assignments)
        return solutions

    def run(self, input, working_memory):
        """
        Get dependency parse of input

        :param input: ASR hypotheses (same format as mention identification input)
        :param working_memory: DSG from last turn
        :return: dict<token span: concept graph>
        """
        dp_parse = [] # list of dicts (one for each hypothesis)

        for hypothesis in input:
            parse = self.dependency_parser.predict(
                sentence=hypothesis['text']
            )
            cg = self.parse_to_cg(parse)
            cg.pull(nodes=['"%s"'%span_obj.string for span_node,span_obj in cg.spans.items()],
                       kb=working_memory.knowledge_base, max_depth=1)
            self.get_unknown_references(cg)
            template_implications = {}
            for situation_node, template in self.template_graphs.items():
                matches = cg.infer(template)
                transformation = self.transformation_graphs[situation_node]
                implication_maps = self.get_variable_assignments(matches)
                template_implications.update(implication_maps)
            dp_parse.append(template_implications)
        return dp_parse

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

    output = AllenDP('allendp').run(asr_hypotheses, working_memory)