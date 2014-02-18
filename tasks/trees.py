import sys
import collections

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype,monads,minmonad,maxmonad",
                "ft.text_plain,part_of_speech",
                "sft.verse_label",
            ],
            "edge": [
                "parents.",
            ],
        },
    },
}

def task(processor):
    '''Find all the top nodes with respect to the parents relationship.
    '''

    API = processor.API()
    F = API['F']
    NN = API['NN']
    C = API['C']
    Ci = API['Ci']
    msg = API['msg']

    words = set(NN(test=F.shebanq_db_otype.v, value='word'))
    topnodes = C.shebanq_parents__T('', words)
    msg('{}'.format(len(topnodes)))

