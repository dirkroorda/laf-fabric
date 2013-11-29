# -*- coding: utf8 -*-
import sys

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "node": "db:otype ft:text,suffix sft:book,chapter,verse",
        "edge": '',
    }
}

def task(graftask):
    (msg, Vi, Vr, NN, NNFV, FN, FE, XNi, XNr, XEi, XEr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book = None
    the_chapter = None
    the_verse = None
    for i in NN():
        this_type = FN(i, "db.otype")
        if not this_type:
            continue
        if this_type == Vi["word"]:
            the_text = Vr[FN(i, "ft.text")]
            the_suffix = Vr[FN(i, "ft.suffix")]
            out.write(the_text + the_suffix)
        elif this_type == Vi["book"]:
            the_book = Vr[FN(i, "sft.book")]
            sys.stderr.write("\r{:>6} {:<30}".format(i, the_book)) 
            out.write("\n{}".format(the_book))
        elif this_type == Vi["chapter"]:
            the_chapter = Vr[FN(i, "sft.chapter")]
            out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == Vi["verse"]:
            the_verse = Vr[FN(i, "sft.verse")]
            out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
