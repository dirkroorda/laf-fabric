# -*- coding: utf8 -*-

features = {
    "nodes": "db:oid,otype,monads",
    "edges": '',
}

def task(graftask):
    (msg, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = Fr(i, Ni["db.oid"])
        otype = Fr(i, Ni["db.otype"])
        monads = Fr(i, Ni["db.monads"])
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
