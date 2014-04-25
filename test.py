import sys
import collections
import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.lib import Transcription
from etcbc.trees import Tree
fabric = LafFabric()

tr = Transcription()
API = fabric.load('bhs3', '--', 'trees', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype monads
    ''','''
    '''),
    "prepare": prepare,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))

tree_big = Tree(API)
tree = Tree(API, ['verse', 'sentence', 'word'])
(parent, children) = tree.embedding()
