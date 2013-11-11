# -*- coding: utf8 -*-
import sys

precompute = {
    "plain": {},
    "memo": {},
    "assemble": {
        "only_nodes": "db:otype ft:text,suffix sft:book,chapter,verse",
        "only_edges": '',
    },
    "assemble_all": {
    },
}

def task(graftask):
    (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book = None
    the_chapter = None
    the_verse = None
    for i in NN():
        this_type = Fi(i, Li["db"], Ni["otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            the_text = Fr(i, Li["ft"], Ni["text"])
            the_suffix = Fr(i, Li["ft"], Ni["suffix"])
            out.write(the_text + the_suffix)
        elif this_type == Vi["book"]:
            the_book = Fr(i, Li["sft"], Ni["book"])
            sys.stderr.write("\r{:>6} {:<30}".format(i, the_book)) 
            out.write("\n{}".format(the_book))
        elif this_type == Vi["chapter"]:
            the_chapter = Fr(i, Li["sft"], Ni["chapter"])
            out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == Vi["verse"]:
            the_verse = Fr(i, Li["sft"], Ni["verse"])
            out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
