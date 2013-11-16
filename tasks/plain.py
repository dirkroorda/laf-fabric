# -*- coding: utf8 -*-

features = {
    "nodes": "db:otype ft:text,suffix sft:book",
    "edges": '',
}

def task(graftask):
    (msg, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()
    prim = graftask.source != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = graftask.add_result("output.txt")

    object_type = Vi["word"] if prim else Vi["book"]
    for i in NNFV(Ni["db.otype"], object_type):
        the_output = ''
        if prim:
            the_text = Fr(i, Ni["ft.text"])
            the_suffix = Fr(i, Ni["ft.suffix"])
            the_newline = "\n" if u'׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_book = Fr(i, Ni["sft.book"])
            the_output = the_book + " "
        out.write(the_output)
