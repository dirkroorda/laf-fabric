import collections
import array

def node_order(API):
    '''Creates a form based on the information passed when creating this object.'''
    msg = API['msg']
    F = API['F']
    NN = API['NN']
    object_rank = {
        'book': -4,
        'chapter': -3,
        'verse': -2,
        'half_verse': -1,
        'sentence': 1,
        'sentence_atom': 2,
        'clause': 3,
        'clause_atom': 4,
        'phrase': 5,
        'phrase_atom': 6,
        'subphrase': 7,
        'word': 8,
    }

# we should sort on minmonad and maxmonad instead of min anchor and max anchor.
# There are monads with have equal min and max anchor. 
# They got sorted wrong.

    def etcbckey(node):
        pass

    def hierarchy(node): return object_rank[F.shebanq_db_otype.v(node)]
    return array.array('I', NN(extrakey=hierarchy))

def node_order_inv(API):
    make_array_inverse = API['make_array_inverse']
    data_items = API['data_items']
    return make_array_inverse(data_items['zG00(node_sort)'])

prepare = collections.OrderedDict((
    ('zG00(node_sort)', (node_order, __file__, True, 'etcbc')),
    ('zG00(node_sort_inv)', (node_order_inv, __file__, True, 'etcbc')),
))
