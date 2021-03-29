
from structpy import specification


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
        z/chase(x/animal(), y/animal()) => scared(y) cause(c:<c/predicate(x)>, z);
        ''')
        print(core.knowledge_base.pretty_print())

    def consider(core, knowledge):
        """
        Add predicates to working memory.
        """
        core.consider('''
        chase(fido, fluffy=cat())
        ''')
        print()
        print(core.working_memory.pretty_print())

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

    def merge(core, concept_sets):
        """
        Merge together each group of concepts in working memory.

        Automatically merges groups with overlap.
        """
        core.merge([])

    def resolve(core, references=None):
        """
        Resolve all references in working memory to their referents.
        """
        resolutions = core.resolve()

    def logical_merge(core):
        """
        Merge isomorphic concepts in working memory.
        """
        core.consider('scared(fluffy)')
        core.logical_merge()

    def pull_types(core):
        """
        Pull type hierarchy of all working memory concepts into working memory.
        """
        core.pull_types()

    def pull_knowledge(core, k=1):
        """
        Pull knowledge of semantic neighbors of working memory concepts from knowledge base.
        """
        core.consider(core.pull_knowledge())

    def pull_expressions(core):
        """
        Pull all expressions of working memory concepts.
        """
        core.pull_expressions()

    def update_confidence(core, feature=None):
        """
        Update confidence scores based on confidence links.
        """
        core.update_confidence()

    def update_salience(core, feature=None):
        """
        Update salience scores based on semantic relatedness.
        """
        core.update_salience()

    def decay_salience(core, feature=None):
        """
        Decay salience
        """
        core.decay_salience()

    def prune_attended(core, feature=None):
        """
        Remove concepts from working memory according to salience feature.
        """
        core.prune_attended()

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





