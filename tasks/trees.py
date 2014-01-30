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
#                "parents.",
            ],
        },
    },
}

def task(processor):
    '''We walk through all words and follow them upwards, along parents edges until there are no more outgoing edges.
    We then have the starting points for our sentences.

    We walk through the starting points, and for each starting point we assemble the tree hanging off that point.
    This we do by walking the parents edges in the opposite direction.

    We use the monad numbers (word numbers) to maintain word order.

    * parents links from words to phrases to clauses to sentences
    * word numbers

    We should use that.
    '''

    API = processor.API()
    F = API['F']
    NN = API['NN']
    C = API['C']
    Ci = API['Ci']
    msg = API['msg']
    msg("API loaded")

