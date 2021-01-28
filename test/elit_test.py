import pytest
from GRIDD.modules.elit_models import ElitModels

@pytest.fixture
def elitmodels():
    return ElitModels()

def test_svo_simple(elitmodels):
    sentence = 'I bought a house'
    tok, pos, dp = elitmodels(sentence)
    assert dp == [[1,'nsbj'],[-1,'root'],[3,'det'],[1,'obj']]

def test_sv_simple(elitmodels):
    sentence = 'I walked'
    tok, pos, dp = elitmodels(sentence)
    assert dp == [[1, 'nsbj'], [-1, 'root']]

def test_slvo_simple(elitmodels):
    sentence = 'I made a call to you'
    tok, pos, dp = elitmodels(sentence)
    assert dp == [[3, 'nsbj'], [3,'lv'], [3,'det'], [-1, 'root'], [5,'case'], [3,'obj']]











