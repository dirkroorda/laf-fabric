# -*- coding: utf8 -*-

import sys

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "node": "db:otype ft:text,suffix sft:book",
        "edge": '',
    }
}

def task(graftask):
    (msg, Vi, Vr, NN, NNFV, FN, FE, XNi, XNr, XEi, XEr) = graftask.get_mappings()

    prim = graftask.env['source'] != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = graftask.add_result("output.txt")

    object_type = Vi["word"] if prim else Vi["book"]
    n_nodes = 0
    for i in NNFV("db.otype", object_type):
        n_nodes += 1
        the_output = ''
        if prim:
            the_text = Vr[FN(i, "ft.text")]
            the_suffix = Vr[FN(i, "ft.suffix")]
            the_newline = "\n" if '׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_book = Vr[FN(i, "sft.book")]
            the_output = the_book + " "
        out.write(the_output)
