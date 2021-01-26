
from structpy import specification
from data_structures.infer import infer, ImplicationRule
from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory


@specification
class MergeLogicalSpec:

    @specification.init
    def MERGE_LOGICAL(MergeLogical, inference_engine):

        merge_logical = MergeLogical(infer)

        working_memory = WorkingMemory(
            KnowledgeBase(
                '''
                barks<predicate>
                own<predicate>
                dog<entity>
                person<entity>
                name<predicate>
                expression<entity>
                user=person()
                sally=person()
                ;'''
            ),
            '''
            barks(fido1=dog())
            own(user, fido1)
            name(user, "john"=expression())
            
            own(user, fido2=dog())
            
            barks(patch=dog())
            own(sally, patch)
            name(sally, "sally"=expression())
            ;'''
        )

        working_memory.pull_ontology()
        merges = merge_logical(working_memory)
        assert ('fido2', 'fido1') in set(merges)
        assert not ('fido1', 'fido2') in set(merges)
        assert not ('patch', 'fido1') in set(merges)
        assert not ('fido1', 'patch') in set(merges)
