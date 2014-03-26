import sys
from laf.fabric import LafFabric

processor = LafFabric(verbose='DETAIL')

API = processor.load('bhs3.txt.hdr', '--', 'lingo',
    {
        "xmlids": {
            "node": False,
            "edge": None,
            "region": False,
        },
        "features": {
            "shebanq": {
                "node": { },
                "edge": [ ],
                "annot": [ ],
            },
        },
        "extra": True,
        "prepare": set(),
    }
)

NN = API['NN']
