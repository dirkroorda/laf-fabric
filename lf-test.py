import sys
import collections

import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
fabric = LafFabric()

version = '4b'
API = fabric.load('etcbc{}'.format(version), 'lexicon', 'valence', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        oid otype monads
        function rela
        g_word_utf8 trailer_utf8
        lex prs uvf sp ls vs vt nametype det gloss
        book chapter verse label number
    ''',
    '''
        mother
    '''),
    "prepare": prepare,
    "primary": False,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))
