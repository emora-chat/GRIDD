from GRIDD.data_structures.knowledge_parser import KnowledgeParser
from GRIDD.chatbot_server import ChatbotServer
import os

if __name__ == '__main__':
    print("John's aunt's illegally owned dog likes a bone")
    cg = KnowledgeParser.from_data('''
    dlb/like(d/dog(), b/bone())
    aunt(john, a/person())
    apd/possess(a, d)
    property(apd, illegal)
    assert(dlb)
    ''')
    cg.print_spanning_tree()

    print("\nJohn's aunt likes to buy a gift for him")
    cg = KnowledgeParser.from_data('''
    aunt(john, a/person())
    abg/buy(a, g/gift())
    indirect_obj(abg, john) 
    alb/like(a, abg)
    assert(alb)
    ''')
    cg.print_spanning_tree()

    print("\nShowering brings me joy but showering is annoying")
    cg = KnowledgeParser.from_data('''
    bs/shower(bot)
    sbj/bring(bs, joy)
    indirect_obj(sbj, bot)
    sba/be(bs, annoying)
    sbs/but(sbj, sba)
    assert(sbs)
    ''')
    cg.print_spanning_tree()

    print('\ninitializing nlu...')
    nlu_pipeline = ChatbotServer()
    nlu_pipeline.initialize_nlu(kb_files=[], device='cpu', local=False)
    print()
    utter = "I bought a house"
    while utter != 'q':
        cg = nlu_pipeline.run_nlu(utter)
        cg.print_spanning_tree()
        print()
        utter = input('>>> ').strip()