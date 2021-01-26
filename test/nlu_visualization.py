from chatbot import Chatbot
from os.path import join
from data_structures.working_memory import WorkingMemory

if __name__ == '__main__':
    chatbot = Chatbot(join('GRIDD', 'resources', 'kg_files', 'framework_test.kg'))
    nlu = chatbot.pipeline['sentence_caser',
                     'elit_models', 'elit_dp',
                     'mention_bridge',
                     'merge_dp', 'merge_bridge']
    utterance = input('>>> ')
    while utterance != 'q':
        working_memory = nlu(utterance, chatbot.working_memory)
        # working_memory.display_graph(exclusions={'var', 'is_type',
        #                                                  'object','entity','predicate',
        #                                                  'span'})
        chatbot.working_memory = WorkingMemory(chatbot.knowledge_base)
        utterance = input('>>> ')