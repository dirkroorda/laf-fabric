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
SPECIFIC = True

class TestLafFabric(unittest.TestCase):
    fabric = None

    def setUp(self):
        if self.fabric == None:
            self.fabric = LafFabric(
                work_dir=WORKDIR,
                laf_dir=LAFDIR,
                save=False,
                verbose='SILENT',
            )
        pass

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_a0_startup(self):
        lafapi = self.fabric.lafapi
        self.assertEqual(lafapi.names._myconfig['work_dir'], WORKDIRA)
        self.assertEqual(lafapi.names._myconfig['m_source_dir'], LAFDIRA)
        pass

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_b0_compile_main(self):
        now = time.time()
        time.sleep(1)
        API = self.fabric.load(SOURCE, '--', 'compile', {}, compile_main=True)
        close = API['close']
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
        close()
        API = self.fabric.load(SOURCE, '--', 'compile', {}, compile_main=False)
        close()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_b1_compile_annox(self):
        now = time.time()
        time.sleep(1)
        API = self.fabric.load(SOURCE, ANNOX, 'compile', {}, compile_annox=True)
        close = API['close']
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
        close()
        API = self.fabric.load(SOURCE, ANNOX, 'compile', {}, compile_annox=False)
        close()
        self.assertEqual(the_log_mtime, os.path.getmtime(the_log)), 

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_d1_load(self):
        self.fabric.lafapi.unload_all()
        API = self.fabric.load(SOURCE, ANNOX, 'load', {
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
        close = API['close']
        close()
        loadspec = self.fabric.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 0)
        self.assertEqual(len(loadspec['clear']), 0)
        self.assertEqual(len(loadspec['load']), 37)
        API = self.fabric.load(SOURCE, ANNOX, 'load', {
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
        close = API['close']
        close()
        loadspec = self.fabric.lafapi.loadspec
        self.assertEqual(len(loadspec['keep']), 20)
        self.assertEqual(len(loadspec['clear']), 17)
        self.assertEqual(len(loadspec['load']), 2)

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_d2_load(self):
        self.fabric.lafapi.unload_all()
        API = self.fabric.load(SOURCE, ANNOX, 'load', {
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
        close = API['close']
        close()
        feature_abbs = self.fabric.lafapi.feature_abbs
        feature_abb = self.fabric.lafapi.feature_abb
        self.assertEqual(feature_abb['otype'], 'shebanq_db_otype')
        self.assertEqual(len(feature_abbs['otype']), 3)
        for nm in ('otype', 'dirk_dbs_otype', 'dirk_db_otype'): nm in feature_abbs['otype']
        self.assertEqual(len(feature_abbs['db_otype']), 2)
        for nm in ('otype', 'dirk_db_otype'): nm in feature_abbs['db_otype']

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_e1_primary_data(self):
        API = self.fabric.load(SOURCE, ANNOX, 'plain', {
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
        NN = API['NN']
        F = API['F']
        P = API['P']
        outfile = API['outfile']
        close = API['close']
        out = outfile('primary_words.txt')
        text = ''
        for n in NN(test=F.otype.v, value='word'):
            text += '['+']['.join([p[1] for p in P.data(n)])+']'
        out.write(text)
        close()
        expected = '''[בְּ][רֵאשִׁ֖ית][בָּרָ֣א][אֱלֹהִ֑ים][אֵ֥ת][הַ][שָּׁמַ֖יִם][וְ][אֵ֥ת][הָ][אָֽרֶץ]'''
        self.assertEqual(text, expected)

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_e2_primary_data(self):
        API = self.fabric.load(SOURCE, ANNOX, 'plain', {
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
        NE = API['NE']
        outfile = API['outfile']
        close = API['close']
        out = outfile('events.txt')
        text = ''
        for (anchor, events) in NE():
            for (node, kind) in events:
                kindr = '(' if kind == 0 else '«' if kind == 1 else '»' if kind == 2 else ')'
                otype = F.otype.v(node)
                text += "{} {:>7}: {:<15} {:>7}\n".format(kindr, anchor, otype, node)
        out.write(text)
        close()
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

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_m1_connectivity(self):
        API = self.fabric.load(SOURCE, ANNOX, 'connectivity',
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
        NN = API['NN']
        F = API['F']
        C = API['C']

        top_node_types = collections.defaultdict(lambda: 0)
        top_nodes = set(C.parents_.endnodes(NN(test=F.otype.v, value='word')))
        self.assertEqual(len(top_nodes), 1)
        for node in NN(nodes=top_nodes):
            tag = F.otype.v(node)
            top_node_types[tag] += 1
        for tag in top_node_types:
            n = top_node_types[tag]
            self.assertEqual(tag, 'sentence')
            self.assertEqual(n, 1)
        nt = 0
        for node in NN():
            parents = C.parents_.v(node)
            if len(list(parents)) and F.otype.v(node) == 'sentence':
                nt += 1
        self.assertEqual(nt, 0)

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u1_plain(self):
        API = self.fabric.load(SOURCE, '--', 'plain', {
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

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u2_not_prepared(self):
        API = self.fabric.load(SOURCE, '--', 'n_prep', {
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
            },
            compile_main=False, compile_annox=False,
        )
        NN = API['NN']
        expected_nodes = (25,26,29,11,12,21,22,27,13,17,0,1,2,14,18,3,15,19,28,16,20,23,4,5,6,7,24,8,9,10)
        for (i, n) in enumerate(NN()): self.assertEqual(n, expected_nodes[i])

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u3_prepared(self):
        API = self.fabric.load(SOURCE, '--', 'prep', {
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
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        NN = API['NN']
        expected_nodes = (25,26,29,21,22,11,12,27,13,17,0,1,14,18,2,15,19,3,28,16,20,23,4,5,6,7,24,8,9,10)
        for (i, n) in enumerate(NN()): self.assertEqual(n, expected_nodes[i])

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u4_edge_features(self):
        API = self.fabric.load(SOURCE, ANNOX, 'edges', {
                "xmlids": {
                    "node": False,
                    "edge": False,
                },
                "features": {
                    "dirk": {
                        "edge": [
                            'part.sectioning',
                        ],
                    },
                },
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        FE = API['FE']
        C = API['C']
        Ci = API['Ci']
        i = 0
        expected_annots = (2,"from verse to its first half verse"),(3,"from verse to its second half verse")
        for (n, v) in sorted(FE.sectioning.alookup.items()):
            self.assertEqual((n, v), expected_annots[i])
            i += 1

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u5_unmarked_edges(self):
        API = self.fabric.load(SOURCE, ANNOX, 'u_edges', {
                "xmlids": {
                    "node": False,
                    "edge": False,
                },
                "features": {
                    "dirk": {
                        "edge": [
                            'part.sectioning',
                        ],
                    },
                    "laf": {
                        "edge": [
                            '.x,y',
                        ],
                    },
                },
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        NN = API['NN']
        C = API['C']
        Ci = API['Ci']
        expected_x = [[26], [29], [27, 28], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        expected_xi = [[], [25], [26], [], [], [], [], [29], [], [], [], [], [], [], [], [], [], [], [29], [], [], [], [], [], [], [], [], [], [], []]
        expected_y = [[], [], [27, 28], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]
        expected_yi = [[], [], [], [], [], [], [], [29], [], [], [], [], [], [], [], [], [], [], [29], [], [], [], [], [], [], [], [], [], [], []] 
        i = 0
        for n in NN():
            j = 0
            for (m, v) in C.laf__x.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_x[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in C.laf__y.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_y[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in Ci.laf__x.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_xi[i][j])
                j += 1
            i += 1
        i = 0
        for n in NN():
            j = 0
            for (m, v) in Ci.laf__y.vv(n, sort=True):
                self.assertEqual(v, '')
                self.assertEqual(m, expected_yi[i][j])
                j += 1
            i += 1

    @unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u6_xml_ids(self):
        API = self.fabric.load(SOURCE, ANNOX, 'plain', {
                "xmlids": {
                    "node": True,
                    "edge": True,
                },
                "features": {
                    "shebanq": {
                        "edge": [
                            "mother.",
                            "parents.",
                        ],
                    },
                },
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        FE = API['FE']
        NN = API['NN']
        X = API['X']
        XE = API['XE']

        expected = {0: 'n2', 1: 'n3', 2: 'n4', 3: 'n5', 4: 'n6', 5: 'n7', 6: 'n8', 7: 'n9', 8: 'n10', 9: 'n11', 10: 'n12', 11: 'n28737', 12: 'n34680', 13: 'n59556', 14: 'n59557', 15: 'n59558', 16: 'n59559', 17: 'n40767', 18: 'n40768', 19: 'n40769', 20: 'n40770', 21: 'n84383', 22: 'n88917', 23: 'n77637', 24: 'n77638', 25: 'n1', 26: 'n93473', 27: 'n95056', 28: 'n95057', 29: 'n93523'}
        self.assertEqual(len(set(NN())), len(expected))
        for (n,x) in expected.items():
            self.assertEqual(X.i(x), n)
            self.assertEqual(X.r(n), x)

        expected_e = {4: 'el1', 5: 'el101734', 6: 'el253771', 7: 'el253772', 8: 'el253773', 9: 'el253774', 10: 'el511117', 11: 'el511118', 12: 'el511119', 13: 'el511120', 14: 'el793283', 15: 'el865010', 16: 'el865011', 17: 'el865012', 18: 'el1029314', 19: 'el1029315', 20: 'el1029316', 21: 'el1029317', 22: 'el1029318', 23: 'el1029319', 24: 'el1029320', 25: 'el1029321', 26: 'el1029322', 27: 'el1029323', 28: 'el1029324'}
        self.assertEqual(len(set(FE.parents_.lookup)|set(FE.mother_.lookup)), len(expected_e))
        for (e,x) in expected_e.items():
            self.assertEqual(XE.i(x), e)
            self.assertEqual(XE.r(e), x)

    #unittest.skipIf(SPECIFIC, 'running an individual test')
    def test_u7_endnodes(self):
        API = self.fabric.load(SOURCE, '--', 'plain', {
                "xmlids": {
                    "node": True,
                    "edge": True,
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
                    "laf": {
                        "edge": ['.x'],
                    },
                },
                "prepare": prepare,
            },
            compile_main=False, compile_annox=False,
        )
        NN = API['NN']
        F = API['F']
        C = API['C']
        Ci = API['Ci']
        for query in (
                ('parents', 'forward', C.parents_, ['word', 'phrase', 'clause', 'sentence'], 17, 1, 1, {'sentence'}),
                ('parents', 'backward', Ci.parents_, ['word', 'phrase', 'clause', 'sentence'], 17, 11, 1, {'word'}),
                ('unannotated', 'forward', C.laf__x, ['half_verse', 'verse', 'chapter', 'book'], 5, 2, 1, {'half_verse'}),
                ('unannotated', 'backward', Ci.laf__x, ['half_verse', 'verse', 'chapter', 'book'], 5, 1, 1, {'book'}),
            ):
                (the_edgetype, direction, the_edge, the_types, exp_o, exp_n, exp_t, exp_s) = query
                the_set = list(NN(test=F.otype.v, values=the_types))
                the_endset = set(the_edge.endnodes(the_set))
                the_endtypes = set([F.otype.v(n) for n in the_endset])
                self.assertEqual(len(the_set), exp_o)
                self.assertEqual(len(the_endset), exp_n)
                self.assertEqual(len(the_endtypes), exp_t)
                self.assertEqual(the_endtypes, exp_s)

if __name__ == '__main__': unittest.main()
