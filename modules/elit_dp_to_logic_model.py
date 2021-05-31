
# https://emorynlp.github.io/ddr/doc/pages/overview.html
from GRIDD.modules.text_to_logic_model import ParseToLogic
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.modules.elit_dp_to_logic_spec import ElitDPSpec
from GRIDD.modules.elit_dp_to_logic_ontology import pos_mapper, generate_elit_dp_ontology, PRECEDE_LABELS, QUEST, TENSEFUL_AUX

import os
from os.path import join

import logging
logging.basicConfig(level=os.environ.get("LOGLEVEL","ERROR"))

NODES = ['focus', 'center', 'pstg', 'ref', 'type', 'ltype']


ont_cg = generate_elit_dp_ontology()
label_ont = ont_cg.types()

class ElitDPToLogic(ParseToLogic):

    def text_to_graph(self, *args):
        """
        Transform the ELIT Dependency Parse attachment list into a concept graph,
        supported with the token and pos ontology
        args[0,1,2] - tok, pos, dp
        :return dependency parse cg
        """
        cg = ConceptGraph(namespace='p_')
        self.convert(*args, cg)
        return cg

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
                             if label.lower() in PRECEDE_LABELS or pos_mapper(pos_tags[idx]) in QUEST]
        for token_idx in range(len(tokens)):
            span = tokens[token_idx]
            span_node = span.to_string()
            pos = pos_mapper(pos_tags[token_idx])
            if not cg.has(pos):
                add_ont_types = label_ont.get(pos, {'pstg'}) - {pos}
                for t in add_ont_types | {'pstg'}:
                    cg.add(pos, 'type', t)
            cg.features[span_node]["span_data"] = span
            self.spans.append(span_node)
            cg.add(span_node, 'type', pos)
            cg.add(span_node, 'type', 'span')
            if span.expression in TENSEFUL_AUX:
                cg.add(span_node, 'type', 'tenseful_aux')
            if token_idx > 0:
                for pti in precede_token_idx:
                    if pti < token_idx:
                        cg.add(tokens[pti].to_string(), 'precede', span_node) # todo - quantity logic for position considerations

        for token_idx, (head_idx, label) in enumerate(dependencies):
            if head_idx != -1:
                source = tokens[head_idx]
                target = tokens[token_idx]
                if not cg.has(label):
                    add_ont_types = label_ont.get(label, set()) - {label}
                    for t in add_ont_types:
                        cg.add(label, 'type', t)
                cg.add(source.to_string(), label, target.to_string())
            else:
                # assert the root
                cg.add(tokens[token_idx].to_string(), 'assert')


if __name__ == '__main__':
    print(ElitDPSpec.verify(ElitDPToLogic))