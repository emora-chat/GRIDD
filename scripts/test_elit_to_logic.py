from os.path import join
from GRIDD.intcore_chatbot import Chatbot
from GRIDD.utilities.utilities import spanning_tree_string_of

copula_examples = [
    "The weather is horrible.",
    "That car looks fast.",
    "The stew smells good.",
    "I do feel foolish.",
    "I do feel like a fool.",
    "She became a racehorse trainer.",
    "It's getting late.",
    "He looks intelligent.",
    "That sounds right.",
    "He turned into a glutton.",
    "I am happy.",
    "I am a doctor.",
    "I am in a house.",
    "I am under my bed.",
    "You are from Georgia."
]

bad_nlu_examples = [
    "I bought a house when I was sad.",
    "I enjoy alcohol and being in nature."
]

def run(utterances):
    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]

    chatbot = Chatbot(*kb, inference_rules=rules, starting_wm=None)

    for utter in utterances:
        print(utter)
        chatbot.run_nlu(utter, debug=False)
        print(spanning_tree_string_of(chatbot.dialogue_intcore.working_memory))
        print()

if __name__ == '__main__':
    run(copula_examples)