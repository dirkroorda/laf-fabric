import collections
import functools
import array
from .lib import monad_set, object_rank

def node_order(API):
    API['fabric'].load_again({"features": ('otype monads', '')}, add=True)
    msg = API['msg']
    F = API['F']
    NN = API['NN']

    def before(a,b):
        sa = monad_set(F.monads.v(a))
        sb = monad_set(F.monads.v(b))
        oa = object_rank[F.otype.v(a)]
        ob = object_rank[F.otype.v(b)]
        if sa == sb: return 0 if oa == ob else -1 if oa < ob else 1
        if sa < sb: return 1
        if sa > sb: return -1
        am = min(sa - sb)
        bm = min(sb - sa)
        return -1 if am < bm else 1 if bm < am else None

    etcbckey = functools.cmp_to_key(before)
    nodes = sorted(NN(), key=etcbckey)
    return array.array('I', nodes)

def node_order_inv(API):
    make_array_inverse = API['make_array_inverse']
    data_items = API['data_items']
    return make_array_inverse(data_items['zG00(node_sort)'])

prepare = collections.OrderedDict((
    ('zG00(node_sort)', (node_order, __file__, True, 'etcbc')),
    ('zG00(node_sort_inv)', (node_order_inv, __file__, True, 'etcbc')),
))
