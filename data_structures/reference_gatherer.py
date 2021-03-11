
PRIMITIVES = {'focus', 'center', 'is_type', 'cover', 'question', 'var'}

def gather_all_references(working_memory):
    # convert reference spans to reference predicates
    for node, features in working_memory.features.items():
        if 'refsp' in features:
            features['refl'] = gather(node, features['refsp'], working_memory)
            del features['refsp']
    return working_memory

def gather(reference_node, constraints_as_spans, concept_graph):
    constraints = set()
    focal_nodes = {reference_node}
    for constraint_span in constraints_as_spans:
        if concept_graph.has(constraint_span):
            foci = concept_graph.objects(constraint_span, 'ref')
            focus = next(iter(foci))  # todo - could be more than one focal node in disambiguation situation?
            focal_nodes.add(focus)
    # expand constraint spans into constraint predicates
    for focal_node in focal_nodes:
        components = [focal_node] if concept_graph.has(predicate_id=focal_node) else []
        components += concept_graph.features[focal_node]['comps']
        # constraint found if constraint predicate is connected to reference node
        for component in components:
            if (not concept_graph.has(predicate_id=component) or
                concept_graph.type(component) not in PRIMITIVES) and \
                concept_graph.graph_component_siblings(component, reference_node):
                constraints.add(component)
    return list(constraints)

