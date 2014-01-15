import sys
import collections

load = {
    "primary": True,
    "xmlids": {
        "node": True,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype,oid,monads",
                "ft.text",
                "sft.book,chapter,verse",
            ],
            "edge": [
            ],
        },
    },
}

config = {
    'target_types': [
        'word',
        'phrase',
    ],
    'new_features': {
        'dirk': {
            'node': [
                "part.intro,role",
            ],
        },
    },
    'passages': {
        'Genesis': '1-3',
        'Isaiah': '40,66',
    },
}

target_types = config['target_types']
type_col = {}
n_types = len(target_types)
for (n, tt) in enumerate(target_types):
    type_col[tt] = n

new_features_spec = config['new_features']
new_fqnames = []
new_fnames = {}
new_features = []
for aspace in sorted(new_features_spec.keys()):
    for kind in sorted(new_features_spec[aspace].keys()):
        for line in new_features_spec[aspace][kind]:
            (alabel, fnames) = line.split('.')
            for fname in fnames.split(','):
                fqname = "{}:{}.{}".format(aspace, alabel, fname)
                new_fqnames.append(fqname)
                new_features.append((aspace, alabel, fname))
                new_fnames[fname] = None
n_features = len(new_fqnames)

def task(graftask):
    '''Workflow to create new annotations.

    There are two modes:

    1. create a blank form (tab delimited file)
    2. create annotations from a filled-in form

    The dictionary ``config`` contains the specifications for creating the form.
    The same specifications are used when reading the filled in form.

    You specify node types that you want to annotate, e.g. *word* and *phrase*.
    You specifiy new features for which you want to provide values, e.g. 
    ``dirk:part.intro`` and ``dirk:part.role``.
    Finally you specify some chapters in the bible that you want to annotate.

    **Mode 1. creates a tab-delimited spreadsheet**

    It will have the following columns:

    A:
        xml_id of the node

    B1, ... , Bn:
        for each node type a column, with in it the piece of primary text corresponding to it.
        So if in our case a column for ``word`` and for ``phrase``.
        If the node is a ``word``, the ``word`` column will be filled with the primary text of that word,
        and the ``phrase`` column will be empty. If the node is a ``phrase``, it is the other way round, 
        with the ``phrase`` content in the ``phrase`` column.

    C1, ... , Cm
        for each new feature a column.
        These contain the cells where you can put in your feature values.
        If you put the value 'A' in column ``dirk:part.intro`` on the row of node ``n``, 
        you declare that node ``n`` has ``dirk:part.intro = 'A'``.

    **Mode 2. creates a LAF annotation file**

    If you have filled in the form and renamed it (replacing ``form`` in the file name by ``data``),
    then mode 2 can do its work. It creates a file with a name that starts with ``annot``.
    It will transform the information that you have put into the spreadsheet into properly targeted annotations.

    **Using the annotations**

    If you move the ``annot`` file over to the ``annox`` directory, and include it in a ``_header_.xml``
    file, you can use the annotations in tasks by selecting it as an annox.
    See the task :mod:`annox_use`.
    '''
    (msg, P, NN, F, X) = graftask.API()

    def make_form():
        msg("Reading the books ...")
        outf = graftask.add_output("form_{}={}.txt".format('_'.join(target_types), '_'.join(sorted(new_fnames.keys()))))

        the_book = None
        the_chapter = None
        the_verse = None
        in_book = False
        in_chapter = False
        do_chapters = {}
        outf.write("{}\t{}\t{}\n".format('passage', "\t".join(target_types), "\t".join(new_fqnames)))
        for i in NN():
            this_type = F.shebanq_db_otype.v(i)
            if this_type in target_types:
                if in_chapter:
                    the_xml_id = X.node.r(i)
                    the_text = "_".join([text for (n, text) in P.data(i)])
                    outf.write("{}\t{}{}{}\t{}\n".format(the_xml_id, "\t" * type_col[this_type], the_text, "\t" * (n_types - type_col[this_type]), "\t" * n_features))
            elif this_type == "book":
                the_book = F.shebanq_sft_book.v(i)
                in_book = the_book in config['passages']
                if in_book:
                    sys.stderr.write(the_book)
                    do_chapters = {}
                    chapter_ranges = config['passages'][the_book].split(',')
                    for chapter_range in chapter_ranges:
                        boundaries = chapter_range.split('-')
                        (b, e) = (None, None)
                        if len(boundaries) == 1:
                            b = int(chapter_range)
                            e = int(chapter_range) + 1
                        else:
                            b = int(boundaries[0])
                            e = int(boundaries[1]) + 1
                        for chapter in range(b, e):
                            do_chapters[str(chapter)] = None
                else:
                    sys.stderr.write("*")
            elif this_type == "chapter":
                if in_book:
                    the_chapter = F.shebanq_sft_chapter.v(i)
                    if the_chapter in do_chapters:
                        sys.stderr.write("{},".format(the_chapter))
                        in_chapter = True
                    else:
                        in_chapter = False
                else:
                    in_chapter = False
            elif this_type == "verse":
                if in_chapter:
                    the_verse = F.shebanq_sft_verse.v(i)
                    outf.write("#{} {}:{}\t{}\t{}\n".format(the_book, the_chapter, the_verse, "\t" * n_types, "\t" * n_features))
        sys.stderr.write("\n")

    def make_annots():
        inp = graftask.add_input("data_{}={}.txt".format('_'.join(target_types), '_'.join(sorted(new_fnames.keys()))))
        outa = graftask.add_output("annot_{}={}.xml".format('_'.join(target_types), '_'.join(sorted(new_fnames.keys()))))
        outa.write('''<?xml version="1.0" encoding="UTF-8"?>
<graph xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/">
    <graphHeader>
        <labelsDecl/>
        <dependencies/>
        <annotationSpaces/>
    </graphHeader>
''')
        aid = 0
        header = True
        features = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: {})))
        for line in inp:
            if header:
                header = False
                continue
            if line.startswith('#'):
                continue
            fields = line.rstrip().split("\t")
            xml_id = fields[0]
            values = fields[n_types + 1:n_types + 1 + n_features]
            for (n, value) in enumerate(values): 
                if value == "":
                    continue
                (aspace, alabel, fname) = new_features[n]
                features[aspace][alabel][xml_id][fname] = value

        for aspace in features:
            for alabel in features[aspace]:
                for xml_id in features[aspace][alabel]:
                    aid += 1
                    outa.write('<a xml:id="a{}" as="{}" label="{}" ref="{}"><fs>\n'.format(aid, aspace, alabel, xml_id))
                    for fname in features[aspace][alabel][xml_id]:
                        value = features[aspace][alabel][xml_id][fname]
                        outa.write('\t<f name="{}" value="{}"/>\n'.format(fname, value))
                    outa.write('</fs></a>\n')
        outa.write("</graph>\n")

    answer = input("1 = make form, 2 = make annotations [1/2] ")
    if answer == "1":
        make_form()
    elif answer == "2":
        make_annots()



