# -*- coding: utf8 -*-

precompute = {
    "plain": {},
    "memo": {},
    "assemble": {
        "only_nodes": "db:otype ft:text,suffix sft:book",
        "only_edges": '',
    },
    "assemble_all": {
    },
}

def task(graftask):
    (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()
    prim = graftask.source != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = graftask.add_result("output.txt")

    object_type = Vi["word"] if prim else Vi["book"]
    for i in NNFV(Li["db"], Ni["otype"], object_type):
        the_output = ''
        if prim:
            the_text = Fr(i, Li["ft"], Ni["text"])
            the_suffix = Fr(i, Li["ft"], Ni["suffix"])
            the_newline = "\n" if u'׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_book = Fr(i, Li["sft"], Ni["book"])
            the_output = the_book + " "
        out.write(the_output)
