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
                "ft.gender",
                "sft.chapter,book",
            ],
            "edge": [
            ],
        },
    },
}

def task(processor):
    '''Counts the frequencies of words with male and female gender features.
    Outputs the frequencies in a tab-delimited file, with frequency values for
    each chapter in the whole Hebrew Bible.
    '''
    API = processor.API()
    F = API['F']
    NN = API['NN']

    stats_file = processor.add_output("stats.txt")

    stats = [0, 0, 0]
    cur_chapter = None
    ch = []
    m = []
    f = []

    for node in NN():
        otype = F.shebanq_db_otype.v(node)
        if otype == "word":
            stats[0] += 1
            if F.shebanq_ft_gender.v(node) == "masculine":
                stats[1] += 1
            elif F.shebanq_ft_gender.v(node) == "feminine":
                stats[2] += 1
        elif otype == "chapter":
            if cur_chapter != None:
                masc = 0 if not stats[0] else 100 * float(stats[1]) / stats[0]
                fem = 0 if not stats[0] else 100 * float(stats[2]) / stats[0]
                ch.append(cur_chapter)
                m.append(masc)
                f.append(fem)
                stats_file.write("{}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem))
            this_chapter = "{} {}".format(F.shebanq_sft_book.v(node), F.shebanq_sft_chapter.v(node))
            sys.stderr.write("\r{:<15}".format(this_chapter))
            stats = [0, 0, 0]
            cur_chapter = this_chapter


