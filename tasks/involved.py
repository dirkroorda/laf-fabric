# -*- coding: utf8 -*-
import sys

features = {
    "node": "db:otype ft:text,suffix sft:book,chapter,verse",
    "edge": '',
}

def task(graftask):
    (msg, NNi, NNr, NEi, NEr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book = None
    the_chapter = None
    the_verse = None
    for i in NN():
        this_type = FNi(i, NNi["db.otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            the_text = FNr(i, NNi["ft.text"])
            the_suffix = FNr(i, NNi["ft.suffix"])
            out.write(the_text + the_suffix)
        elif this_type == Vi["book"]:
            the_book = FNr(i, NNi["sft.book"])
            sys.stderr.write("\r{:>6} {:<30}".format(i, the_book)) 
            out.write("\n{}".format(the_book))
        elif this_type == Vi["chapter"]:
            the_chapter = FNr(i, NNi["sft.chapter"])
            out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == Vi["verse"]:
            the_verse = FNr(i, NNi["sft.verse"])
            out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
