from structpy import specification
from GRIDD.data_structures.id_map import IdMap
from GRIDD.globals import *


@specification
class NodeFeaturesSpec:
    """
    Interface into features of nodes in working memory.
    """

    @specification.init
    def NODEFEATURES(NodeFeatures):
        node_features = NodeFeatures()
        assert len(node_features) == 0
        node_features=NodeFeatures({'A': 'a', 'B':'b'})
        assert node_features['A'] == 'a'
        assert node_features['B'] == 'b'
        return node_features

    @specification.init
    def update(NodeFeatures, other, id_map=None):
        """
        Update the node features as the maximum value between self and the features in `other`.

        `id_map` specifies the mapping between the nodes in `other` to the nodes in self
        """
        node_features = NodeFeatures(
            {'A': {
                    SALIENCE: 0.65,
                    'comps': {'orig', 'D'}
                },
            'B': {
                    SALIENCE: 0.5,
                },
            'D': {
                    SALIENCE: 0.01,
                },
            }
        )
        node_features_2 = NodeFeatures(
            {'A': {
                    SALIENCE: 0.5,
                },
            'B': {
                    SALIENCE: 0.75,
                },
            'C': {
                    SALIENCE: 0.1,
                },
            'X': {
                    'comps': {'x'}
                },
            'Z': {
                    'comps': {'z', 'zz'}
                }
            }
        )
        id_map = IdMap()
        for key, value in {'Z': 'A', 'z': 'a', 'zz': 'aa', 'X': 'E', 'x': 'e'}.items():
            id_map[key] = value

        node_features.update(node_features_2, id_map=id_map)
        assert node_features['A'][SALIENCE] == 0.65
        assert node_features['B'][SALIENCE] == 0.75
        assert node_features['C'][SALIENCE] == 0.1
        assert node_features['D'][SALIENCE] == 0.01
        assert 'Z' not in node_features
        assert node_features['A']['comps'] == {'orig', 'D', 'a', 'aa'}
        assert 'X' not in node_features
        assert node_features['E']['comps'] == {'e'}
        return node_features

    def merge(node_features, kept, replaced):
        """
        Replace `replaced` by `kept` by keeping the maximum feature values.
        """
        node_features.merge('C', 'D')
        assert 'D' not in node_features
        assert node_features['C'][SALIENCE] == 0.1
        assert node_features['A']['comps'] == {'orig', 'C', 'a', 'aa'}

    # todo - add tests for functions which perform feature updates after specific pipeline steps
    def update_from_ontology(node_features, elements):
        """
        Update features of nodes pulled from ontology.
        """
        pass

    def update_from_kb(node_features, elements):
        """
        Update features of nodes pulled from KnowledgeBase.
        """
        pass

    def update_from_mentions(node_features, elements, wm):
        """
        Update features of nodes added as a mention identification.
        """
        pass

    def update_from_inference(node_features, elements, wm):
        """
        Update features of nodes added as an inference.
        """
        pass

    def update_from_response(node_features, main_predicate, expansion_predicates):
        """
        Update features of nodes which are selected/expanded as response predicates.
        """
        pass

    def copy(node_features):
        cp = node_features.copy()
        assert id(cp) != id(node_features)

    def to_json(node_features):
        pass

    def from_json(node_features, json_dict, id_map=None):
        pass

    @specification.init
    def get_reference_links(NodeFeatures, element=None):
        """
        Return the reference nodes and their links present in the node features.

        If a specific element is specified,
            Return the reference links of `element` in `node_features`, if they exist.
            Otherwise, return None.
        """
        node_features = NodeFeatures(
            {'A': {'refl': ['a', 'aa']},
             'B': {'refl': ['b']},
             'C': {SALIENCE: 1.0}
            }
        )
        assert node_features.get_reference_links() == {
            'A': ['a', 'aa'],
            'B': ['b']
        }
        assert node_features.get_reference_links('A') == ['a', 'aa']