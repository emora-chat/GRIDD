
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
ALLOW_SINGLE = ['cd', 'dt', 'ex', 'adj', 'noun', 'pron', 'adv', 'interj', 'verb', 'question_word']

TENSEFUL_AUX = ['go', 'goes', 'went', 'do', 'does', 'did', 'be', 'is', 'are', 'were', 'was'] # use lemma instead from elit

ADVCL_INDICATOR = ['adv', 'aux', 'mark', 'case']
ACL_INDICATOR = ['aux', 'mark', 'case']
SUBJECTS = ['nsbj', 'csbj']

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
        for n in ADVCL_INDICATOR:
            ewm.add(POS_MAP.get(n, n), 'type', 'advcl_indicator')
        for n in ACL_INDICATOR:
            ewm.add(POS_MAP.get(n, n), 'type', 'acl_indicator')
        for n in SUBJECTS:
            ewm.add(POS_MAP.get(n, n), 'type', 'sbj')
        self.convert(*args, ewm)
        return ewm

    # todo - verify that POS tags and DP labels are disjoint
    def convert(self, elit_results, cg):
        """
        Add dependency parse links into the expression concept graph
        :param elit_results: dictionary of elit model results
        :param cg: the concept graph being created
        """
        tokens = elit_results.get("tok", [])
        pos_tags = elit_results.get("pos", [])
        dependencies = elit_results.get("dep", [])
        precede_token_idx = [idx for idx, (head_idx, label) in enumerate(dependencies)
                             if label.lower() in PRECEDE_LABELS or pos_tags[idx].lower().replace('$','ds') in QUEST]
        for token_idx in range(len(tokens)):
            span = tokens[token_idx]
            expression = span.expression
            pos = pos_tags[token_idx].lower().replace('$','ds')
            pos = POS_MAP.get(pos, pos)
            if 'pstg' not in cg.supertypes(pos): # todo - optimization by dynamic programming
                cg.add(pos, 'type', 'pstg')
            span_node = span.to_string()
            if expression in TENSEFUL_AUX:
                cg.add(span_node, 'type', 'tenseful_aux')
            cg.features[span_node]["span_data"] = span
            cg.add(span_node)
            self.spans.append(span_node)
            expression = '"%s"' % expression
            cg.add(span_node, 'ref', expression)
            cg.add(span_node, 'type', pos)
            if token_idx > 0:
                for pti in precede_token_idx:
                    if pti < token_idx:
                        cg.add(tokens[pti].to_string(), 'precede', span_node) # todo - quantity logic for position considerations

        for token_idx, (head_idx, label) in enumerate(dependencies):
            if head_idx != -1:
                source = tokens[head_idx]
                target = tokens[token_idx]
                if label == 'com': # condense compound relations into single entity
                    original_source = source.to_string()
                    original_target = target.to_string()

                    for tuple in cg.predicates(original_target, 'ref') + cg.predicates(original_source, 'ref'):
                        cg.remove(tuple[2]) # remove non-condensed expressions
                    self.spans.remove(original_target)
                    original_source_span_idx = self.spans.index(original_source)
                    del cg.features[original_source]
                    del cg.features[original_target]

                    source.string = target.string + ' ' + source.string
                    source.expression = target.expression + ' ' + source.expression
                    source.start = target.start
                    new_source = source.to_string()
                    cg.features[new_source]["span_data"] = source
                    self.spans[original_source_span_idx] = new_source
                    cg.add(new_source, 'ref', '"%s"'%source.string) # add updated condensed expression
                    cg.merge(new_source, original_source)
                    cg.merge(new_source, original_target)
                else:
                    cg.add(source.to_string(), label, target.to_string())
            else:
                # assert the root
                cg.add(tokens[token_idx].to_string(), 'assert')


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