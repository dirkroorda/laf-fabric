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
                "sft.book",
            ],
            "edge": [
            ],
        },
    },
}

def task(laftask):
    '''Produces the plain text of the Hebrew Bible, in fact the Biblia Hebraica Stuttgartensia version.

    No book, chapter, verse marks. Newlines for each verse.
    The outcome should be identical to the primary data file in the original LAF resource.

    This is a handy check on all the data transformations involved. If the output of this task
    is not byte for byte equal to the primary data, something seriously wrong with LAF-Fabric!
    '''
    (msg, P, NN, F, X) = laftask.API()

    prim = laftask.env['source'] != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = laftask.add_output("output.txt")

    for i in F.shebanq_db_otype.s('word' if prim else 'book'):
        the_output = ''
        if prim:
            the_text = F.shebanq_ft_text.v(i)
            the_suffix = F.shebanq_ft_suffix.v(i)
            the_newline = "\n" if '׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_output = F.shebanq_sft_book.v(i) + " "
        out.write(the_output)
