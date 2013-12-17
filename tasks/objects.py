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
    '''Produces a list of all WIVU objects with their types, ids and
    *monads* (words) they contain.
    '''
    (msg, P, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = F.shebanq_db_oid.v(i)
        otype = F.shebanq_db_otype.v(i)
        monads = F.shebanq_db_monads.v(i)
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
