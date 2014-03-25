import sys
import collections
from laf.fabric import LafFabric
from etcbc.preprocess import prepare

# Test modes "tiny" and "tinyc" should work out of the box, without configuration.
# They use the example data, which is just Genesis 1:1 from the Hebrew Text database in LAF.
#
#   python laf-fabric-test.py tiny
#   python laf-fabric-test.py tinyc
#
# "tinyc" forces compilation, "tiny" only compiles when needed.
#
# Test modes "full" and "fulls" work the full Hebrew text database, provided
# you have the data.
# "full" uses your configuration of the work directory as in your laf-fabric.cfg,
# either in this # directory, or in your home directory.
# "fulls" uses a standard location, in your home directory, and saves it
# to your laf-fabric.cfg in your home directory, or creates it if it does not exist.
#
#   python laf-fabric-test.py full
#   python laf-fabric-test.py fulls
#
# This script tests all facilities of the LAF-API.

testmodes = {
    'tiny': {
        'work_dir': './example-data/etcbc-gen11',
        'laf_dir': './example-data/etcbc-gen11',
        'source_file': 'bhs3-tiny.txt.hdr',
        'verbose': 'DEBUG',
        'compile': False,
        'save': False,
    },
    'tinys': {
        'work_dir': './example-data/etcbc-gen11',
        'laf_dir': './example-data/etcbc-gen11',
        'source_file': 'bhs3-tiny.txt.hdr',
        'verbose': 'DEBUG',
        'compile': False,
        'save': True,
    },
    'tinyc': {
        'work_dir': './example-data/etcbc-gen11',
        'laf_dir': './example-data/etcbc-gen11',
        'source_file': 'bhs3-tiny.txt.hdr',
        'verbose': 'DEBUG',
        'compile': True,
        'save': False,
    },
    'full': {
        'work_dir': None,
        'laf_dir': None,
        'source_file': 'bhs3.txt.hdr',
        'verbose': 'NORMAL',
        'compile': False,
        'save': False,
    },
    'fulls': {
        'work_dir': None,
        'laf_dir': None,
        'source_file': 'bhs3.txt.hdr',
        'verbose': 'NORMAL',
        'compile': False,
        'save': True,
    },
}

mode = sys.argv[1] if len(sys.argv) > 1 else 'tiny'
if mode not in testmodes:
    print("Unknown mode: {}".format(mode))
    sys.exit(1)
test = testmodes[mode]
print("MODE={}".format(mode))

# Start up LAF-Fabric

fabric = LafFabric(
    work_dir=test['work_dir'],
    laf_dir=test['laf_dir'],
    save=test['save'],
    verbose=test['verbose'],
)
API = fabric.api

print('''
################ PLAIN TEXT ##########################################
#                                                                    #
# Retrieve the plain text by means of two features on the word nodes.#
# The outcome should be byte-equal to the primary data in the laf    #
# resource.                                                          #
#                                                                    #
######################################################################
''')
fabric.load(test['source_file'], '--', 'plain',
        {
            "xmlids": {
                "node": False,
                "edge": False,
            },
            "features": {
                "shebanq": {
                    "node": [
                        "db.otype",
                        "ft.text,suffix",
                        "sft.book",
                    ],
                    "edge": [
                    ],
                },
            },
        },
        compile_main=test['compile'], compile_annox=False,
    )
exec(fabric.localnames.format(var='fabric'))

msg("Get the words ... ")
out = outfile("unicode_utf8.txt")

for i in F.shebanq_db_otype.s('word'):
    text = F.shebanq_ft_text.v(i) 
    suffix = F.shebanq_ft_suffix.v(i) 
    out.write('{}{}{}'.format(text, suffix, "\n" if '׃' in suffix else ""))
close()

print('''
################ OBJECTS # ORDER # PREPARING #########################
#                                                                    #
# List objects with their type and id. Mind the proper nesting,      #
# which is a consequence of ordering the nodes. LAF-Fabric must be   #
# helped by a module that knows the objects in the ETCBC data.       #
#                                                                    #
######################################################################
''')
fabric.load(test['source_file'], '--', 'objects',
    {
        "xmlids": {
            "node": False,
            "edge": False,
        },
        "features": {
            "shebanq": {
                "node": [
                    "db.oid,otype,monads",
                ],
                "edge": [
                ],
            },
        },
        'prepare': prepare,
    }
)
exec(fabric.localnames.format(var='fabric'))

msg("Get the objects ... ")
out = outfile("objects.txt")

for i in NN():
    oid = F.shebanq_db_oid.v(i)
    otype = F.shebanq_db_otype.v(i)
    monads = F.shebanq_db_monads.v(i)
    out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
close()

