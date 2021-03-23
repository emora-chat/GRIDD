
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
        core = IntelligenceCore('''
        animal<entity>
        dog<animal>
        cat<animal>
        scared<predicate>
        happy<predicate>
        fido=dog()
        happy(fido)
        ''')
        return core

    def know(core, knowledge):
        """
        Add predicates to the knowledge base.
        """
        core.know('''
        chase<predicate>;
        z/chase(x/animal(), y/animal()) => scared(y) cause(c{c/predicate(x)}, z);
        ''')

    def consider(core, knowledge):
        """
        Add predicates to working memory.
        """
        core.consider('''
        chase(fido, fluffy=cat())
        ''')

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

    def apply_resolutions(core, resolutions=None):
        """
        Merge references with their referents if able.
        """
        core.apply_resolutions(core.resolve())

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

    def prune_attended(core, feature=None):
        """
        Remove concepts from working memory according to salience feature.
        """
        core.decay_salience()
        core.prune_attended()

    def operate(core, operations=None):
        """
        Update operation predicates (e.g. `max`, `add`).
        """
        core.operate()

    def update_confidences(core, feature=None):
        """
        Update confidence scores based on confidence links.
        """
        core.update_confidences()

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

    def display(core, verbosity=1):
        """
        Display working memory.
        """
        core.display(10)





