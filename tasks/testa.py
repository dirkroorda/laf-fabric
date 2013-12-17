# -*- coding: utf8 -*-

import sys

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
            ],
        },
        "dirk": {
            "node": [
                "part.comment",
            ],
            "edge": [
                "part.comment",
            ],
        },
    },
}

def task(graftask):
    '''Produces an annotated list of the books in the bible.

    The annotations come from an extra annotation package, that annotates some of the books
    in a rather trivial way. 
    If there is no comment, the ooutput will say "*no comment*
    '''
    (msg, NN, F, X) = graftask.get_mappings()

    msg("Get the books ...")

    out = graftask.add_result("output.txt")

    for i in NN(test=F.shebanq_db_otype.v, value='book'):
        dirk_says = F.dirk_part_comment.v(i)
        the_output = "{} Dirk: {}".format(F.shebanq_sft_book.v(i), dirk_says if dirk_says else 'no comment')
        msg(the_output)
        out.write(the_output)
