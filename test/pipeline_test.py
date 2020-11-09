import pytest, random
from pipeline import Pipeline
from branch import Branch
from aggregator import Aggregator
from modules.module import Module

class A(Module):
    def run(self, input):
        return input + 'a'

class B(Module):
    def run(self, input):
        return input + 'b'

class C(Module):
    def run(self, input):
        return input + 'c'

class D(Module):
    def run(self, input):
        return input + 'd'

class One(Module):
    def run(self, input):
        return input + '1'

class Two(Module):
    def run(self, input):
        return input + '2'

class Three(Module):
    def run(self, input):
        return input + '3'


astr = A('astr')
bstr = B('bstr')
cstr = C('cstr')
dstr = D('dstr')

onestr = One('1str')
twostr = Two('2str')
threestr = Three('3str')

def test_pipeline_add():
    p = Pipeline('string builder')
    p.add_model(astr)
    p.add_model(bstr)
    p.add_model(cstr)
    p.add_model(dstr)
    assert p.model_names[0] == 'astr'
    assert p.model_names[1] == 'bstr'
    assert p.model_names[2] == 'cstr'
    assert p.model_names[3] == 'dstr'

def test_pipeline_insert():
    p = Pipeline('string builder')
    p.add_model(astr)
    p.add_model(bstr)
    p.insert_model_by_position(cstr, 0)
    assert p.model_names[0] == 'cstr'
    assert p.model_names[1] == 'astr'
    assert p.model_names[2] == 'bstr'
    p.insert_model_after('astr', dstr)
    assert p.model_names[0] == 'cstr'
    assert p.model_names[1] == 'astr'
    assert p.model_names[2] == 'dstr'
    assert p.model_names[3] == 'bstr'

def test_pipeline_extend():
    p = Pipeline('string builder')
    p.add_models([astr,cstr,dstr,bstr])
    assert p.model_names[0] == 'astr'
    assert p.model_names[1] == 'cstr'
    assert p.model_names[2] == 'dstr'
    assert p.model_names[3] == 'bstr'

def test_pipeline_display():
    p = Pipeline('string builder')
    p.add_models([astr,cstr,dstr,bstr])
    assert p.to_display() == '(astr -> cstr -> dstr -> bstr)'

def test_pipeline_run():
    p = Pipeline('string builder')
    p.add_models([astr,bstr,cstr,dstr])
    output = p.run('')
    assert output == 'abcd'

def test_two_pipelines():
    p1 = Pipeline('string builder 1')
    p1.add_models([astr,bstr,cstr,dstr])
    p2 = Pipeline('string builder 2')
    p2.add_models([dstr,cstr,bstr,astr])
    p = Pipeline('mega string builder')
    p.add_models([p1,p2])
    assert p.run('') == 'abcddcba'

##########################################################################

def test_branch_run():
    b = Branch('string builder')
    b.add_models([{'model': astr, 'weight': 1.0},
                  {'model': bstr, 'weight': 1.0},
                  {'model': cstr, 'weight': 1.0},
                  {'model': dstr, 'weight': 1.0}])
    outputs = b.run('')
    assert outputs['astr'] == 'a'
    assert outputs['bstr'] == 'b'
    assert outputs['cstr'] == 'c'
    assert outputs['dstr'] == 'd'

##########################################################################

class Random(Aggregator):
    def run(self, input):
        outputs = self.branch.run(input)
        selection = random.choice(list(outputs.items()))
        return selection[1]

class Maximum(Aggregator):
    def run(self, input):
        outputs = self.branch.run(input)
        models_by_weight = [(model_name,meta['weight'])
                            for model_name, meta in self.branch.models.items()]
        max_tuple = max(models_by_weight, key=lambda x: x[1])
        selection = outputs[max_tuple[0]]
        return selection

def test_pipeline_and_branch_using_naive_aggreg_run():
    p = Pipeline('multicomponent')
    b = Branch('numbers')
    b.add_models([{'model': onestr, 'weight': 1.0},
                  {'model': twostr, 'weight': 1.0},
                  {'model': threestr, 'weight': 1.0}])
    getrand = Random('get random', b)
    p.add_models([astr,bstr,getrand,cstr,dstr])
    output = p.run('')
    assert output[0] == 'a'
    assert output[1] == 'b'
    assert output[2] in '123'
    assert output[3] == 'c'
    assert output[4] == 'd'

def test_pipeline_and_branch_using_meta_info_aggreg_run():
    p = Pipeline('multicomponent')
    b = Branch('numbers')
    b.add_models([{'model': onestr, 'weight': 1.0},
                  {'model': twostr, 'weight': 1.0},
                  {'model': threestr, 'weight': 2.0}])
    getmax = Maximum('get max', b)
    p.add_models([astr,bstr,getmax,cstr,dstr])
    output = p.run('')
    assert output[0] == 'a'
    assert output[1] == 'b'
    assert output[2] == '3'
    assert output[3] == 'c'
    assert output[4] == 'd'








