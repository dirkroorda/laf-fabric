# -*- coding: utf8 -*-
import sys
import collections

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "sft.book",
            ],
            "edge": [
                "mother.",
                "parents.",
            ],
        },
    },
    "other_edges": True,
}

def task(processor):
    '''Make an inventory of edges with respect to label, type of source node, type of target node.

    '''
    (msg, P, NN, F, C, X) = processor.API()

    msg("Get the edges...")

    bookname = None
    found = 0
    edge_kind = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: 0)))

    mother_c = C.shebanq_mother_['']
    parents_c = C.shebanq_parents_['']
    none_c = C._none_['']

    for i in NN():
        otype = F.shebanq_db_otype.v(i)
        for (kind, info) in (
            ('mother', mother_c),
            ('parents', parents_c),
            ('none', none_c),
        ):
            if i in info:
                for d in info[i]:
                    found += 1
                    dtype = F.shebanq_db_otype.v(d)
                    edge_kind[kind][otype][dtype] += 1
        if otype == "book":
            bookname = F.shebanq_sft_book.v(i)
            sys.stderr.write("{} ({})\n".format(bookname, found))
    sys.stderr.write("Total {}\n".format(found))

    for kind in ('mother', 'parents', 'self', 'none'):
        for source_type in sorted(edge_kind[kind]):
            for target_type in sorted(edge_kind[kind][source_type]):
                print("{:<15} =={:<7}==> {:<15} : {:>10} x".format(source_type, kind, target_type, edge_kind[kind][source_type][target_type]))

