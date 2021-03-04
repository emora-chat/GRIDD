from GRIDD.modules.reference_merge_spec import ReferenceMergeSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine

class ReferenceMerge:

    def __init__(self, reference_retrieval_func, device='cpu'):
        self.reference_retrieval = reference_retrieval_func
        self.inference_engine = InferenceEngine(device=device)

    def get_reference_preconditions(self, references, concept_graph):
        reference_preconditions = {}
        for reference, links in references.items():
            constraints = [self.reference_retrieval(l) for l in links]
            constraint_predicates = [(reference, 'var', None)]
            for constraint in constraints:
                if concept_graph.has(predicate_id=constraint):
                    constraint_predicates.append(concept_graph.predicate(constraint))
                    constraint_predicates.append((constraint, 'var', None))
                else:
                    print('Reference: ', reference)
                    print('Links: ', links)
                    print('Constraints: ', constraints)
                    print('Current: ', constraint)
                    raise Exception('Found non-predicate reference link')
            reference_preconditions[reference] = ConceptGraph(predicates=constraint_predicates,
                                                              namespace='reference_')
        return reference_preconditions

    def __call__(self, concept_graph):
        references = concept_graph.features.get_reference_links()
        reference_preconditions = self.get_reference_preconditions(references, concept_graph)
        match_dict = self.inference_engine.infer(concept_graph, *[(precondition, None, reference_node)
                                                                 for reference_node, precondition
                                                                 in reference_preconditions.items()])
        compatible_pairs = [(reference_node, match[reference_node])
                            for reference_node, (pre,post,matches) in match_dict.items()
                            for match in matches
                            if reference_node != match[reference_node]]
        return compatible_pairs



if __name__ == '__main__':
    print(ReferenceMergeSpec.verify(ReferenceMerge))