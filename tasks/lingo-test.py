import collections
import sys
from etcbc import preprocess

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.gender,part_of_speech",
                "sft.verse_label",
            ],
            "edge": [
            ],
        },
    },
}

def task(processor):
    '''Crude visualization of the syntactic structure of the text.

    Shows the linguistic objects in their actual embedding.
    Replaces each word by a dot.

    Verbs are represented with a spade sign (♠), nouns by (♂), (♀), (?) depending on their gender.

    Words that happen to be outside any syntactic container are marked as (◘).

    '''
    API = processor.API()
    F = API['F']
    NN = API['NN']

    preprocess.check(API)

    out = processor.add_output("output.txt")

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

    cur_verse_label = ['','']


    lastmin = None
    lastmax = None

    for node in NN():
        otype = F.shebanq_db_otype.v(node)
        ob = type_map[otype]
        if ob == None:
            continue

        if ob == "w":
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
        elif ob == "V":
            this_verse_label = F.shebanq_sft_verse_label.v(node)
            cur_verse_label[0] = this_verse_label
            cur_verse_label[1] = this_verse_label
        elif ob == "S":
            out.write("\n{:<11} (".format(cur_verse_label[1], ob))
            cur_verse_label[1] = ''
        else:
            out.write("({}".format(ob))
