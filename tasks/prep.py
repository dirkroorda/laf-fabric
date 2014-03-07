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
            ],
            "edge": [
            ],
        },
    },
}

def task(processor):
    '''Produces the plain text of the Hebrew Bible, in fact the Biblia Hebraica Stuttgartensia version.

    No book, chapter, verse marks. Newlines for each verse.
    The outcome should be identical to the primary data file in the original LAF resource.

    This is a handy check on all the data transformations involved. If the output of this task
    is not byte for byte equal to the primary data, something seriously wrong with LAF-Fabric!
    '''
    API = processor.API()
    F = API['F']
    msg = API['msg']
    preprocess.check(API)

