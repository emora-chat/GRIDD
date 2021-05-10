
from structpy import specification


@specification
class IdMapSpec:
    """
    Bimap that maps a set of ids from one space to another
    with automatically generated conversions.
    """

    @specification.init
    def ID_MAP(IdMap, items=None, namespace=None, chars=None, start_index=0, condition=None, contains=None):
        """
        Create an `IdMap` object.
        """
        id_map = IdMap(
            items=['my', 'name', 'is', 'bob'],
            namespace='x',
            start_index=4,
            condition=lambda e: len(e) <= 3
        )
        return id_map

    def get(id_map, item=None):
        """

        """
        assert id_map.get('my') == 'x4'
        assert id_map.get('name') == 'name'
        assert id_map.get('is') == 'x5'
        assert id_map.get('bob') == 'x6'
        assert id_map.get('hello') == 'hello'
        assert id_map.get() == 'x7'
        assert id_map.get('sir') == 'x8'

    def identify(id_map, id):
        """

        """
        assert id_map.identify('x4') == 'my'
        assert id_map.identify('name') == 'name'

    def getitem(id_map, item):
        """

        """
        assert id_map['my'] == 'x4'

    def setitem(id_map, obj, id):
        """

        """
        id_map['my'] = 'x1'
        assert id_map['my'] == 'x1'
        id_map['exclamation'] = '!!!!!'
        assert id_map['exclamation'] == '!!!!!'

    def contains(id_map, obj):
        """
        __contains__ magic method
        """
        assert 'my' in id_map
        assert 'x5' not in id_map

    def reverse(id_map):
        """

        """
        assert id_map.reverse()['x8'] == 'sir'
        assert id_map.reverse()['name'] == 'name'