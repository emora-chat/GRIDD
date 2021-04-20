import requests, json
from os.path import join
from GRIDD.data_structures.concept_compiler import ConceptCompiler

def run_nlg(responses):
    try:  # use remote nlg module
        input_dict = {"expanded_response_predicates": [responses, None],
                      "conversationId": 'local'}
        response = requests.post('http://cobot-LoadB-1L3YPB9TGV71P-1610005595.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        response = response.json()
        if "performance" in response:
            del response["performance"]
            del response["error"]
        gen_results = json.loads(response["nlg_responses"])
        print(gen_results)
    except Exception as e:
        print('Failed! %s' % e)

if __name__ == '__main__':
    count = 0
    compiler = ConceptCompiler(predicates=None, types=None, namespace='wm')
    with open(join('GRIDD', 'scripts', 'test_nlg.txt'), 'r') as f:
        lines = []
        for line in f:
            if line.strip() == ';':
                print('# %d -'%count, end=' ')
                logicstring = ''.join(lines)
                cg = compiler.compile(logicstring)
                ((s,t,o,i),) = cg.predicates(predicate_type='assert')
                main_p = cg.predicate(o)
                supporting_p = [pred for pred in cg.predicates() if pred[3] != i]
                responses = [(main_p, supporting_p, 'nlg')]
                run_nlg(responses)
                lines = []
            else:
                lines.append(line)