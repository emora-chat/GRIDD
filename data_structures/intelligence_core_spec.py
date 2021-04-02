
from structpy import specification
from GRIDD.globals import *

@specification
class IntelligenceCoreSpec:
    """
    Intelligence Core is a AI module for managing a knowledge
    base and performing flexible inferences on the facts in that
    knowledge base.
    """

    @specification.init
    def INTELLIGENCE_CORE(IntelligenceCore, knowledge_base=None, working_memory=None, inference_engine=None):
        """
        Create an Intelligence Core
        """
        core = IntelligenceCore(['''
        animal = (entity)
        [dog, cat] = (animal)
        [scared, happy] = (predicate)
        fido = dog()
        happy(fido)
        ''', 'GRIDD/resources/kg_files/intcore.kg'])
        return core

    def know(core, knowledge):
        """
        Add predicates to the knowledge base.
        """
        core.know('''
        cause = (predicate);
        z/chase(x/animal(), y/animal()) => scared(y);
        ''')

    def accept(core, knowledge):
        """
        Add predicates to working memory with confidence assumed.
        """
        core.accept('''
        chase(fido, fluffy=cat())
        ''')
        print()
        print(core.working_memory.pretty_print())

    def consider(core, knowledge):
        """
        Add predicates to working memory.
        """
        core.consider('''
        cref:<chase(fido, cref=cat())>
        ''')
        print()
        print(core.working_memory.pretty_print())

    def pull_types(core):
        """
        Pull type hierarchy of all working memory concepts into working memory.
        """
        core.pull_types()

    def infer(core, rules=None):
        """
        Find solutions to inference rule preconditions.
        """
        inferences = core.infer()

    def apply_inferences(core, inferences=None):
        """
        Add instantiated postconditions to working memory based on inference solutions.
        """
        core.apply_inferences(core.infer())
        return

    def update_confidence(core, feature=None):
        """
        Update confidence scores based on confidence links.
        """
        core.update_confidence()
        return

    def update_salience(core, feature=None):
        """
        Update salience scores based on semantic relatedness.
        """
        core.update_salience()
        return

    def resolve(core, references=None):
        """
        Resolve all references in working memory to their referents.
        """
        resolutions = core.resolve()
        assert len(resolutions) == 3
        assert ('fluffy', 'cref') in resolutions
        return

    def pull_knowledge(core, k=1):
        """
        Pull knowledge of semantic neighbors of working memory concepts from knowledge base.
        """
        additions = core.pull_knowledge(10, 10)
        assert len(additions) == 1
        core.consider(additions)
        return

    def decay_salience(core, feature=None):
        """
        Decay salience
        """
        core.consider('''
        ht=happy(taylor=dog()){"%s": 0.1}
        '''%SALIENCE)
        core.decay_salience()
        assert core.working_memory.features['ht'][SALIENCE] == 0.0

    def prune_attended(core, keep, feature=None):
        """
        Remove concepts from working memory according to salience feature.
        """
        core.prune_attended(2)
        assert not core.working_memory.has(predicate_id='ht')
        return

    def pull_expressions(core):
        """
        Pull all expressions of working memory concepts.
        """
        core.pull_expressions()

    def merge(core, concept_sets):
        """
        Merge together each group of concepts in working memory.

        Automatically merges groups with overlap.
        """
        core.merge([])

    def logical_merge(core):
        """
        Merge isomorphic concepts in working memory.
        """
        core.consider('scared(fluffy)')
        core.logical_merge()

    def operate(core, operations=None):
        """
        Update operation predicates (e.g. `max`, `add`).
        """
        core.operate()

    def display(core, verbosity=1):
        """
        Display working memory.
        """
        core.display(10)





