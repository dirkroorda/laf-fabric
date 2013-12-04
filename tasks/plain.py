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
                "ft.text,suffix",
                "sft.book",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    (msg, NN, F, X) = graftask.get_mappings()

    prim = graftask.env['source'] != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = graftask.add_result("output.txt")

    object_type = F.shebanq_db_otype.i('word') if prim else F.shebanq_db_otype.i('book')

    n_nodes = 0
    for i in NN(test=F.shebanq_db_otype.v, value=object_type):
        n_nodes += 1
        the_output = ''
        if prim:
            the_text = F.shebanq_ft_text.vr(i)
            the_suffix = F.shebanq_ft_suffix.vr(i)
            the_newline = "\n" if '׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_output = F.shebanq_sft_book.vr(i) + " "
        out.write(the_output)
