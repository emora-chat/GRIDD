
from collections import defaultdict
from GRIDD.data_structures.node_features_spec import NodeFeaturesSpec
from GRIDD.data_structures.span import Span
from GRIDD.globals import CONFIDENCE

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
                    if feature in {'salience', 'cover', 'coldstart'}:
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
                            print('Span Update: ', features['span_data'])
                            raise RuntimeError('Node already has span info!') #todo - get rid of before deployment
                        else:
                            self[node]['span_data'] = features['span_data']
                    else:
                        self[node][feature] = other_value

    def merge(self, kept, replaced): # todo - add confidence?
        if replaced in self:
            if kept not in self:
                self[kept] = {}
            if 'salience' in self[kept] or 'salience' in self[replaced]:
                self[kept]['salience'] = max(self[kept].get('salience', 0.0), self[replaced].get('salience', 0.0))
            if 'cover' in self[kept] or 'cover' in self[replaced]:
                self[kept]['cover'] = max(self[kept].get('cover', 0.0), self[replaced].get('cover', 0.0))
            if 'coldstart' in self[kept] or 'coldstart' in self[replaced]:
                self[kept]['coldstart'] = max(self[kept].get('coldstart', 0.0), self[replaced].get('coldstart', 0.0))
            if 'span_data' in self[replaced]:
                if 'span_data' in self[kept]:
                    print('Replaced: ', self[replaced]['span_data'])
                    print('Kept: ', self[kept]['span_data'])
                    raise Exception('Cannot merge two span nodes!')
                else:
                    self[kept]['span_data'] = self[replaced]['span_data']
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
        inference_salience = 0.75  # todo - how to set inference salience???
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

    def remove(self, node):
        del self[node]

    def discard(self, node):
        if node in self:
            del self[node]

    def get_reference_links(self, element=None):
        if element is not None:
            if element in self:
                return self[element].get('refl', None)
            return None
        else:
            references = {}
            for item, features in self.items():
                if 'refl' in features:
                    references[item] = features['refl']
            return references

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