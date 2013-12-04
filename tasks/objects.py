# -*- coding: utf8 -*-

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.oid,otype,monads",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    (msg, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = F.shebanq_db_oid.vr(i)
        otype = F.shebanq_db_otype.vr(i)
        monads = F.shebanq_db_monads.vr(i)
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
