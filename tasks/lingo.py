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
                "ft.gender,part_of_speech",
                "sft.verse_label",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    '''Crude visualization of the syntactic structure of the text.

    Shows the linguistic objects in their actual embedding.
    Replaces each word by a dot.

    Verbs are represented with a spade sign (♠), nouns by (♂), (♀), (?) depending on their gender.

    Words that happen to be outside any syntactic container are marked as (◘).

    .. note::
        The WIVU data does not have an explicit hierarchy, there is no defined tree structure.
        Linguistic objects such as sentences, clauses and phrases may lay embedded in each other, but if a
        sentence is co-extensial with a clause (having exactly the same *monads* or words), there is
        nothing in the data that specifies that the clause is contained in the sentence.
    '''
    (msg, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    type_map = collections.defaultdict(lambda: None, [
        ("verse", 'V'),
        ("sentence", 'S'),
        ("sentence_atom", 's'),
        ("clause", 'C'),
        ("clause_atom", 'c'),
        ("phrase", 'P'),
        ("phrase_atom", 'p'),
        ("subphrase", 'q'),
        ("word", 'w'),
    ])
    otypes = ['V', 'S', 's', 'C', 'c', 'P', 'p', 'q', 'w']

    watch = collections.defaultdict(lambda: {})
    start = {}
    cur_verse_label = ['','']

    def print_node(ob, obdata):
        (node, minm, maxm, monads) = obdata
        if ob == "w":
            if not watch:
                out.write("◘".format(monads))
            else:
                outchar = "."
                if F.shebanq_ft_part_of_speech.v(node) == "noun":
                    if F.shebanq_ft_gender.v(node) == "masculine":
                        outchar = "♂"
                    elif F.shebanq_ft_gender.v(node) == "feminine":
                        outchar = "♀"
                    elif F.shebanq_ft_gender.v(node) == "unknown":
                        outchar = "?"
                if F.shebanq_ft_part_of_speech.v(node) == "verb":
                    outchar = "♠"
                out.write(outchar)
            if monads in watch:
                tofinish = watch[monads]
                for o in reversed(otypes):
                    if o in tofinish:
                        out.write("{})".format(o))
                del watch[monads]
        elif ob == "V":
            this_verse_label = F.shebanq_sft_verse_label.v(node)
            cur_verse_label[0] = this_verse_label
            cur_verse_label[1] = this_verse_label
        elif ob == "S":
            out.write("\n{:<11}{{{:>6}-{:>6}}} ".format(cur_verse_label[1], minm, maxm))
            cur_verse_label[1] = ''
            sys.stderr.write("\r{:>6}-{:>6}".format(minm, maxm))
            out.write("({}".format(ob))
            watch[maxm][ob] = None
        else:
            out.write("({}".format(ob))
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
    for ob in otypes:
        if ob in start:
            print_node(ob, start[ob])

