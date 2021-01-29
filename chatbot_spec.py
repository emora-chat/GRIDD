
from structpy import specification

import json
from os.path import join
test_resource_file = join('GRIDD', 'resources', 'kg_files', 'framework_test.kg')


@specification
class ChatbotSpec:

    @specification.init
    def CHATBOT(Chatbot, knowledge_base):
        """
        Instantiate a chatbot. The constructor expects a variable number
        of knowledge graphs (providable via .kg file names, KnowledgeGraph objects
        or logic strings).
        """
        chatbot = Chatbot(test_resource_file)
        return chatbot

    @specification.init
    def respond(Chatbot, user_utterance=None, dialogue_state=None):
        """
        Get a response from the chatbot given a `user_utterance` string.
        Returns a string representing the chatbot response.

        Providing no `user_utterance` prompts the chatbot to initiate
        or continue the dialogue.

        When calling `.respond`, the `dialogue_state` of a `.save` call
        can be provided to resume the conversation from the save point.
        """
        chatbot = Chatbot(test_resource_file)

        print('Chatbot cold start:')
        print(chatbot.respond(), '\n')

        print('Chatbot responds to "I feel okay, how are you?":')
        utt = chatbot.respond("I feel okay, how are you?")
        print(utt)

        return chatbot

    def save(chatbot):
        """
        Save the chatbot state to a json object for future load.
        """
        js = chatbot.save()
        print(json.dumps(js, indent=2))
        with open('ds.json', 'w') as f:
            json.dump(js, f)

    def load(chatbot, dialogue_state):
        """
        Load the chatbot state from a json object or json string.
        """
        s1 = chatbot.respond("I bought a new house.")
        with open('ds.json') as f:
            chatbot.load(f.read())
        s2 = chatbot.respond("I bought a new house.")
        print(s1)
        print(s2)



