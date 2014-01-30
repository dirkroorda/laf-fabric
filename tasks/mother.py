# -*- coding: utf8 -*-
import sys
import collections

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "sft.book",
            ],
            "edge": [
                "mother.",
            ],
        },
    },
}

def task(processor):
    '''Lists the mothers of all clauses in the Psalms.

    Outputs the the id and type of every object that has
    a mother, and outputs the ids and object types of the mothers as well.
    '''
    API = processor.API()
    F = API['F']
    C = API['C']
    NN = API['NN']
    msg = API['msg']

    msg("Get the mothers...")

    out = processor.add_output("mothers.tsv")

    bookname = None
    found = 0
    mother_kind = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

    mother_c = C.shebanq_mother_['']

    for i in NN():
        otype = F.shebanq_db_otype.v(i)
        if i in other_c:
            for mother in mother_c[i]:
                found += 1
                motype = F.shebanq_db_otype.v(mother)
                mother_kind[otype][motype] += 1
                out.write("{}\t{}\t{}\t{}\n".format(otype, i, motype, mother))
        if otype == "book":
            bookname = F.shebanq_sft_book.v(i)
            sys.stderr.write("{} ({})\n".format(bookname, found))
    sys.stderr.write("Total {}\n".format(found))
    for source_type in sorted(mother_kind):
        for target_type in sorted(mother_kind[source_type]):
            print("{:<15} ==mother==> {:<15} : {:>10} x".format(source_type, target_type, mother_kind[source_type][target_type]))

