import sys
import collections
from IPython import embed

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.part_of_speech,noun_type,lexeme_utf8",
                "sft.book",
            ],
            "edge": [
            ],
        },
    },
}

def task(processor):
    '''Collect co-occurrence data for lexemes across books in the bible.

    This is work together with Martijn Naaijer.

    We construct tables to load into Gephi (graph analysis).
    Nodes: the bible books.
    Edges: for each distinct lexeme that occurs in book1 and book2, we construct an edge.
    N.B.: we get multiple edges between pairs of nodes.
    Edges will be weighted.
   
    * The first weigth factor is only dependent on the lexeme: it is 1/s(lexeme)
      where s(lexeme) is the support for lexeme, defined as the number of books in which the lexeme occurs.
    * The second weight factor is dependent on the books: it is 1/#(book1 + book2)
      where book1 + book2 is the union of the sets of lexemes in book1 and book2, and #(set)
      is the cardinality of the set.

    Returns:
        The data will be delivered in two tab separated files: nodes.tsv for nodes, and edges.tsv for edges.
    
    Node format
        id <tab> label <newline>

    Edge format
        id <tab> source <tab> target <tab> type <tab> label <tab> weight 

    The type is always 1, meaning: bidirectional. 


    '''
    (msg, P, NN, F, C, X) = processor.API()

    lexemes = collections.defaultdict(lambda: collections.defaultdict(lambda:collections.defaultdict(lambda:0)))
    lexeme_support_book = collections.defaultdict(lambda: collections.defaultdict(lambda: {}))

    tasks = {
        'noun_common': {
            '1': processor.add_output("noun_common_1.gexf"),
            '2': processor.add_output("noun_common_2.gexf"),
        },
        'noun_proper': {
            '1': processor.add_output("noun_proper_1.gexf"),
            '2': processor.add_output("noun_proper_2.gexf"),
        },
        'verb': {
            '1': processor.add_output("verb_1.gexf"),
            '2': processor.add_output("verb_2.gexf"),
        },
        'all': {
            '1': processor.add_output("all_1.gexf"),
            '2': processor.add_output("all_2.gexf"),
        },
    }

    methods = {
        '1': lambda x, y: float(x) / y,
        '2': lambda x, y: float(x) / y / y,
    }

    book_name = None
    books = []

    data_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns:viz="http:///www.gexf.net/1.2draft/viz" xmlns="http://www.gexf.net/1.1draft" version="1.2">
<meta>
<creator>LAF-Fabric</creator>
</meta>
<graph defaultedgetype="undirected" idtype="string" type="static">
'''
    do_multigraph = False
    '''If there are multiple edges between a pair of nodes, the graph is called amultigraph.
    Gephi versions <0.9 do not support multigraphs.
    
    In the multigraph case, we create an edge for each lexeme that is common to a pair of books.
    In the other case, we add the weights of individual lexeme-labeled edges into the weight of 
    a single, total edge.
    '''
     

    for node in NN():
        this_type = F.shebanq_db_otype.v(node)
        if this_type == "word":
            lexeme = F.shebanq_ft_lexeme_utf8.v(node)

            lexemes['all'][book_name][lexeme] += 1
            lexeme_support_book['all'][lexeme][book_name] = 1

            p_o_s = F.shebanq_ft_part_of_speech.v(node)
            if p_o_s == "noun":
                noun_type = F.shebanq_ft_noun_type.v(node)
                if noun_type == "common":
                    lexemes['noun_common'][book_name][lexeme] += 1
                    lexeme_support_book['noun_common'][lexeme][book_name] = 1
                elif noun_type == "proper":
                    lexemes['noun_proper'][book_name][lexeme] += 1
                    lexeme_support_book['noun_proper'][lexeme][book_name] = 1
            elif p_o_s == "verb":
                lexemes['verb'][book_name][lexeme] += 1
                lexeme_support_book['verb'][lexeme][book_name] = 1

        elif this_type == "book":
            book_name = F.shebanq_sft_book.v(node)
            books.append(book_name)
            sys.stderr.write("{} ".format(book_name))
    sys.stderr.write("\n")

    nodes_header = '''<nodes count="{}">\n'''.format(len(books))

    for this_type in tasks:

        lexeme_support = {}
        for lexeme in lexeme_support_book[this_type]:
            lexeme_support[lexeme] = len(lexeme_support_book[this_type][lexeme])
             
        book_size = collections.defaultdict(lambda: 0)
        for book in lexemes[this_type]:
            book_size[book] = len(lexemes[this_type][book])
             
        node_data = []
        for node in range(len(books)):
            node_data.append('''<node id="{}" label="{}"/>\n'''.format(node + 1, books[node]))

        edge_id = 0
        edge_data = collections.defaultdict(lambda: [])
        for src in range(len(books)):
            for tgt in range(src + 1, len(books)):
                book_src = books[src]
                book_tgt = books[tgt]
                lexemes_src = {}
                lexemes_tgt = {}
                lexemes_src = lexemes[this_type][book_src]
                lexemes_tgt = lexemes[this_type][book_tgt]
                intersection_size = 0
                weights = collections.defaultdict(lambda: 0)
                for lexeme in lexemes_src:
                    if lexeme not in lexemes_tgt:
                        continue
                    pre_weight = lexeme_support[lexeme]
                    for this_method in tasks[this_type]:
                        weights[this_method] += methods[this_method](1000, pre_weight)
                    intersection_size += 1
                combined_size = book_size[book_src] + book_size[book_tgt] - intersection_size
                edge_id += 1
                for this_method in tasks[this_type]:
                    edge_data[this_method].append('''<edge id="{}" source="{}" target="{}" weight="{:.3g}"/>\n'''.
                        format(edge_id, src + 1, tgt + 1, weights[this_method]/combined_size))
                
        for this_method in tasks[this_type]:
            edges_header = '''<edges count="{}">\n'''.format(len(edge_data[this_method]))
            out_file = tasks[this_type][this_method]
            out_file.write(data_header)

            out_file.write(nodes_header)
            for node_line in node_data:
                out_file.write(node_line)
            out_file.write("</nodes>\n")

            out_file.write(edges_header)
            for edge_line in edge_data[this_method]:
                out_file.write(edge_line)
            out_file.write("</edges>\n")
            out_file.write("</graph></gexf>\n")

        sys.stdout.write("{}: nodes:  {}; edges: {}\n".format(this_type, len(books), edge_id))

