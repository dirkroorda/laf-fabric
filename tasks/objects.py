# -*- coding: utf8 -*-

precompute = {
    "plain": {},
    "memo": {},
    "assemble": {
        "only_nodes": "db:oid,otype,monads",
        "only_edges": '',
    },
    "assemble_all": {
    },
}

def task(graftask):
    (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    for i in NN():
        oid = Fr(i, Li["db"], Ni["oid"])
        otype = Fr(i, Li["db"], Ni["otype"])
        monads = Fr(i, Li["db"], Ni["monads"])
        out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
