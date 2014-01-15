# -*- coding: utf8 -*-
import collections
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
                "ft.clause_atom_relation",
                "sft.chapter,book,verse,verse_label",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    '''Counts the frequencies of the all clause patterns in the books of Genesis and the Psalms.
    Outputs the frequencies in a tab-delimited file.
    '''
    (msg, P, NN, F, X) = graftask.API()

    msg("Get the frequencies of the clause patterns...")

    out = graftask.add_output("clause_patterns.csv")

    books = ["Genesis", "Psalms"]
    clause_atom_relations = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    clause_atom_relations_total = {}
    bookname = None

    for i in NN():
        otype = F.shebanq_db_otype.v(i)
        if otype == "clause_atom" and bookname in books:
            car = F.shebanq_ft_clause_atom_relation.v(i)
            if not car not in clause_atom_relations[bookname]: 
                #clause_atom_relations[bookname].append(car)
                if car not in clause_atom_relations_total:
                    clause_atom_relations_total[car] = None
            clause_atom_relations[bookname][car] += 1
        elif otype == "book":
            bookname = F.shebanq_sft_book.v(i)

    clause_atom_relations_all = sorted(clause_atom_relations_total.keys())

    out.write("{:10}\t".format("CARnumber"))
    for bookname in books:
        out.write("{:10}\t".format(bookname))
    out.write("\n")
    for pattern in clause_atom_relations_all:
        out.write("{:10}\t".format(pattern))
        for bookname in books:
            if pattern in clause_atom_relations[bookname]:
                out.write("{:10}\t".format(clause_atom_relations[bookname][pattern]))
            else:
                out.write("{:10}\t".format("0"))
        out.write("\n")
