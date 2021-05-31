
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.span import Span

def get_ner_mentions(elit_results):
    """
    :param elit_results - dictionary of outputs from ELIT models

    Examples:
        barack obama -> ['PERSON', 0, 2, "barack obama"]
        barack obama's daughter -> ['PERSON', 0, 3, "barack obama 's"]
        the united states senate met this week -> ['GPE', 1, 3, 'United States'], ['ORG', 3, 4, 'Senate'], ['DATE', 5, 7, 'this week']
        a united states tourist was detained at the mexican border -> ['GPE', 1, 3, 'United States'], ['NORP', 8, 9, 'Mexican']
        Amazon's Alexa -> ['ORG', 2, 3, 'Amazon']
        the fourth of july is my favorite holiday -> ['DATE', 1, 4, '4th of July']
    """
    mentions = {}
    if len(elit_results["tok"]) > 0:
        token = elit_results["tok"][0]
        ner = elit_results["ner"]
        for ner_type, sidx, eidx, string in ner:
            cg = ConceptGraph(namespace='ner_')
            # todo - determine pos_tag of ner span
            # todo - if plural, add `group` type
            span = Span(string, sidx, eidx, token.sentence, token.turn, token.speaker, string, None)
            concept = cg.id_map().get()
            cg.add(concept, 'type', ner_type.lower()+'_ner')
            cg.add(concept, 'focus')
            cg.add(concept, 'center')
            cg.add(span)
            cg.features[span.to_string()]["span_data"] = span
            mentions[span.to_string()] = cg
    return mentions
