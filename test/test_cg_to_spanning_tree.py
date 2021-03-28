# @specification.init
# def to_spanning_tree(ConceptGraph):
#
#     cg = ConceptGraph(predicates=[
#         ('d', 'type', 'dog', 'dtd'),
#         ('b', 'type', 'bone', 'btb'),
#         ('a', 'type', 'person', 'atp'),
#         ('sally', 'buy', 'b', 'sbb'),
#         ('d', 'like', 'sbb', 'dlb'),
#         ('dlb', 'degree', 'really', 'ddr'),
#         ('john', 'aunt', 'a', 'jaa'),
#         ('a', 'possess', 'd', 'apd'),
#         ('apd', 'property', 'illegal', 'api'),
#         ('"dog"', 'expr', 'dog'),
#         ('"person"', 'expr', 'person'),
#         ('"bone"', 'expr', 'bone'),
#         ('"buy"', 'expr', 'buy'),
#         ('"like"', 'expr', 'like'),
#         ('"degree"', 'expr', 'degree'),
#         ('"really"', 'expr', 'really'),
#         ('"aunt"', 'expr', 'aunt'),
#         ('"possess"', 'expr', 'possess'),
#         ('"property"', 'expr', 'property'),
#         ('"illegal"', 'expr', 'illegal'),
#         ('"john"', 'expr', 'john'),
#         ('"sally"', 'expr', 'sally'),
#         ('dlb', 'assert')
#     ])
#     root = SpanningNode('__root__')
#     like = SpanningNode('dlb', 'like')
#     d = SpanningNode('d')
#     dog = SpanningNode('dog')
#     dtd = SpanningNode('dtd', 'type')
#     b = SpanningNode('b')
#     bone = SpanningNode('bone')
#     btb = SpanningNode('btb', 'type')
#     buy = SpanningNode('sbb', 'buy')
#     john = SpanningNode('john')
#     sally = SpanningNode('sally')
#     degree = SpanningNode('ddr', 'degree')
#     really = SpanningNode('really')
#     rpossess = SpanningNode('apd', 'possess', 'r')
#     a = SpanningNode('a')
#     person = SpanningNode('person')
#     atp = SpanningNode('atp')
#     raunt = SpanningNode('jaa', 'aunt', 'r')
#     property = SpanningNode('api', 'property')
#     illegal = SpanningNode('illegal')
#
#     root.children['link'] = [like]
#     like.children['arg0'] = [d]
#     like.children['arg1'] = [buy]
#     like.children['link'] = [degree]
#     d.children['link'] = [rpossess, dtd]
#     buy.children['arg0'] = [sally]
#     buy.children['arg1'] = [b]
#     b.children['link'] = [btb]
#     btb.children['arg1'] = [bone]
#     degree.children['arg1'] = [really]
#     rpossess.children['arg1'] = [a]
#     rpossess.children['link'] = [property]
#     dtd.children['arg1'] = [dog]
#     a.children['link'] = [raunt, atp]
#     atp.children['arg1'] = [person]
#     raunt.children['arg1'] = [john]
#     property.children['arg1'] = [illegal]
#
#     s = time.time()
#     span_tree_root = cg.to_spanning_tree()
#     # print('to spanning tree: %.5f sec'%(time.time()-s))
#     assert root.equal(span_tree_root)
#
#     s = time.time()
#     # print(cg.print_spanning_tree())
#     # print('print spanning tree: %.5f sec'%(time.time()-s))
#
#     cg = ConceptGraph(predicates=[
#         ('d', 'type', 'dog', 'dtd'),
#         ('b', 'type', 'bone', 'btb'),
#         ('a', 'type', 'person', 'atp'),
#         ('john', 'buy', 'b', 'sbb'),
#         ('d', 'like', 'sbb', 'dlb'),
#         ('john', 'aunt', 'a', 'jaa'),
#         ('a', 'possess', 'd', 'apd'),
#         ('"dog"', 'expr', 'dog'),
#         ('"person"', 'expr', 'person'),
#         ('"bone"', 'expr', 'bone'),
#         ('"buy"', 'expr', 'buy'),
#         ('"like"', 'expr', 'like'),
#         ('"aunt"', 'expr', 'aunt'),
#         ('"possess"', 'expr', 'possess'),
#         ('"john"', 'expr', 'john'),
#         ('"sally"', 'expr', 'sally'),
#         ('dlb', 'assert')
#     ])
#     # print(cg.print_spanning_tree())