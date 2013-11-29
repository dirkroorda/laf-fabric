# -*- coding: utf8 -*-

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "node": "db:oid,otype,monads",
        "edge": '',
    }
}

def task(graftask):
    (msg, Vi, Vr, NN, NNFV, FN, FE, XNi, XNr, XEi, XEr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = Vr[FN(i, "db.oid")]
        otype = Vr[FN(i, "db.otype")]
        monads = Vr[FN(i, "db.monads")]
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
