
from structpy import specification


@specification
class TreeSpec:

    @specification.init
    def TREE(Tree, root, edges=None):
        tree = Tree(
            'animal',
            edges=[
                ('animal', 'amphibian'),
                ('animal', 'mammal', 'dominant'),
                ('mammal', 'human', 'apex'),
                ('mammal', 'cat', 'pet')
            ]
        )
        return tree

    def root(tree):
        assert tree.root() == 'animal'

    def has(tree, node, child=None, label=None):
        assert tree.has('animal')
        assert tree.has('mammal')
        assert tree.has('mammal', 'human')
        assert tree.has('mammal', 'human', 'apex')
        assert not tree.has('animal', 'cat')
        assert not tree.has('dog')

    def children(tree, node):
        assert set(tree.children('mammal')) == {'human', 'cat'}
        assert tree.children('mammal') == {'human': 'apex', 'cat': 'pet'}

    def parent(tree, node):
        assert tree.parent('cat') == 'mammal'

    def add(tree, parent, child, label=None):
        tree.add('animal', 'reptile')
        tree.add('animal', 'bird')
        tree.add('reptile', 'snake', 'typical')
        tree.add('reptile', 'crocodile', 'water')
        tree.add('bird', 'eagle')

        assert tree.has('bird', 'eagle')
        assert tree.children('reptile') == {'snake': 'typical', 'crocodile': 'water'}
        assert 'eagle' in tree.children('bird')




