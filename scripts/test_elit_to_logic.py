from os.path import join
from GRIDD.intcore_chatbot import Chatbot
from GRIDD.utilities.utilities import spanning_tree_string_of

copula_examples = [
    "The weather is horrible",
    "That car looks fast",
    "The stew smells good",
    "I do feel foolish",
    "I do feel like a fool",
    "She became a racehorse trainer",
    "It's getting late",
    "He looks intelligent",
    "That sounds right",
    "He turned into a glutton",
    "I am happy",
    "I am a doctor",
    "I am in a house",
    "I am under my bed",
    "You are from Georgia",
    "He was proud of her",
    "I am scared of the dark"
]

prepositions = [
    "I bought a house in London",
    "The weather in Georgia is nice",
    "I am in a play",
    "We are in agreement",
    "The entrance of Kroger was dirty",
    "I am happy by the water",

]

passive = [
    "I am inspired by you",
    "The dog was eaten by the bear",
    "Bananas are adored by monkeys",
    "Was I chosen",
    "Was the dog found",
    "Was the bear chased by a hunter"
]

bad_nlu_examples = [
    "I am inspired because of you",
    "I bought a house when I was sad",
    "I enjoy alcohol and being in nature"
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
        print()
        s = spanning_tree_string_of(chatbot.dialogue_intcore.working_memory)
        if len([line for line in s.split('\n') if not line.startswith('\t') and line.strip() != '']) > 1:
            print('** UNHANDLED **')
        print(s)
        print()

if __name__ == '__main__':
    run(passive)