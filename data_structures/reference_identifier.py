from GRIDD.data_structures.reference_identifier_spec import ReferenceIdentifierSpec

class ReferenceIdentifier:

    def __init__(self, reference_by_rule):
        self.reference_by_rule = reference_by_rule

    def identify(self, rule, span, data_dict):
        if rule in self.reference_by_rule:
            return self.reference_by_rule[rule](span, data_dict)
        return None

if __name__ == '__main__':
    print(ReferenceIdentifierSpec.verify(ReferenceIdentifier))
