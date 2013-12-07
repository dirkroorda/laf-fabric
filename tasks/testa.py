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
                "part.this_is",
            ],
            "edge": [
                "part.this_is",
            ],
        },
    },
}

def task(graftask):
    '''Produces the plain text of the Hebrew Bible, in fact the Biblia Hebraica Stuttgartensia version.

    No book, chapter, verse marks. Newlines for each verse.
    The outcome should be identical to the primary data file in the original LAF resource.

    This is a handy check on all the data transformations involved. If the output of this task
    is not byte for byte equal to the primary data, something seriously wrong with the workbench!
    '''
    (msg, NN, F, X) = graftask.get_mappings()

    msg("Get the books ...")

    out = graftask.add_result("output.txt")

    print("XXX {}".format(F.shebanq_db_otype))

    for i in NN(test=F.shebanq_db_otype.v, value='book'):
        dirk_says = F.dirk_part_this_is.v(i)
        the_output = "{} Dirk: {}".format(F.shebanq_sft_book.v(i), dirk_says if dirk_says else 'no comment')
        msg(the_output)
        out.write(the_output)
