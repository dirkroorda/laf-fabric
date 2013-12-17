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
                "db.otype,monads,maxmonad,minmonad",
                "ft.noun_type,gender,part_of_speech",
                "sft.verse_label,chapter,book",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    '''An exercise in visualizing and distant reading.

    We count proper nouns and their relative frequencies, we record the gender of the nouns.
    We produce output in various tables.

    We also produce a projection of the complete bible text to a set of symbols,
    where verbs map to ♠, male proper nouns to ♂,
    female proper nouns to ♀, and unknown gender proper nouns to ⊙.
    All other words map to a dash. Moreover, the sentence, clause and phrase
    structure is also rendered by means of boundary characters.

    Returns:
        output.txt (file): the projection of the full text as described above
    Returns:
        stats_v_raw.txt (file): a table with per verse counts for words, verbs, proper nouns per gender
    Returns:
        stats_v_compact.txt (file): a table with per verse frequencies for verbs, and proper nouns
    Returns:
        stats_c_compact.txt (file): a table with per chapter frequencies for verbs, and proper nouns
    '''
    (msg, P, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")
    stats_v_raw = graftask.add_result("stats_v_raw.txt")
    stats_v_compact = graftask.add_result("stats_v_compact.txt")
    stats_c_compact = graftask.add_result("stats_c_compact.txt")

    type_map = collections.defaultdict(lambda: None, [
        ("chapter", 'Ch'),
        ("verse", 'V'),
        ("sentence", 'S'),
        ("clause", 'C'),
        ("phrase", 'P'),
        ("word", 'w'),
    ])
    otypes = ['Ch', 'V', 'S', 'C', 'P', 'w']
    watch = collections.defaultdict(lambda: {})
    start = {}
    cur_verse_label = ['','']
#   stats_v: counts in each verse: all words, verbs, proper nouns, masc proper nouns, proper nouns, proper nouns unknown gender
    stats_v = [None, 0, 0, 0, 0, 0]
    stats_c = [None, 0, 0, 0, 0, 0]

    def print_node(ob, obdata):
        (node, minm, maxm, monads) = obdata
        if ob == "w":
            if not watch:
                out.write("◘".format(monads))
            else:
                outchar = "─"
                stats_v[0] += 1
                stats_c[0] += 1
                p_o_s = F.shebanq_ft_part_of_speech.v(node)
                if p_o_s == "noun":
                    if F.shebanq_ft_noun_type.v(node) == "proper":
                        stats_v[2] += 1
                        stats_c[2] += 1
                        if F.shebanq_ft_gender.v(node) == "masculine":
                            outchar = "♂"
                            stats_v[3] += 1
                            stats_c[3] += 1
                        elif F.shebanq_ft_gender.v(node) == "feminine":
                            outchar = "♀"
                            stats_v[4] += 1
                            stats_c[4] += 1
                        elif F.shebanq_ft_gender.v(node) == "unknown":
                            outchar = "⊙"
                            stats_v[5] += 1
                            stats_c[5] += 1
                elif p_o_s == "verb":
                    outchar = "♠"
                    stats_v[1] += 1
                    stats_c[1] += 1
                out.write(outchar)
            if monads in watch:
                tofinish = watch[monads]
                for o in reversed(otypes):
                    if o in tofinish:
                        if o == 'C':
                            out.write("┤")
                        elif o == 'P':
                            if 'C' not in tofinish:
                                out.write("┼")
                        elif o != 'S':
                            out.write("{}»".format(o))
                del watch[monads]
        elif ob == "Ch":
            this_chapter_label = "{} {}".format(F.shebanq_sft_book.v(node), F.shebanq_sft_chapter.v(node))
            if stats_c[0] == None:
                stats_c_compact.write("\t".join(('chapter', 'word', 'verb_f', 'proper_f')) + "\n")
            else:
                n_proper = float(stats_c[0])
                stats_c_compact.write("{}\t{:.3g}\t{:.3g}\n".format(stats_c[0], 100 * stats_c[1]/n_proper, 100 * stats_c[2]/n_proper))
            for i in range(6):
                stats_c[i] = 0
            stats_c_compact.write(this_chapter_label + "\t")
        elif ob == "V":
            this_verse_label = F.shebanq_sft_verse_label.v(node).strip(" ")
            sys.stderr.write("\r{:<11}".format(this_verse_label))
            if stats_v[0] == None:
                stats_v_raw.write("\t".join(('verse', 'word', 'verb', 'proper', 'masc', 'fem', 'unknown')) + "\n")
                stats_v_compact.write("\t".join(('verse', 'word', 'verb_f', 'proper_f')) + "\n")
            else:
                n_proper = float(stats_v[0])
                stats_v_raw.write("\t".join([str(stat) for stat in stats_v]) + "\n")
                stats_v_compact.write("{}\t{:.3g}\t{:.3g}\n".format(stats_v[0], 100 * stats_v[1]/n_proper, 100 * stats_v[2]/n_proper))
            for i in range(6):
                stats_v[i] = 0
            stats_v_raw.write(this_verse_label + "\t")
            stats_v_compact.write(this_verse_label + "\t")
            cur_verse_label[0] = this_verse_label
            cur_verse_label[1] = this_verse_label
        elif ob == "S":
            out.write("\n{:<11} ".format(cur_verse_label[1]))
            cur_verse_label[1] = ''
            watch[maxm][ob] = None
        elif ob == "C":
            out.write("├")
            watch[maxm][ob] = None
        elif ob == "P":
            watch[maxm][ob] = None
        else:
            out.write("«{}".format(ob))
            watch[maxm][ob] = None

    lastmin = None
    lastmax = None

    for i in NN():
        otype = F.shebanq_db_otype.v(i)

        ob = type_map[otype]
        if ob == None:
            continue
        monads = F.shebanq_db_monads.v(i)
        minm = F.shebanq_db_minmonad.v(i)
        maxm = F.shebanq_db_maxmonad.v(i)
        if lastmin == minm and lastmax == maxm:
            start[ob] = (i, minm, maxm, monads)
        else:
            for o in otypes:
                if o in start:
                    print_node(o, start[o])
            start = {ob: (i, minm, maxm, monads)}
            lastmin = minm
            lastmax = maxm
    stats_v_raw.write("\t".join([str(stat) for stat in stats_v]) + "\n")
    n_proper = float(stats_v[0])
    stats_v_compact.write("{}\t{:.3g}\t{:.3g}\n".format(stats_v[0], stats_v[1]/n_proper, stats_v[2]/n_proper))
    n_proper = float(stats_c[0])
    stats_c_compact.write("{}\t{:.3g}\t{:.3g}\n".format(stats_c[0], stats_c[1]/n_proper, stats_c[2]/n_proper))
    for ob in otypes:
        if ob in start:
            print_node(ob, start[ob])

