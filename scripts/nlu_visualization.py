from GRIDD.chatbot import Chatbot
from os.path import join
from GRIDD.data_structures.working_memory import WorkingMemory
import GRIDD.globals as globals
from GRIDD.scripts import extract_elit_rules_from_doc

if __name__ == '__main__':
    globals.DEBUG = True

    extract_elit_rules_from_doc.extract()

    chatbot = Chatbot(join('GRIDD', 'resources', 'kg_files', 'framework_test.kg'))
    nlu = chatbot.pipeline['sentence_caser',
                     'elit_models', 'elit_dp',
                     'mention_bridge',
                     'merge_dp', 'merge_bridge']
    utterance = input('>>> ')
    while utterance != 'q':
        working_memory = nlu(utterance, chatbot.working_memory, None, None)[1]
        # print(working_memory.ugly_print(exclusions={'var', 'is_type', 'object', 'entity', 'predicate', 'span'}))
        chatbot.working_memory = WorkingMemory(chatbot.knowledge_base)
        utterance = input('>>> ')