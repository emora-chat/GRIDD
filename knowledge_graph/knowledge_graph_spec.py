
from structpy import specification


@specification
class KnowledgeGraph:
    """
    Data structure for creating, editing, and querying a Knowledge Graph as part of the
    GRIDD Framework.

    Nodes in the knowledge graph are accessed by a string identifier, which is provided
    by the user upon adding the node (although some nodes are automatically generated and
    assigned an integer ID).
    """

    def KNOWLEDGE_GRAPH(KnowledgeGraph, filename=None, nodes=None):
        """
        Create a `KnowledgeGraph` object.

        Providing a `file_name` will load a text file from a previous `knowledge_graph.save` operation.

        Providing a `nodes` list will initialize those nodes.
        """
        knowledge_graph = KnowledgeGraph('example.kg')
        return knowledge_graph

    def add_entity_type(kg, entity_type, supertypes):
        """
        Add a concept to the KG that cannot be interpreted as a predicate.

        `entity_type` is the id of the added concept.

        `supertypes` should be a list of `entity_type`'s types (a single string can
        be provided in the case of a single type relationship).
        """
        kg.add_entity_type('dog', 'canine')

    def add_predicate_type(kg, predicate_type, supertypes, arg0_types, arg1_types=None):
        """
        Add a concept to the KG that is interpretable as a predicate.

        `predicate_type` is the id of the added concept.

        `supertypes` should be a list of `predicate_type`'s types (a single string can
        be provided in the case of a single type relationship).

        `arg0_types` represents the conjunction of type(s) of the predicate's first argument.

        `arg1_types` (optionally) represents the conjunction of type(s) of the predicate's
        second argument. If arg1_types is None, then the predicate is a monopredicate.
        """
        kg.add_predicate_type('buy', ['event', 'economic_transaction'], 'person', 'purchasable')
        kg.add_predicate_type('leadership_role', 'social_role', 'agent_group', 'agent')

    def add_property(kg, type_, property_dict):
        """
        Add a set of properties to a concept in the kg.

        `type_` represents the type node that the properties are added to (should not be an instance).

        `property_dict` is a json-like dictionary describing the property attachments being added (see example).
        """
        kg.add_property('buy', {
            'use': 'currency',
            'source': 'vendor'
        })

    def add_entity_instance(kg, supertypes, properties, entity_instance=None):
        """
        Add an entity instance.

        `entity_instance` is the instance's identifier (optional).

        `supertypes` are the type(s) of `entity_instance`.

        `properties` is a json-like properties dictionary satisfying all `supertypes` properties.
        If not all supertype properties are satisfied, this method raises a `ValueError`.
        """
        pass

    def add_predicate_instance(kg, supertypes, properties):
        """
        Add an predicate instance.

        `supertypes` are the type(s) of `predicate_instance`.

        `properties` is a json-like properties dictionary satisfying all `supertypes` properties.
        If all supertype properties are not satisfied, this method raises a `ValueError`.

        `properties` should contain appropriate `arg0` and `arg1` entries to satisfy the argument
        structure of all the predicate's supertypes.
        """
        pass

    def add_conditions(kg, type_, conditions):
        """
        Add conditions that can be satisfied to infer a type relationship between some instance and a type.

        `type_` is the type-to-infer.

        `conditions` is a property dictionary representing the set of conditions that must be satisfied.
        Note that for predicate type inference, argument type satisfaction must hold by default.
        """
        pass

    def add_implication_rule(kg, conditions, properties):
        """
        Add an unnamed type with satisfaction conditions and a set of properties serving as a postcondition.

        `conditions` is a json-like property dictionary representing conditions.

        `properties` is a json-like property dictionary representing inferred knowledge.
        """
        pass

    def properties(kg, concept):
        """

        """
        pass

    def types(kg, concept):
        """

        """
        pass

    def subtypes(kg, concept):
        """

        """
        pass

    def instances(kg, type_):
        """

        """
        pass

    def implication_rules(kg, type_):
        """

        """
        pass

    def save(kg, json_filename):
        """

        """
        pass




