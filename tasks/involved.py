# -*- coding: utf8 -*-
import sys

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.text,suffix",
                "sft.book,chapter,verse",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    '''Produces the plain text of the Hebrew Bible, in fact the Biblia Hebraica Stuttgartensia version.

    In contrast to the task :mod:`task.plain`, the
    books, chapters, and verses are marked.
    '''
    (msg, P, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book = None
    the_chapter = None
    the_verse = None
    for i in NN():
        this_type = F.shebanq_db_otype.v(i)
        if this_type == "word":
            the_text = F.shebanq_ft_text.v(i)
            the_suffix = F.shebanq_ft_suffix.v(i)
            out.write(the_text + the_suffix)
        elif this_type == "book":
            the_book = F.shebanq_sft_book.v(i)
            sys.stderr.write("\r{:>6} {:<30}".format(i, the_book)) 
            out.write("\n{}".format(the_book))
        elif this_type == "chapter":
            the_chapter = F.shebanq_sft_chapter.v(i)
            out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == "verse":
            the_verse = F.shebanq_sft_verse.v(i)
            out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
