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

def task(processor):
    '''Produces the text of thev book Isaiah, interspersed with word numbers
    (*monad* numbers in WIVU speak).

    This is a first, clumsy attempt to pave the way for ading new features.
    In order to add new features, you have to indicate unambiguously to which
    nodes the features apply. 
    Here you can at least see the word numbers.

    A better way is coming, where you can add features to all nodes, not just words nodes,
    but also phrase, clause and sentence nodes.
    '''
    (msg, P, NN, F, C, X) = processor.API()

    out = processor.add_output("output.txt")

    the_book = None
    the_chapter = None
    the_verse = None
    ontarget = True
    for i in NN():
        this_type = F.shebanq_db_otype.v(i)
        if this_type == "word":
            if ontarget:
                the_monads = F.shebanq_db_monads.v(i)
                the_text = F.shebanq_ft_text.v(i)
                the_suffix = F.shebanq_ft_suffix.v(i)
                out.write(the_monads + "_" + the_text + the_suffix)
        elif this_type == "book":
            the_book = F.shebanq_sft_book.v(i)
            ontarget = the_book == "Isaiah"
            if ontarget:
                sys.stderr.write(the_book)
                out.write("\n{}".format(the_book))
            else:
                sys.stderr.write("*")
        elif this_type == "chapter":
            if ontarget:
                the_chapter = F.shebanq_sft_chapter.v(i)
                out.write("\n{} {}".format(the_book, the_chapter))
        elif this_type == "verse":
            if ontarget:
                the_verse = F.shebanq_sft_verse.v(i)
                out.write("\n{}:{} ".format(the_chapter, the_verse))
    sys.stderr.write("\n")
