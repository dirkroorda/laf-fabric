# -*- coding: utf8 -*-
import collections
import sys

features = {
    "node": "db:otype ft:gender sft:verse_label,chapter,book",
    "edge": '',
}

def task(graftask):
    (msg, Ni, Nr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()
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
        otype = FNr(node, Ni["db.otype"])
        if not otype:
            continue
        ob = type_map[otype]
        if ob == None:
            continue
        if ob == "w":
            stats[0] += 1
            if FNi(node, Ni["ft.gender"]) == Vi["masculine"]:
                stats[1] += 1
            elif FNi(node, Ni["ft.gender"]) == Vi["feminine"]:
                stats[2] += 1
        elif ob == "Ch":
            this_chapter = "{} {}".format(FNr(node, Ni["sft.book"]), FNr(node, Ni["sft.chapter"]))
            sys.stderr.write("\r{:<15}".format(this_chapter))
            if stats[0] == None:
                stats_file.write("\t".join(('chapter', 'masc_f', 'fem_f', 'fem_masc_r')) + "\n")
            else:
                total = float(stats[0])
                masc = float(stats[1])
                fem = float(stats[2])
                femmasc = 1 if (not masc and not fem) else 100 if not masc else (fem / masc)
                masc = 0 if not total else 100 * masc / total
                fem = 0 if not total else 100 * fem / total
                stats_file.write("{}\t{:.3g}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem, femmasc))
            for i in range(3):
                stats[i] = 0
            cur_chapter = this_chapter
    total = float(stats[0])
    masc = float(stats[1])
    fem = float(stats[2])
    femmasc = 1 if not masc and not fem else 100 if not masc else fem / masc
    masc = 0 if not total else 100 * masc / total
    fem = 0 if not total else 100 * fem / total
    stats_file.write("{}\t{:.3g}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem, femmasc))


