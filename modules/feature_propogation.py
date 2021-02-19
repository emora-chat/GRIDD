from GRIDD.data_structures.score_graph import ScoreGraph
from GRIDD.modules.feature_propogation_spec import FeaturePropogationSpec

class FeaturePropogation:

    def __init__(self, max_score, turn_decrement, propogation_rate, propogation_decrement):
        self.max_score = max_score
        self.turn_decrement = turn_decrement
        self.propogation_rate = propogation_rate
        self.propogation_decrement = propogation_decrement

    def __call__(self, working_memory, iterations):
        """
        Update the features of the nodes in working memory
        """
        for key in working_memory.features:
            working_memory.features[key]['salience'] = max(0.0, working_memory.features[key].get('salience', 0.0) - self.turn_decrement)

        edges = [(*edge, 'spread') for s, t, o, i in working_memory.predicates()
                                    for edge in [(s, i), (i, s), (o, i), (i, o)]
                                    if edge[0] is not None and edge[1] is not None
                                    and t not in ['ref', 'def'] and o != 'span']

        # higher salience pulls up lower salience attachments, but not vice versa
        score_graph = ScoreGraph(
            edges=edges,
            updaters={
                'spread': (lambda x, y: (0,
                                         min(self.max_score - y, self.propogation_rate*(x - self.propogation_decrement - y))
                                         if x is not None and y is not None and x - self.propogation_decrement >= y
                                         else 0))
            },
            get_fn=lambda x: working_memory.features[x].get('salience', 0.0),
            set_fn=lambda x, y: working_memory.features[x].__setitem__('salience', y),
            maximum=self.max_score
        )

        score_graph.update(iterations=iterations, push=True)

        # to_remove = set()
        # for key in working_memory.features['salience']:
        #     if working_memory.features['salience'][key] <= 0.0:
        #         to_remove.add(key)
        # for key in to_remove:
        #     del working_memory.features['salience'][key]
        #     working_memory.remove(key)

        return working_memory

if __name__ == '__main__':
    print(FeaturePropogationSpec.verify(FeaturePropogation))