print('''
################ CONNECTIVITY ########################################
#                                                                    #
# Travel along edges. See how far you can travel until you reach     #
# end points. If you start from a set of nodes, what is the set of   #
# nodes that your reach?                                             #
#                                                                    #
######################################################################
''')
fabric.load(test['source_file'], '--', 'parents',
{
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.text",
                "sft.book",
            ],
            "edge": [
                "parents.",
            ],
        },
        "": {
            "edge": ['.x'],
        },
    },
})
exec(fabric.localnames.format(var='fabric'))

msg("Get the parents ...")

print('''
======================================================================
= compute an overview of the parents relation                        =
======================================================================
''')
out = outfile('parents_of.csv')
bookname = None
found = 0

for i in NN():
    otype = F.shebanq_db_otype.v(i)
    for p in C.shebanq_parents_.v(i):
        found += 1
        ptype = F.shebanq_db_otype.v(p)
        if mode == 'tiny':
            msg("{}={} -> {}={}".format(otype, F.shebanq_ft_text.v(i) if otype == 'word' else i, ptype, F.shebanq_ft_text.v(p) if ptype == 'word' else p))
        else:
            out.write("{}={} -> {}={}\n".format(otype, F.shebanq_ft_text.v(i) if otype == 'word' else i, ptype, F.shebanq_ft_text.v(p) if ptype == 'word' else p))
    if otype == "book":
        bookname = F.shebanq_sft_book.v(i)
        sys.stderr.write("{} ({})\n".format(bookname, found))
sys.stderr.write("Total {}\n".format(found))

print('''
======================================================================
= travel from a set of nodes and inspect the set where you arrive    =
======================================================================
''')
msg("Travel from node sets ...")

for query in (
        ('parents', 'forward', C.shebanq_parents_, ['word', 'phrase', 'clause', 'sentence']),
        ('parents', 'backward', Ci.shebanq_parents_, ['word', 'phrase', 'clause', 'sentence']),
        ('unannotated', 'forward', C.__x, ['half_verse', 'verse', 'chapter', 'book']),
        ('unannotated', 'backward', Ci.__x, ['half_verse', 'verse', 'chapter', 'book']),
    ):
        (the_edgetype, direction, the_edge, the_types) = query
        the_set = list(NN(test=F.shebanq_db_otype.v, values=the_types))
        the_endset = set(the_edge.endnodes(the_set))
        the_endtypes = set([F.shebanq_db_otype.v(n) for n in the_endset])
        print("Traveling from start set {} with {} nodes along {} edges {}:\nYou end up in an end set of {} endnodes with {} type(s) namely {}.\n".format(
            the_types, len(the_set), the_edgetype, direction, len(the_endset), len(the_endtypes), the_endtypes
    ))
close()

print('''
################ XML IDENTIFIERS IN ORIGINAL SOURCE ##################
#                                                                    #
# List the original XML identifers of node elements in the           #
# original LAF resource.                                             #
#                                                                    #
#                                                                    #
######################################################################
''')
fabric.load(test['source_file'], '--', 'xmlids',
{
    "xmlids": {
        "node": True,
        "edge": True,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.oid,otype",
            ],
            "edge": [
            ],
        },
    },
})
exec(fabric.localnames.format(var='fabric'))

msg("Get the xmlids ...")
out = outfile('xmlids-nodes.txt')

for n in NN():
    otype = F.shebanq_db_otype.v(n)
    oid = F.shebanq_db_oid.v(n)
    xid = X.r(n)
    nid = X.i(xid)
    if nid != n: Emsg('nid {} != {} n'.format(nid, n), verbose='ERROR')
    result = 'nid={} n={} {}(oid={}) xid={}'.format(nid, n, otype, oid, xid)
    if mode == 'tiny':
        msg(result)
    else:
        out.write(result + '\n')
close()

print('''
################ EXTRA ANNOTATION PACKAGES (ANNOX) ###################
#                                                                    #
# Show the annotations that have been meda in an extra annotation    #
# package (also known as an annox)                                   #
#                                                                    #
#                                                                    #
######################################################################
''')
fabric.load(test['source_file'], 'participants', 'personal',
        {
            "xmlids": {
                "node": False,
                "edge": False,
            },
            "features": {
                "dirk": {
                    "node": [
                        "part.intro,role",
                    ],
                    "edge": [
                    ],
                },
                "shebanq": {
                    "node": [
                        "db.otype",
                        "ft.text",
                    ],
                    "edge": [
                    ],
                },
            },
        },
        compile_main=test['compile'], compile_annox=False,
    )
exec(fabric.localnames.format(var='fabric'))

msg("Get the annotations ...")
out = outfile('annotations.txt')

for n in set(F.dirk_part_intro.s()) | set(F.dirk_part_role.s()):
    otype = F.shebanq_db_otype.v(n)
    rep = F.shebanq_ft_text.v(n) if otype == 'word' else n
    intro = F.dirk_part_intro.v(n)
    role = F.dirk_part_role.v(n)
    msg("{}({})\tintro='{}'\trole='{}'".format(
        otype, rep,
        intro or 'n/a',
        role or 'n/a',
    ))
close()

