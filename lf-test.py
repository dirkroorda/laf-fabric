from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.mql import MQL

fabric = LafFabric()

API = fabric.load('bhs3.txt.hdr', '--', 'plain', {"features": ("otype oid text surface_consonants",""), "primary": False})
exec(fabric.localnames.format(var='fabric'))

Q = MQL(API)

qu = '''
select all objects
in {1-20}
where
    [phrase
        [word surface_consonants = 'H']
        [word]
    ]
    ..
    [phrase
        [word]
        [word]
    ]
'''

sheaf = Q.mql(qu)
print(sheaf.compact(F.surface_consonants.v))
print("= = = = = = = > > > > > > > >")
print(sheaf.compact_results(F.surface_consonants.v))
