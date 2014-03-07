import sys
import collections
import array

def node_order(API):
    '''Creates a form based on the information passed when creating this object.
    '''
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

    def hierarchy(node):
        return object_rank[F.shebanq_db_otype.v(node)]

    return array.array('I', NN(extrakey=hierarchy))

def check(API):
    API['prep'](node_order, 'node_resorted', __file__)
