from GRIDD.modules.reference_merge_spec import ReferenceMergeSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine

class ReferenceMerge:

    def __init__(self, device='cpu'):
        self.inference_engine = InferenceEngine(device=device)

    def _get_reference_preconditions(self, references, concept_graph):
        reference_preconditions = {}
        for reference, constraints in references.items():
            constraint_predicates = {(reference, 'var', None)}
            for constraint in constraints:
                if concept_graph.has(predicate_id=constraint):
                    constraint_predicates.add(concept_graph.predicate(constraint))
                constraint_predicates.add((constraint, 'var', None))
            reference_preconditions[reference] = ConceptGraph(predicates=constraint_predicates,
                                                              namespace='reference_')
        return reference_preconditions

    def __call__(self, concept_graph):
        compatible_pairs = []
        references = {}
        for s, t, _ in concept_graph.edges(label='refl'):
            references.setdefault(s, set()).add(t)
        if len(references) > 0:
            reference_preconditions = self._get_reference_preconditions(references, concept_graph)
            match_dict = self.inference_engine.infer(concept_graph, *[(precondition, None, reference_node)
                                                                     for reference_node, precondition
                                                                     in reference_preconditions.items()])
            compatible_pairs = []
            for reference_node, (pre,post,matches) in match_dict.items():
                if len(matches) == 2:
                    # todo - what to do on reference ambiguity; for now, don't merge
                    # one match of the 2 is the reference itself, so only one real match is found
                    for match in matches:
                        pairs = [(match[node], node) for node in match] if reference_node != match[reference_node] else []
                        compatible_pairs.extend(pairs)
        return compatible_pairs



if __name__ == '__main__':
    print(ReferenceMergeSpec.verify(ReferenceMerge))