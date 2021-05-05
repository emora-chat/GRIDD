
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.intelligence_core import IntelligenceCore

ls = '''

[pet,person,predicate]=(object)
[request,possess,property]=(predicate)
user=person()
emora=person()
possess(user, X/pet())
i:<i/property(X)>
request(emora, i)
;

i/property(X/pet())
possess(user, X)
request(emora, i)
-> q_pet_property ->
$ What is your X like ? $
;
'''

ic = IntelligenceCore(ls)

matches = ic.nlg_inference_engine.infer(ic.knowledge_base)

print(matches)