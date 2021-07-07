from os.path import join
from GRIDD.intcore_chatbot import Chatbot
from globals import *
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

modals = [
    "I should wake up",
    "I must score well",
    "Should I dye my hair",
    "Could you tell me more"
]

adv = [
    "I go home",
    "I ran quickly",
    "I bought a house yesterday",
    "I bought milk when I was hungry",
    "You came to see me",
    "I came to swim"
]

nested = [
    "I like to swim",
    "I came to swim",
    "I like being happy",
    "I like being in Georgia"
]

questions = [
    "What is your name",
    "What name is yours",
    "What is her dog's color",
    "What is the color of her dog",
    "What color is her dog",
    "What is your job",
    "What animal is in trouble"
]

negation = [
    'They are not studying',
    'They never study',
    "They no longer study"
]

bad_nlu_examples = [
    "You came to see me",
    "I came to swim",
    "I enjoy alcohol and being in nature",
    "I bought a house where I work",
    "I am inspired because of you",
    "The color of my car is red",
]

def run(utterances):
    kb_dir = join('GRIDD', 'resources', KB_FOLDERNAME, 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', KB_FOLDERNAME, 'rules')
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
    run(questions)