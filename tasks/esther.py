# -*- coding: utf8 -*-
# MY CLONE #
import sys
import collections

precompute = {
    "plain": {},
    "memo": {},
    "assemble": {
        "only_nodes": "db:otype ft:part_of_speech,noun_type,lexeme_utf8 sft:book",
        "only_edges": '',
    },
    "assemble_all": {
    },
}

def task(graftask):
    (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

    target_book = "Esther"
    lexemes = collections.defaultdict(lambda:collections.defaultdict(lambda:0))

    out_all = graftask.add_result("lexemes_all.txt")
    out_esther = graftask.add_result("lexemes_esther.txt")

    ontarget = True
    book_name = None
    books = []
    words = collections.defaultdict(lambda: 0)

    for node in NN():
        this_type = Fi(node, Li["db"], Ni["otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            p_o_s = Fi(node, Li["ft"], Ni["part_of_speech"])
            if p_o_s == Vi["noun"]:
                noun_type = Fi(node, Li["ft"], Ni["noun_type"])
                if noun_type == Vi["common"]:
                    words[book_name] += 1
                    lexeme = Fr(node, Li["ft"], Ni["lexeme_utf8"])
                    lexemes[book_name][lexeme] += 1

        elif this_type == Vi["book"]:
            book_name = Fr(node, Li["sft"], Ni["book"])
            books.append(book_name)
            ontarget = Fi(node, Li["sft"], Ni["book"]) == Vi[target_book]
            if ontarget:
                sys.stderr.write(book_name)
            else:
                sys.stderr.write("*")
    sys.stderr.write("\n")

    for book in books:
        lexeme_number = 0
        out_all.write(u"{}\n".format(book))
        linfo = lexemes[book]
        for lexeme in sorted(linfo.keys()):
            lexeme_number += 1
            out_all.write(u"\t{}\t{}\t{}\n".format(lexeme_number, lexeme, linfo[lexeme]))

    lexeme_number = 0
    out_esther.write(u"\t{}\n".format("\t".join(books)))
    linfo = lexemes[target_book]
    for lexeme in sorted(linfo.keys()):
        lexeme_number += 1
        out_esther.write(u"{}\t{}\n".format(lexeme, "\t".join(["{:.3g}".format(1000 * float(lexemes[book][lexeme])/words[book]) for book in books])))
    print "{} lexemes".format(lexeme_number)

