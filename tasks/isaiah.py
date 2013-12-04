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
                "db.otype,monads",
                "ft.text,suffix",
                "sft.book,chapter,verse",
            ],
            "edge": [
            ],
        },
    },
}

def task(graftask):
    (msg, NN, F, X) = graftask.get_mappings()

    out = graftask.add_result("output.txt")

    the_book_id = None
    the_book = None
    the_chapter = None
    the_verse = None
    ontarget = True
    for i in NN():
        this_type = F.shebanq_db_otype.v(i)
        if this_type == F.shebanq_db_otype.i("word"):
            if ontarget:
                the_monads = F.shebanq_db_monads.vr(i)
                the_text = F.shebanq_ft_text.vr(i)
                the_suffix = F.shebanq_ft_suffix.vr(i)
                out.write(the_monads + "_" + the_text + the_suffix)
        elif this_type == F.shebanq_db_otype.i("book"):
            the_book_id = F.shebanq_sft_book.v(i)
            ontarget = the_book_id == F.shebanq_sft_book.i("Isaiah")
            if ontarget:
                the_book = F.shebanq_sft_book.vr(i)
                sys.stderr.write(the_book)
                out.write("\n{}".format(the_book))
            else:
                sys.stderr.write("*")
        elif this_type == F.shebanq_db_otype.i("chapter"):
            if ontarget:
                the_chapter = F.shebanq_sft_chapter.vr(i)
                out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == F.shebanq_db_otype.i("verse"):
            if ontarget:
                the_verse = F.shebanq_sft_verse.vr(i)
                out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
