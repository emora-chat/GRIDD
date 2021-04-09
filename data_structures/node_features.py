
from collections import defaultdict
from GRIDD.data_structures.node_features_spec import NodeFeaturesSpec
from GRIDD.data_structures.span import Span
from GRIDD.globals import *

class NodeFeatures(defaultdict):

    def __init__(self, values=None):
        super(NodeFeatures, self).__init__(dict)
        if values is not None and len(values) > 0:
            super().update(values)

    def update(self, other, id_map=None, concepts=None):
        for node, features in other.items():
            if concepts is None or node in concepts:
                if id_map is not None:
                    node = id_map.get(node)
                for feature, other_value in features.items():
                    if feature in {SALIENCE, 'cover', COLDSTART}:
                        if feature in self[node]:
                            self[node][feature] = max(self[node][feature], other_value)
                        else:
                            self[node][feature] = other_value
                    elif feature == CONFIDENCE:
                        if feature in self[node]:
                            print(f'WARNING: Existing confidence value of {node} is being updated!')
                        self[node][feature] = other_value
                    elif feature == 'span_data':
                        if 'span_data' in self[node]:
                            print('Node: ', str(node))
                            print('Span Exists: ', self[node]['span_data'])
                            print('Span Update: ', other_value)
                            raise RuntimeError('Node already has span info!') #todo - get rid of before deployment
                        else:
                            self[node]['span_data'] = other_value
                    else:
                        self[node][feature] = other_value

    def merge(self, kept, replaced):
        if replaced in self:
            if kept not in self:
                self[kept] = {}
            for feature, other_value in self[replaced].items():
                if feature in {SALIENCE, 'cover', COLDSTART}:
                    if feature in self[kept]:
                        self[kept][feature] = max(self[kept][feature], other_value)
                    else:
                        self[kept][feature] = other_value
                elif feature == CONFIDENCE:
                    if feature in self[kept]:
                        print(f'WARNING: Existing confidence value of {kept} is being updated!')
                    self[kept][feature] = other_value
                elif feature == 'span_data':
                    if 'span_data' in self[kept]:
                        print('Node: ', str(kept))
                        print('Span Exists: ', self[kept]['span_data'])
                        print('Span Update: ', other_value)
                        raise RuntimeError('Node already has span info!')  # todo - get rid of before deployment
                    else:
                        self[kept]['span_data'] = other_value
                else:
                    self[kept][feature] = other_value
            del self[replaced]

    def update_from_ontology(self, elements):
        for e in elements:
            self[e][SALIENCE] = self[e].get(SALIENCE, 0.0)

    def update_from_kb(self, elements):
        for e in elements:
            self[e][SALIENCE] = self[e].get(SALIENCE, 0.0)

    def update_from_mentions(self, elements, wm):
        for id in elements:
            self[id][SALIENCE] = 1.0
            if wm.has(predicate_id=id):
                self[id]['cover'] = 1.0

    def update_from_inference(self, elements, wm):
        inference_salience = 0.75  # todo - how to set inference salience???
        for id in elements:
            if wm.has(predicate_id=id) and wm.type(id) == 'question':
                self[id][SALIENCE] = inference_salience * 1.5
            else:
                self[id][SALIENCE] = max(inference_salience, self[id].get(SALIENCE, 0.0))

    def update_from_response(self, main_predicate, expansion_predicates):
        self[main_predicate[3]][SALIENCE] = 1.0
        self[main_predicate[3]]['cover'] = 1.0
        for pred in expansion_predicates:
            self[pred[3]][SALIENCE] = 1.0
            self[pred[3]]['cover'] = 1.0

    def remove(self, node):
        del self[node]

    def discard(self, node):
        if node in self:
            del self[node]

    def copy(self):
        return NodeFeatures(self)

    def to_json(self):
        json_compatible = {}
        for node, features in self.items():
            json_compatible[node] = {}
            for feature, value in features.items():
                if feature == "span_data":
                    json_compatible[node][feature] = value.to_string()
                else:
                    json_compatible[node][feature] = value
        return json_compatible

    def from_json(self, json_dict, id_map=None):
        for node, features in json_dict.items():
            if id_map is not None:
                node = id_map.get(node)
            for feature, value in features.items():
                if feature == "span_data":
                    self[node][feature] = Span.from_string(value)
                else:
                    self[node][feature] = value


if __name__ == '__main__':
    print(NodeFeaturesSpec.verify(NodeFeatures))