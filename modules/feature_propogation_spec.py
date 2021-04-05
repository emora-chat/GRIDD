from structpy import specification
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.globals import *

E = 0.0001

@specification
class FeaturePropogationSpec:

    @specification.init
    def FEATUREPROPOGATION(FeaturePropogation, max_score, turn_decrement, propogation_rate, propogation_decrement):
        feature_propogation = FeaturePropogation(max_score=1.0, turn_decrement=0.1, propogation_rate=0.5, propogation_decrement=0.1)
        return feature_propogation

    def __call__(feature_propogation, working_memory, iterations):
        """
        Update the spreadable features of working_memory
        """
        working_memory = WorkingMemory(KnowledgeBase())
        working_memory.add('john', 'likes', 'avengers', 'wm_0')
        working_memory.features['wm_0'][SALIENCE] = 1.0
        working_memory.features['john'][SALIENCE] = 1.0
        working_memory.features['avengers'][SALIENCE] = 1.0
        working_memory.features['likes'][SALIENCE] = 1.0
        working_memory.add('avengers', 'genre', 'action', 'wm_1')
        working_memory.add('sally', 'eat', 'cake', 'wm_2')
        working_memory.features['wm_2'][SALIENCE] = 1.0
        working_memory.features['wm_2'][COLDSTART] = 1.0

        feature_propogation(working_memory, iterations=1)
        assert 0.9 - E <= working_memory.features['wm_0'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['john'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['avengers'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['likes'][SALIENCE] <= 0.9 + E
        assert 0.4 - E <= working_memory.features['wm_1'][SALIENCE] <= 0.4 + E
        assert 0.0 - E <= working_memory.features['action'][SALIENCE] <= 0.0 + E
        assert working_memory.features['wm_2'][SALIENCE] == 1.0

        working_memory = WorkingMemory(KnowledgeBase())
        working_memory.add('john', 'likes', 'avengers', 'wm_0')
        working_memory.features['wm_0'][SALIENCE] = 1.0
        working_memory.features['john'][SALIENCE] = 1.0
        working_memory.features['avengers'][SALIENCE] = 1.0
        working_memory.features['likes'][SALIENCE] = 1.0
        working_memory.add('avengers', 'genre', 'action', 'wm_1')

        feature_propogation(working_memory, iterations=2)
        assert 0.9 - E <= working_memory.features['wm_0'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['john'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['avengers'][SALIENCE] <= 0.9 + E
        assert 0.9 - E <= working_memory.features['likes'][SALIENCE] <= 0.9 + E
        assert 0.6 - E <= working_memory.features['wm_1'][SALIENCE] <= 0.6 + E
        assert 0.15 - E <= working_memory.features['action'][SALIENCE] <= 0.15 + E

