from GRIDD.chatbot import Chatbot
from os.path import join
from GRIDD.data_structures.working_memory import WorkingMemory
from globals import *
from GRIDD.scripts import extract_elit_rules_from_doc

if __name__ == '__main__':

    extract_elit_rules_from_doc.extract()

    kb = join('GRIDD', 'resources', KB_FOLDERNAME, 'kb')
    test_kb = join('GRIDD', 'resources', KB_FOLDERNAME, 'framework_test.kg')
    rules_dir = join('GRIDD', 'resources', KB_FOLDERNAME, 'rules')
    rules = [rules_dir]

    chatbot = Chatbot(kb, rules=rules, device='cuda:1')
    nlu = chatbot.pipeline['sentence_caser',
                     'elit_models', 'elit_dp',
                     'mention_bridge',
                     'merge_dp', 'merge_coref', 'merge_bridge']
    utterance = input('>>> ')
    while utterance != 'q':
        working_memory = nlu(utterance, chatbot.working_memory, None)
        # print(working_memory.ugly_print(exclusions={'var', 'object', 'entity', 'predicate', 'span'}))
        chatbot.working_memory = WorkingMemory(chatbot.knowledge_base)
        utterance = input('>>> ')