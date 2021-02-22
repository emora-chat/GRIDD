
from collections import defaultdict

class NodeFeatures:

    def __init__(self):
        self.features = defaultdict(dict)

    def update(self, other, id_map=None):
        for node, features in other.items():
            if id_map is not None:
                node = id_map.get(node)
            for feature, other_value in features.items():
                self.features[node][feature] = max(self.features[node].get(feature, 0.0), other_value)

    def merge(self, kept, replaced):
        self.features[kept]['salience'] = max(self.features[kept].get('salience', 0.0), self.features[replaced].get('salience', 0.0))
        self.features[kept]['cover'] = max(self.features[kept].get('cover', 0.0), self.features[replaced].get('cover', 0.0))
        self.features[kept]['coldstart'] = max(self.features[kept].get('coldstart', 0.0), self.features[replaced].get('coldstart', 0.0))
        del self.features[replaced]

    def get(self, key, default):
        return self.features.get(key, default)

    def items(self):
        return self.features.items()

    def to_dict(self):
        return self.features

    def __getitem__(self, item):
        return self.features[item]

    def __setitem__(self, key, value):
        self.features[key] = value