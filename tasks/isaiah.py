# -*- coding: utf8 -*-
import sys

features = {
    "node": "db:otype,monads ft:text,suffix sft:book,chapter,verse",
    "edge": '',
}

def task(graftask):
    (msg, NNi, NNr, NEi, NEr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book_id = None
    the_book = None
    the_chapter = None
    the_verse = None
    ontarget = True
    for i in NN():
        this_type = FNi(i, NNi["db.otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            if ontarget:
                the_monads = FNr(i, NNi["db.monads"])
                the_text = FNr(i, NNi["ft.text"])
                the_suffix = FNr(i, NNi["ft.suffix"])
                out.write(the_monads + "_" + the_text + the_suffix)
        elif this_type == Vi["book"]:
            the_book_id = FNi(i, NNi["sft.book"])
            ontarget = the_book_id == Vi["Isaiah"]
            if ontarget:
                the_book = FNr(i, NNi["sft.book"])
                sys.stderr.write(the_book)
                out.write("\n{}".format(the_book))
            else:
                sys.stderr.write("*")
        elif this_type == Vi["chapter"]:
            if ontarget:
                the_chapter = FNr(i, NNi["sft.chapter"])
                out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == Vi["verse"]:
            if ontarget:
                the_verse = FNr(i, NNi["sft.verse"])
                out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
