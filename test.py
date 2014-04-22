import sys
import random
import collections
from pyparsing import nestedExpr
import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.mql import MQL
fabric = LafFabric()

data_dir = '/Users/dirk/Dropbox/DANS/current/projects/etcbc/DOP/'
sort_frags_file = 'ot_fragments.txt'
data_path = "{}/{}".format(data_dir, sort_frags_file)
