import sys

load = {
    "primary": True,
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
            ],
        },
        "dirk": {
            "node": [
                "part.comment,intro,role",
            ],
            "edge": [
                "part.comment",
            ],
        },
    },
}

def task(processor):
    '''Shows how to use added annotations.

    The annotations come from an extra annotation package, which contains a few
    extra annotation files.
    
    **dirk.xml** annotates some of the books in a rather trivial way. 

    If there is no comment, the output of this task will say "*no comment*, otherwise
    the comment is shown.

    **word_phrase=intro_role.xml** is a form based annotation package.
    See task :mod:`annox_create`.

    It contains a few annotations in Genesis 1.
    All these annotations will be shown in a listing in the output.
    '''
    (msg, P, NN, F, C, X) = processor.API()

    msg("Get the books ...")

    out = processor.add_output("output.txt")

    for i in NN(test=F.shebanq_db_otype.v, value='book'):
        dirk_says = F.dirk_part_comment.v(i)
        the_output = "{} Dirk: {}\n".format(F.shebanq_sft_book.v(i), dirk_says if dirk_says else 'no comment')
        out.write(the_output)

    for i in NN(test=F.shebanq_db_otype.v, values=['word', 'phrase']):
        the_type = F.shebanq_db_otype.v(i)
        intro = F.dirk_part_intro.v(i)
        role = F.dirk_part_role.v(i)
        if role and intro:
            the_text = "_".join([text for (n, text) in P.data(i)])
            out.write("{}\t{}\tintro={}\trole={}\n".format(the_type, the_text, role, intro))

