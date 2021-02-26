
from collections import defaultdict
from GRIDD.data_structures.node_features_spec import NodeFeaturesSpec

class NodeFeatures(defaultdict):

    def __init__(self, values=None):
        super(NodeFeatures, self).__init__(dict)
        if values is not None and len(values) > 0:
            super().update(values)

    def update(self, other, id_map=None):
        for node, features in other.items():
            if id_map is not None:
                node = id_map.get(node)
            for feature, other_value in features.items():
                self[node][feature] = max(self[node].get(feature, 0.0), other_value)

    def merge(self, kept, replaced):
        self[kept]['salience'] = max(self[kept].get('salience', 0.0), self[replaced].get('salience', 0.0))
        self[kept]['cover'] = max(self[kept].get('cover', 0.0), self[replaced].get('cover', 0.0))
        self[kept]['coldstart'] = max(self[kept].get('coldstart', 0.0), self[replaced].get('coldstart', 0.0))
        del self[replaced]

    def update_from_ontology(self, elements):
        for e in elements:
            self[e]['salience'] = self[e].get('salience', 0.0)

    def update_from_kb(self, elements):
        for e in elements:
            self[e]['salience'] = self[e].get('salience', 0.0)

    def update_from_mentions(self, elements, wm):
        for id in elements:
            self[id]['salience'] = 1.0
            if wm.has(predicate_id=id):
                self[id]['cover'] = 1.0

    def update_from_inference(self, elements, wm):
        inference_salience = 0.5  # todo - how to set inference salience???
        for id in elements:
            if wm.has(predicate_id=id) and wm.type(id) == 'question':
                self[id]['salience'] = inference_salience * 1.5
            else:
                self[id]['salience'] = max(inference_salience, self[id].get('salience', 0.0))

    def update_from_response(self, main_predicate, expansion_predicates):
        self[main_predicate[3]]['salience'] = 1.0
        self[main_predicate[3]]['cover'] = 1.0
        for pred in expansion_predicates:
            self[pred[3]]['salience'] = 1.0
            self[pred[3]]['cover'] = 1.0

    def copy(self):
        return NodeFeatures(self)


if __name__ == '__main__':
    print(NodeFeaturesSpec.verify(NodeFeatures))