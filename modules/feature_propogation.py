from GRIDD.data_structures.score_graph import ScoreGraph


class FeaturePropogation:

    def __call__(self, working_memory):
        """
        Update the features of the nodes in working memory
        """
        for key in working_memory.features['salience']:
            working_memory.features['salience'][key] -= 0.1

        edges = [(*edge, 'spread') for s, t, o, i in working_memory.predicates()
                                    for edge in [(s, i), (i, s), (o, i), (i, o)]
                                    if edge[0] is not None and edge[1] is not None
                                    and t not in ['ref', 'def'] and o != 'span']

        # higher salience pulls up lower salience attachments, but not vice versa
        score_graph = ScoreGraph(
            edges=edges,
            updaters={
                'spread': (lambda x, y: (0,
                                         min(1.0 - y, 0.9*(x - y))
                                         if x is not None and y is not None and x >= y
                                         else 0))
            },
            get_fn=lambda x: working_memory.features['salience'].get(x),
            set_fn=lambda x, y: working_memory.features['salience'].__setitem__(x, y)
        )

        score_graph.update(iterations=1, push=True)

        # to_remove = set()
        # for key in working_memory.features['salience']:
        #     if working_memory.features['salience'][key] <= 0.0:
        #         to_remove.add(key)
        # for key in to_remove:
        #     del working_memory.features['salience'][key]
        #     working_memory.remove(key)

        return working_memory