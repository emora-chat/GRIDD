from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.node_features import NodeFeatures

def identity(x): return x

@specification
class ReferenceMergeSpec:

    @specification.init
    def REFERENCEMERGE(ReferenceMerge, reference_retrieval_func, device='cpu'):
        """
        `reference_retrieval_func` defines how reference links in `concept_graph` metadata are processed
        into predicate instances when the `reference_merge` module is called.

        `device` is used to specify whether inference matching is done on cpu or gpu.
        """
        ref_merge = ReferenceMerge(reference_retrieval_func=identity)
        return ref_merge

    def __call__(ref_merge, concept_graph):
        """
        Returns pairs of nodes where each pair contains a compatible node for a given reference node.

        Reference nodes are identified as nodes with reference links in the metadata.
        The reference links are processed into predicate instances by the module's
        `reference_retrieval_func`.
        These predicate instances are used to construct the precondition of the implication rule
        defining the constraints of the reference node.
        These preconditions are applied to `concept_graph` through the `graph_matching_engine`
        in order to find compatible nodes for each reference.
        """

        cg = ConceptGraph(predicates=[
            ('fido', 'type', 'dog', 'ftd'),
            ('fido', 'color', 'red', 'fcr'),
            ('spark', 'type', 'dog', 'std'),
            ('spark', 'color', 'white', 'scw'),
            ('rose', 'color', 'white', 'rcw'),
            ('d1', 'type', 'dog', 'dtd'),
            ('d1', 'color', 'red', 'dcr'),
            ('d2', 'color', 'white', 'dcw')
        ], feature_cls=NodeFeatures)
        cg.features['d1']['refl'] = ['dtd', 'dcr']
        cg.features['d2']['refl'] = ['dcw']

        pairs = ref_merge(cg)
        assert len(pairs) == 3
        assert ('d1', 'fido') in pairs
        assert ('d2', 'spark') in pairs
        assert ('d2', 'rose') in pairs