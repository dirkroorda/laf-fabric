import sys
from laf.fabric import LafFabric
from etcbc.preprocess import prepare

testmodes = {
    'tiny': {
        'work_dir': './example-data',
        'laf_dir': './example-data/etcbc-gen11',
        'source_file': 'bhs3-tiny.txt.hdr',
        'verbose': 'NORMAL',
        'compile': False,
    },
    'full': {
        'work_dir': None,
        'laf_dir': None,
        'source_file': 'bhs3.txt.hdr',
        'verbose': 'NORMAL',
        'compile': False,
    },
}

mode = sys.argv[1] if len(sys.argv) > 1 else 'tiny'
if mode not in testmodes:
    print("Unknown mode: {}".format(mode))
    sys.exit(1)
test = testmodes[mode]
print("MODE={}".format(mode))

processor = LafFabric(
    work_dir=test['work_dir'],
    laf_dir=test['laf_dir'],
    save=mode=='full',
    verbose=test['verbose'],
)
API = processor.api

processor.load(test['source_file'], '--', 'plain',
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

F = API['F']
msg = API['msg']
outfile = API['outfile']
close = API['close']

msg("Get the words ... ")

out = outfile("unicode_utf8.txt")

for i in F.shebanq_db_otype.s('word'):
    text = F.shebanq_ft_text.v(i) 
    suffix = F.shebanq_ft_suffix.v(i) 
    out.write('{}{}{}'.format(text, suffix, "\n" if '׃' in suffix else ""))
close()

processor.load(test['source_file'], '--', 'objects',
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
#        'prepare': prepare,
    }
)

NN = API['NN']
F = API['F']
outfile = API['outfile']
close = API['close']

msg("Get the objects ... ")

out = outfile("output.txt")

for i in NN():
    oid = F.shebanq_db_oid.v(i)
    otype = F.shebanq_db_otype.v(i)
    monads = F.shebanq_db_monads.v(i)
    out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))
close()
