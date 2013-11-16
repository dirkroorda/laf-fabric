# -*- coding: utf8 -*-
import sys

features = {
    "nodes": "db:otype,monads ft:text,suffix sft:book,chapter,verse",
    "edges": '',
}

def task(graftask):
    (msg, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book_id = None
    the_book = None
    the_chapter = None
    the_verse = None
    ontarget = True
    for i in NN():
        this_type = Fi(i, Ni["db.otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            if ontarget:
                the_monads = Fr(i, Ni["db.monads"])
                the_text = Fr(i, Ni["ft.text"])
                the_suffix = Fr(i, Ni["ft.suffix"])
                out.write(the_monads + "_" + the_text + the_suffix)
        elif this_type == Vi["book"]:
            the_book_id = Fi(i, Ni["sft.book"])
            ontarget = the_book_id == Vi["Isaiah"]
            if ontarget:
                the_book = Fr(i, Ni["sft.book"])
                sys.stderr.write(the_book)
                out.write("\n{}".format(the_book))
            else:
                sys.stderr.write("*")
        elif this_type == Vi["chapter"]:
            if ontarget:
                the_chapter = Fr(i, Ni["sft.chapter"])
                out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == Vi["verse"]:
            if ontarget:
                the_verse = Fr(i, Ni["sft.verse"])
                out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
