from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.chatbot_server import ChatbotServer
import os

if __name__ == '__main__':

    print('\ninitializing nlu...')
    nlu_pipeline = ChatbotServer()
    nlu_pipeline.initialize_nlu(kb_files=[], device='cpu', local=True)
    print()
    utter = input('>>> ').strip()
    while utter != 'q':
        cg = nlu_pipeline.run_nlu(utter, display=False)
        cg.pull_expressions()
        print(cg.print_spanning_tree())
        print()
        utter = input('>>> ').strip()

    utters = [
        "I ain't bad",
        "You aren't bad",
        "You can't do that",
        "You can't've been serious",
        "You could've been hurt",
        "You couldn't have been hurt",
        "You didn't say that",
        "She doesn't know",
        "You don't know",
        "She hadn't known",
        "She hasn't gone",
        "You haven't gone",
        "He'd pay",
        "He'd've paid",
        "He's a good guy",
        "How'd you know",
        "How'll you buy that",
        "How's it going",
        "I'd've paid",
        "I'll've graduated",
        "I'm paying",
        "I'm good",
        "I've paid",
        "She isn't going",
        "It'd be fine",
        "It'll be fine",
        "It's fine",
        "Let's go",
        "You might've gone",
        "You must've gone",
        "You mustn't go",
        "She'd pay",
        "She'll pay",
        "She's good",
        "You should've paid",
        "You shouldn't have paid",
        "You shouldn't've paid",
        "So's she coming",
        "That's cool",
        "There'd be a fight",
        "There'd've been a fight",
        "There's hope",
        "They'd pay",
        "They'll pay",
        "They're happy",
        "They've paid",
        "You wanna go to the store",
        "She wasn't ready",
        "We'd better go",
        "We'd've gone",
        "We've paid",
        "You weren't lucky",
        "What'll happen now",
        "What're you doing",
        "What's happening",
        "What've you done",
        "When's she coming",
        "When've you ever finished that",
        "Where'd she go",
        "Where's she"
        "Where've you gone",
        "Who'll pay",
        "Who'll've finished by then",
        "Who's coming",
        "Who've finished",
        "Why's that",
        "Why've you said that",
        "You will've finished",
        "You won't finish",
        "You won't've finished",
        "You would've finished",
        "You wouldn't finish",
        "You wouldn't've finished",
        "Y'all should go",
        "Y'all're going",
        "Y'all've finished",
        "You'd go",
        "You'd've gone",
        "You'll go",
        "You'll've gone",
        "You're happy",
        "You've been happy"
    ]
    for utter in utters:
        cg = nlu_pipeline.run_nlu(utter, display=False)
        print()
        cg = nlu_pipeline.run_nlu(utter.replace("'",""), display=False)
        print()

    print("John's aunt's illegally owned dog likes a bone")
    cg = KnowledgeParser.from_data('''
    dlb/like(d/dog(), b/bone())
    aunt(john, a/person())
    apd/possess(a, d)
    property(apd, illegal)
    assert(dlb)
    ''')
    print(cg.print_spanning_tree())

    print("\nJohn's aunt likes to buy a gift for him")
    cg = KnowledgeParser.from_data('''
    aunt(john, a/person())
    abg/buy(a, g/gift())
    indirect_obj(abg, john) 
    alb/like(a, abg)
    assert(alb)
    ''')
    print(cg.print_spanning_tree())

    print("\nShowering brings me joy but showering is annoying")
    cg = KnowledgeParser.from_data('''
    bs/shower(bot)
    sbj/bring(bs, joy)
    indirect_obj(sbj, bot)
    sba/be(bs, annoying)
    sbs/but(sbj, sba)
    assert(sbs)
    ''')
    print(cg.print_spanning_tree())

