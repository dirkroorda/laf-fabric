# -*- coding: utf8 -*-
import sys
import collections

features = {
    "node": "db:otype ft:part_of_speech,noun_type,lexeme_utf8 sft:book",
    "edge": '',
}

def task(graftask):
    '''Collect frequency data of common nouns in Esther per bible book.

    This is part of reproducing results in Martijn Naaijer's thesis.

    We count lexemes of common nouns throughout the bible
    and we deliver a table of counts of all lexemes and a table of
    frequencies of lexemes restricted to the common nouns of Esther.

    When counting lexemes, we count the occurrences of *words*.
    If *word1* and *word2* have *n1* and *n2* occurrences, and both
    have the same *lexeme*, then *lexeme* has *n1* plus *n2*
    occurrences.

    When we compute frequencies, we divide lexeme occurrences as defined
    above by the total number of word occurrences.

    Returns:
        lexemes_all.txt (file): a table of all lexemes, ordered by bible book, with the number
        of occurrences in that bible book.

    Returns:
        lexemes_esther.txt (file): a matrix with as rows the lexemes of
        common nouns in Esther and as columns the books of the bible.
        A cell contain the frequency of that lexeme in that book multiplied by 1000 
    '''
    (msg, NNi, NNr, NEi, NEr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

    target_book = "Esther"
    lexemes = collections.defaultdict(lambda:collections.defaultdict(lambda:0))

    out_all = graftask.add_result("lexemes_all.txt")
    out_esther = graftask.add_result("lexemes_esther.txt")

    ontarget = True
    book_name = None
    books = []
    words = collections.defaultdict(lambda: 0)

    for node in NN():
        this_type = FNi(node, NNi["db.otype"])
        if not this_type:
            continue
        if this_type == Vi["word"]:
            p_o_s = FNi(node, NNi["ft.part_of_speech"])
            if p_o_s == Vi["noun"]:
                noun_type = FNi(node, NNi["ft.noun_type"])
                if noun_type == Vi["common"]:
                    words[book_name] += 1
                    lexeme = FNr(node, NNi["ft.lexeme_utf8"])
                    lexemes[book_name][lexeme] += 1

        elif this_type == Vi["book"]:
            book_name = FNr(node, NNi["sft.book"])
            books.append(book_name)
            ontarget = FNi(node, NNi["sft.book"]) == Vi[target_book]
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

