import sys
import os
import time
import glob
import collections
from contextlib import contextmanager
import unittest

from laf.fabric import LafFabric
from etcbc.preprocess import prepare

SOURCE = 'bhs3-tiny.txt.hdr'
ANNOX = 'participants'
WORKDIR = './example-data/etcbc-gen11'
WORKDIRA = '{}/example-data/etcbc-gen11'.format(os.getcwd())
LAFDIR = WORKDIR
LAFDIRA = WORKDIRA

class TestLafFabric(unittest.TestCase):
    processor = None

    def setUp(self):
        if self.processor == None:
            self.processor = LafFabric(
                work_dir=WORKDIR,
                laf_dir=LAFDIR,
                save=False,
                verbose='SILENT',
            )
        pass

    def test_a0_startup(self):
        lafapi = self.processor.lafapi
        self.assertEqual(lafapi.names._myconfig['work_dir'], WORKDIRA)
        self.assertEqual(lafapi.names._myconfig['m_source_dir'], LAFDIRA)
        pass

    def test_b0_compile_main(self):
        now = time.time()
        time.sleep(1)
        API = self.processor.load(SOURCE, '--', 'compile', {}, compile_main=True)
        found = 0
        the_log = None
        the_log_mtime = None
        newer = True
        for f in glob.glob("{}/bin/{}/*".format(WORKDIRA, SOURCE)):
            fn = os.path.basename(f)
            if fn in 'AZ': continue
            elif fn == '__log__compile__.txt':
                the_log = f
                the_log_mtime = os.path.getmtime(f)
            else:
                found += 1
            if os.path.getmtime(f) < now: newer = False
        self.assertTrue(newer)
        self.assertTrue(the_log)
        self.assertEqual(found, 64)
        API['close']()
        API = self.processor.load(SOURCE, '--', 'compile', {}, compile_main=False)
        API['close']()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    def test_b1_compile_annox(self):
        now = time.time()
        time.sleep(1)
        API = self.processor.load(SOURCE, ANNOX, 'compile', {}, compile_annox=True)
        found = 0
        the_log = None
        the_log_mtime = None
        newer = True
        for f in glob.glob("{}/bin/{}/A/{}/*".format(WORKDIRA, SOURCE, ANNOX)):
            fn = os.path.basename(f)
            if fn == '__log__compile__.txt':
                the_log = f
                the_log_mtime = os.path.getmtime(f)
            else:
                found += 1
            if os.path.getmtime(f) < now: newer = False
        self.assertTrue(newer)
        self.assertTrue(the_log)
        self.assertEqual(found, 9)
        API['close']()
        API = self.processor.load(SOURCE, ANNOX, 'compile', {}, compile_annox=False)
        API['close']()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    def test_d1_load(self):
        self.processor.lafapi.unload_all()
        API = self.processor.load(SOURCE, ANNOX, 'load', {
                "xmlids": {
                    "node": True,
                    "edge": True,
                },
                "features": {
                    "shebanq": {
                        "node": [
                            "db.otype",
                            "ft.text,suffix",
                            "sft.book",
                        ],
                        "edge": [
                            "mother.",
                            "parents.",
                        ],
                    },
                },
                "primary": True,
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        API['close']()
        loadspec = self.processor.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 0)
        self.assertEqual(len(loadspec['clear']), 0)
        self.assertEqual(len(loadspec['load']), 37)
        API = self.processor.load(SOURCE, ANNOX, 'load', {
                "xmlids": {
                    "node": True,
                    "edge": False,
                },
                "features": {
                    "shebanq": {
                        "node": [
                            "db.oid",
                            "ft.text,suffix",
                            "sft.book",
                        ],
                        "edge": [
                            "parents.",
                        ],
                    },
                },
                "primary": False,
            },
            compile_main=False, compile_annox=False,
        )
        API['close']()
        loadspec = self.processor.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 20)
        self.assertEqual(len(loadspec['clear']), 17)
        self.assertEqual(len(loadspec['load']), 2)

    def test_d2_load(self):
        self.processor.lafapi.unload_all()
        API = self.processor.load(SOURCE, ANNOX, 'load', {
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
                            "mother.",
                            "parents.",
                        ],
                    },
                    "dirk": {
                        "node": [
                            "db.otype",
                            "dbs.otype",
                        ],
                    }
                },
                "primary": True,
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        API['close']()
        feature_abbs = self.processor.lafapi.feature_abbs
        feature_abb = self.processor.lafapi.feature_abb
        self.assertEqual(feature_abb['otype'], 'shebanq_db_otype')
        self.assertEqual(len(feature_abbs['otype']), 3)
        for nm in ('shebanq_db_otype', 'dirk_dbs_otype', 'dirk_db_otype'): nm in feature_abbs['otype']
        self.assertEqual(len(feature_abbs['db_otype']), 2)
        for nm in ('shebanq_db_otype', 'dirk_db_otype'): nm in feature_abbs['otype']

    def test_e1_primary_data(self):
        API = self.processor.load(SOURCE, ANNOX, 'plain', {
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
                "primary": True,
            },
            compile_main=False, compile_annox=False,
        )
        P = API['P']
        F = API['F']
        NN = API['NN']
        out = API['outfile']('primary_words.txt')
        text = ''
        for n in NN(test=F.shebanq_db_otype.v, value='word'):
            text += '['+']['.join([p[1] for p in P.data(n)])+']'
        out.write(text)
        API['close']()
        expected = '''[בְּ][רֵאשִׁ֖ית][בָּרָ֣א][אֱלֹהִ֑ים][אֵ֥ת][הַ][שָּׁמַ֖יִם][וְ][אֵ֥ת][הָ][אָֽרֶץ]'''
        self.assertEqual(text, expected)

    def test_e2_primary_data(self):
        API = self.processor.load(SOURCE, ANNOX, 'plain', {
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
                "primary": True,
            },
            compile_main=False, compile_annox=False,
        )
        F = API['F']
        NN = API['NN']
        NE = API['NE']
        out = API['outfile']('events.txt')
        text = ''
        for (anchor, events) in NE():
            for (node, kind) in events:
                kindr = '(' if kind == 0 else '«' if kind == 1 else '»' if kind == 2 else ')'
                otype = F.shebanq_db_otype.v(node)
                text += "{} {:>7}: {:<15} {:>7}\n".format(kindr, anchor, otype, node)
        out.write(text)
        API['close']()
        expected = '''(       0: book                 25
(       0: chapter              26
(       0: verse                29
(       0: clause               11
(       0: clause_atom          12
(       0: sentence             21
(       0: sentence_atom        22
(       0: half_verse           27
(       0: phrase               13
(       0: phrase_atom          17
(       0: word                  0
)       3: word                  0
(       3: word                  1
)      12: word                  1
)      12: phrase_atom          17
)      12: phrase               13
»      12: sentence_atom        22
»      12: sentence             21
»      12: clause_atom          12
»      12: clause               11
«      13: clause               11
«      13: clause_atom          12
«      13: sentence             21
«      13: sentence_atom        22
(      13: word                  2
(      13: phrase               14
(      13: phrase_atom          18
)      20: phrase_atom          18
)      20: phrase               14
)      20: word                  2
»      20: sentence_atom        22
»      20: sentence             21
»      20: clause_atom          12
»      20: clause               11
«      21: clause               11
«      21: clause_atom          12
«      21: sentence             21
«      21: sentence_atom        22
(      21: word                  3
(      21: phrase               15
(      21: phrase_atom          19
)      30: phrase_atom          19
)      30: phrase               15
)      30: word                  3
»      30: sentence_atom        22
»      30: sentence             21
»      30: clause_atom          12
»      30: clause               11
)      31: half_verse           27
«      31: clause               11
«      31: clause_atom          12
«      31: sentence             21
«      31: sentence_atom        22
(      31: half_verse           28
(      31: phrase               16
(      31: phrase_atom          20
(      31: subphrase            23
(      31: word                  4
)      35: word                  4
»      35: subphrase            23
»      35: phrase_atom          20
»      35: phrase               16
»      35: sentence_atom        22
»      35: sentence             21
»      35: clause_atom          12
»      35: clause               11
«      36: clause               11
«      36: clause_atom          12
«      36: sentence             21
«      36: sentence_atom        22
«      36: phrase               16
«      36: phrase_atom          20
«      36: subphrase            23
(      36: word                  5
)      38: word                  5
(      38: word                  6
)      48: word                  6
)      48: subphrase            23
»      48: phrase_atom          20
»      48: phrase               16
»      48: sentence_atom        22
»      48: sentence             21
»      48: clause_atom          12
»      48: clause               11
«      49: clause               11
«      49: clause_atom          12
«      49: sentence             21
«      49: sentence_atom        22
«      49: phrase               16
«      49: phrase_atom          20
(      49: word                  7
)      51: word                  7
(      51: subphrase            24
(      51: word                  8
)      55: word                  8
»      55: subphrase            24
»      55: phrase_atom          20
»      55: phrase               16
»      55: sentence_atom        22
»      55: sentence             21
»      55: clause_atom          12
»      55: clause               11
«      56: clause               11
«      56: clause_atom          12
«      56: sentence             21
«      56: sentence_atom        22
«      56: phrase               16
«      56: phrase_atom          20
«      56: subphrase            24
(      56: word                  9
)      58: word                  9
(      58: word                 10
)      64: word                 10
)      64: subphrase            24
)      64: phrase_atom          20
)      64: phrase               16
)      64: sentence_atom        22
)      64: sentence             21
)      64: clause_atom          12
)      64: clause               11
)      65: half_verse           28
)      65: verse                29
)    3901: chapter              26
)  185245: book                 25
'''
        self.assertEqual(text, expected)

    def test_m1_connectivity(self):
        API = self.processor.load(SOURCE, ANNOX, 'connectivity',
        {
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
                        "parents.",
                    ],
                },
            },
        }, compile_main=False)

        FE = API['FE']
        F = API['F']
        C = API['C']
        Ci = API['Ci']
        NN = API['NN']
        top_node_types = collections.defaultdict(lambda: 0)
        top_nodes = C.shebanq_parents_.endnodes(set(NN(test=F.shebanq_db_otype.v, value='word')))
        self.assertEqual(len(top_nodes), 1)
        for node in NN(nodes=top_nodes):
            tag = F.shebanq_db_otype.v(node)
            top_node_types[tag] += 1
        for tag in top_node_types:
            n = top_node_types[tag]
            self.assertEqual(tag, 'sentence')
            self.assertEqual(n, 1)
        nt = 0
        for node in NN():
            parents = C.shebanq_parents_.v(node)
            if len(list(parents)) and F.shebanq_db_otype.v(node) == 'sentence':
                nt += 1
        self.assertEqual(nt, 0)

    def test_u1_plain(self):
        API = self.processor.load(SOURCE, '--', 'plain', {
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
            compile_main=False, compile_annox=False,
        )

        F = API['F']

        textitems = []
        for i in F.otype.s('word'):
            text = F.text.v(i) 
            suffix = F.suffix.v(i) 
            textitems.append('{}{}{}'.format(text, suffix, "\n" if '׃' in suffix else ""))
        text = ''.join(textitems)
        expected = '''בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃
'''
        self.assertEqual(text, expected)

if __name__ == '__main__': unittest.main()
