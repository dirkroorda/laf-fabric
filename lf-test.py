import sys
import collections
from laf.fabric import LafFabric
fabric = LafFabric()
fabric.load('bhs3', '--', 'test', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''otype text suffix clause_constituent_relation phrase_type surface_consonants oid maxmonad minmonad monads text_plain''','''mother. parents.'''),
    "primary": False,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))
plain_file = outfile("bhs3_plain.txt")
for i in F.shebanq_db_otype.s('word'):
    the_text = F.text.v(i)
    the_suffix = F.suffix.v(i)
    the_newline = "\n" if '׃' in the_suffix else ""
    plain_file.write(the_text + the_suffix + the_newline)
close()
