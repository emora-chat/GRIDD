
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
                    if feature in {SALIENCE, COLDSTART}:
                        if feature in self[node]:
                            self[node][feature] = max(self[node][feature], other_value)
                        else:
                            self[node][feature] = other_value
                    elif feature in {BASE_CONFIDENCE, BASE_UCONFIDENCE}:
                        self[node][feature] = other_value
                    elif feature == 'span_data':
                        if 'span_data' in self[node]:
                            print('[WARNING] Node %s already has span info!'%str(node))
                            print('\tSpan Exists: ', self[node]['span_data'])
                            print('\tSpan Update: ', other_value)
                        else:
                            self[node]['span_data'] = other_value
                    elif feature in {UTURN_POS, ETURN_POS, UTURN, ETURN}:
                        self[node].setdefault(feature, []).extend(other_value)
                    else:
                        self[node][feature] = other_value

    def merge(self, kept, replaced):
        if replaced in self:
            if kept not in self:
                self[kept] = {}
            for feature, other_value in self[replaced].items():
                if feature in {SALIENCE, COLDSTART}:
                    if feature in self[kept]:
                        self[kept][feature] = max(self[kept][feature], other_value)
                    else:
                        self[kept][feature] = other_value
                elif feature in {BASE_CONFIDENCE, BASE_UCONFIDENCE}:
                    self[kept][feature] = other_value
                elif feature == 'span_data':
                    if 'span_data' in self[kept]:
                        print('[WARNING] Node %s already has span info!' % str(kept))
                        print('\tSpan Exists: ', self[kept]['span_data'])
                        print('\tSpan Update: ', other_value)
                    else:
                        self[kept]['span_data'] = other_value
                elif feature in {UTURN_POS, ETURN_POS, UTURN, ETURN}:
                    self[kept].setdefault(feature, []).extend(other_value)
                else:
                    self[kept][feature] = other_value
            del self[replaced]

    def remove(self, node):
        del self[node]

    def discard(self, node):
        if node in self:
            del self[node]

    def get_confidence(self, node, default=0.0):
        return self.get(node, {}).get(CONFIDENCE,
                                      self.get(node, {}).get(BASE_CONFIDENCE, default))

    def copy(self):
        return NodeFeatures(self)

    def to_json(self):
        json_compatible = {}
        for node, features in self.items():
            json_compatible[node] = {}
            for feature, value in features.items():
                if feature == "span_data":
                    json_compatible[node][feature] = value.to_string()
                elif isinstance(value, float):
                    json_compatible[node][feature] = round(value, 2)
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