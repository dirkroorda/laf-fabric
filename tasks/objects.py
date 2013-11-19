# -*- coding: utf8 -*-

features = {
    "node": "db:oid,otype,monads",
    "edge": '',
}

def task(graftask):
    (msg, NNi, NNr, NEi, NEr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = FNr(i, NNi["db.oid"])
        otype = FNr(i, NNi["db.otype"])
        monads = FNr(i, NNi["db.monads"])
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
