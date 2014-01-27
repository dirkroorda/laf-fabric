import collections
import sys

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.text_plain,part_of_speech",
                "sft.book,chapter,verse",
            ],
            "edge": [
            ],
        },
    },
}

relevant_nodes = [
    ("word", ''),
    ("subphrase", 'p'),
    ("phrase", 'P'),
    ("clause", 'C'),
    ("sentence", 'S'),
    ("_split_", None),
    ("verse", None),
    ("chapter", None),
    ("book", None),
]

pos_table = {
 'adjective': 'aj',
 'adverb': 'av',
 'article': 'dt',
 'conjunction': 'cj',
 'interjection': 'ij',
 'interrogative': 'ir',
 'negative': 'ng',
 'noun': 'n',
 'preposition': 'pp',
 'pronoun': 'pr',
 'verb': 'vb',
}

select_node = collections.defaultdict(lambda: None)
abbrev_node = collections.defaultdict(lambda: None)

for (i, (otype, abb)) in enumerate(relevant_nodes):
    select_node[otype] = i
    abbrev_node[otype] = abb if abb != None else otype

split_n = select_node['_split_']

def task(processor):
    '''Sentence trees.

    '''
    API = processor.API()
    F = API['F']
    NE = API['NE']
    msg = API['msg']

    trees = processor.add_output("trees.txt")

    level = 0

    book = None
    chapter = None
    verse = None
    verse_label = None
    tree = None

    n = 0
    for (anchor, events) in NE(key=lambda n:select_node[F.shebanq_db_otype.v(n)], simplify=lambda n:select_node[F.shebanq_db_otype.v(n)] < split_n):
        for (node, kind) in events:
            if kind == 3:
                otype = F.shebanq_db_otype.v(node)
                if select_node[otype] > split_n:
                    continue
                tree += ')'
                if otype == 'sentence':
                    tree += '\n'
                    trees.write(tree)

            elif kind == 2:
                otype = F.shebanq_db_otype.v(node)
                if select_node[otype] > split_n:
                    continue
                tree += '»{}»'.format(abbrev_node[otype])

            elif kind == 1:
                otype = F.shebanq_db_otype.v(node)
                if select_node[otype] > split_n:
                    continue
                tree += '«{}« '.format(abbrev_node[otype])

            elif kind == 0:
                otype = F.shebanq_db_otype.v(node)
                if otype == 'book':
                    book = F.shebanq_sft_book.v(node)
                    msg(book)
                elif otype == 'chapter':
                    chapter = F.shebanq_sft_chapter.v(node)
                elif otype == 'verse':
                    verse = F.shebanq_sft_verse.v(node)
                    verse_label = '{} {}:{}'.format(book, chapter, verse)
                elif otype == 'sentence':
                    tree = '{:<15} (S '.format(verse_label)
                elif otype == 'word':
                    pos = pos_table[F.shebanq_ft_part_of_speech.v(node)]
                    text = F.shebanq_ft_text_plain.v(node)
                    tree += '({} "{}"'.format(pos, text)
                else:
                    tree += '({} '.format(abbrev_node[otype])

