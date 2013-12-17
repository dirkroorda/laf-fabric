# -*- coding: utf8 -*-

import sys

load = {
    "primary": True,
    "xmlids": {
        "node": True,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype,oid,monads",
                "ft.text",
                "sft.book,chapter,verse",
            ],
            "edge": [
            ],
        },
    },
}

config = {
    'target_type': 'word',
    'new_features': {
        'dirk': {
            'node': [
                "part.intro,role",
            ],
        },
    },
    'passages': {
        'Genesis': '1-3',
        'Isaiah': '40,66',
    },
}

def task(graftask):
    '''Produces a tab delimited file, meant as a feature import sheet.

    The dictionary ``config`` contains the specifications.
    '''
    (msg, P, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.csv")

    msg("Reading the books ...")

    the_book = None
    the_chapter = None
    the_verse = None
    in_book = False
    in_chapter = False
    do_chapters = {}
    target_type = config['target_type']
    for i in NN():
        this_type = F.shebanq_db_otype.v(i)
        print("{} {}".format(this_type, i))
        if this_type == target_type:
            if in_chapter:
                the_text = "*".join([text for (n. text) in P.data(i)])
                out.write("\t{}".format(the_text))
        elif this_type == "book":
            the_book = F.shebanq_sft_book.v(i)
            in_book = the_book in config['passages']
            if in_book:
                sys.stderr.write(the_book)
                do_chapters = {}
                chranges = config['passages'][the_book].split(',')
                for chrange in chranges:
                    boundaries = chrange.split('-')
                    (b, e) = (None, None)
                    if len(boundaries) == 1:
                        b = int(chrange)
                        e = int(chrange) + 1
                    else:
                        b = int(boundaries[0])
                        e = int(boundaries[1]) + 1
                    for ch in range(b, e):
                        do_chapters[str(ch)] = None
            else:
                sys.stderr.write("*")
        elif this_type == "chapter":
            if in_book:
                the_chapter = F.shebanq_sft_chapter.v(i)
                if the_chapter in do_chapters:
                    sys.stderr.write("{},".format(the_chapter))
                    in_chapter = True
                else:
                    in_chapter = False
        elif this_type == "verse":
            if in_chapter:
                the_verse = F.shebanq_sft_verse.v(i)
                out.write("\n{} {}:{} ".format(the_book, the_chapter, the_verse))
    sys.stderr.write("\n")
