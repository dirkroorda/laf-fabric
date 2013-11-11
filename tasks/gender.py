# -*- coding: utf8 -*-
import collections
import sys

precompute = {
    "plain": {},
    "memo": {},
    "assemble": {
        "only_nodes": "db:otype ft:gender sft:verse_label,chapter,book",
        "only_edges": '',
    },
    "assemble_all": {
    },
}

def task(graftask):
    (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()
    stats_file = graftask.add_result("stats.txt")

    type_map = collections.defaultdict(lambda: None, [
        ("chapter", 'Ch'),
        ("word", 'w'),
    ])
    otypes = ['Ch', 'w']
#   stats: counts in each chapter: all words, masc words, fem words, ratio fem/masc
    stats = [None, 0, 0]

    cur_chapter = None
    for node in NN():
        otype = Fr(node, Li["db"], Ni["otype"])
        if not otype:
            continue
        ob = type_map[otype]
        if ob == None:
            continue
        if ob == "w":
            stats[0] += 1
            if Fi(node, Li["ft"], Ni["gender"]) == Vi["masculine"]:
                stats[1] += 1
            elif Fi(node, Li["ft"], Ni["gender"]) == Vi["feminine"]:
                stats[2] += 1
        elif ob == "Ch":
            this_chapter = "{} {}".format(Fr(node, Li["sft"], Ni["book"]), Fr(node, Li["sft"], Ni["chapter"]))
            sys.stderr.write("\r{:<15}".format(this_chapter))
            if stats[0] == None:
                stats_file.write("\t".join(('chapter', 'masc_f', 'fem_f', 'fem_masc_r')) + "\n")
            else:
                masc = float(stats[1])
                fem = float(stats[2])
                femmasc = 1 if not masc and not fem else 100 if not masc else (fem / masc)
                masc = 100 * masc / stats[0]
                fem = 100 * fem / stats[0]
                stats_file.write("{}\t{:.3g}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem, femmasc))
            for i in range(3):
                stats[i] = 0
            cur_chapter = this_chapter
    masc = float(stats[1])
    fem = float(stats[2])
    femmasc = 1 if not masc and not fem else 100 if not masc else fem / masc
    masc = 100 * masc / stats[0]
    fem = 100 * fem / stats[0]
    stats_file.write("{}\t{:.3g}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem, femmasc))


