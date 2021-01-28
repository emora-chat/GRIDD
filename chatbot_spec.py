
from structpy import specification

import json


@specification
class ChatbotSpec:

    @specification.init
    def CHATBOT(Chatbot, knowledge_base):
        """
        Instantiate a chatbot. The constructor expects a variable number
        of knowledge graphs (providable via .kg file names, KnowledgeGraph objects
        or logic strings).
        """
        chatbot = Chatbot('data_structures/kg_files/framework_test.kg')
        return chatbot

    @specification.init
    def respond(Chatbot, user_utterance=None, dialogue_state=None):
        """
        Get a response from the chatbot given a `user_utterance` string.

        Providing no `user_utterance` prompts the chatbot to initiate
        or continue the dialogue.

        Returns a tuple of the form `(chatbot_response, dialogue_state)`
        where `chatbot_response` is a string and `dialogue_state` is some
        object used to track the dialogue state.

        When calling `.respond`, the `dialogue_state` of a previous call
        can be provided to resume the conversation from that point in the
        conversation.
        """
        chatbot = Chatbot('data_structures/kg_files/framework_test.kg')

        print('Chatbot cold start:')
        print(chatbot.respond()[0], '\n')

        print('Chatbot responds to "I feel okay, how are you?":')
        utt, ds = chatbot.respond("I feel okay, how are you?")
        print(utt)

        print('Loading previous point of conversation in new chatbot:')
        new_chatbot = Chatbot('data_structures/kg_files/framework_test.kg')
        print(new_chatbot.respond("I feel okay, how are you?", dialogue_state=ds)[0])

        return chatbot

    def save(chatbot):
        """
        Save the chatbot state to a json object for future load.
        """
        js = chatbot.save()
        with open('ds.json') as f:
            json.dump(js, f)

    def load(chatbot, dialogue_state):
        """
        Load the chatbot state from a json object or json string.
        """
        r1, s1 = chatbot.respond("I bought a new house.")
        with open('ds.json') as f:
            chatbot.load(f.read())
        r2, s2 = chatbot.respond("I bought a new house.")
        assert r1 == r2



