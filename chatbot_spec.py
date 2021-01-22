
from structpy import specification


@specification
class ChatbotSpec:

    @specification.init
    def CHATBOT(Chatbot, knowledge_base):
        """

        """
        chatbot = Chatbot('data_structures/kg_files/framework_test.kg')
        return chatbot

