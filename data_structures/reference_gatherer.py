from GRIDD.data_structures.reference_gatherer_spec import ReferenceGathererSpec

class ReferenceGatherer:

    PRIMITIVES = {'focus', 'center', 'is_type', 'cover', 'question', 'var'}

    def gather(self, reference_node, constraints_as_spans, concept_graph):
        constraints = set()
        focal_nodes = {reference_node}
        for constraint_span in constraints_as_spans:
            foci = concept_graph.objects(constraint_span, 'ref')
            focus = next(iter(foci))  # todo - could be more than one focal node in disambiguation situation?
            focal_nodes.add(focus)
        # expand constraint spans into constraint predicates
        for focal_node in focal_nodes:
            components = [focal_node] if concept_graph.has(predicate_id=focal_node) else []
            components += concept_graph.features[focal_node]['comps']
            # constraint found if constraint predicate is connected to reference node
            for component in components:
                if (not concept_graph.has(predicate_id=component) or \
                    concept_graph.type(component) not in ReferenceGatherer.PRIMITIVES) and \
                    concept_graph.graph_component_siblings(component, reference_node):
                    constraints.add(component)
        return constraints


if __name__ == '__main__':
    print(ReferenceGathererSpec.verify(ReferenceGatherer))
