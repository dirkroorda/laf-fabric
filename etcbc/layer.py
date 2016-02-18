class Layer(object):
    '''Layering of MQL objects.

    ``up(otype, n)`` is the node of MQL type ``otype`` that acts as container of node ``n``.
    In this way you can get e.g. for each subphrase and phrase_atom the book, chapter, half_verse and sentence_atom in which it occurs.
    ``down(otype, n)`` is the converse of ``up()``: it delivers an ordered list of nodes of MQL type ``otype`` contained in node ``n``.
    '''
    def __init__(self, lafapi):
        lafapi.api['fabric'].load_again({"features": ('otype book chapter verse number', '')}, add=True, verbose='INFO')
        self.up = lafapi.data_items['zL00(node_up)']
        self.down = lafapi.data_items['zL00(node_down)']
        self.lafapi = lafapi

    def u(self, tp, n): return self.up.get(tp, {}).get(n, None)
    def d(self, tp, n): return self.down.get(tp, {}).get(n, None)
    def p(self, tp, book=None, chapter=None, verse=None, sentence=None, clause=None, phrase=None):
        F = self.lafapi.api['F']
        drill_nodes = list(F.otype.s('book'))
        first_step = True
        for (rtp, val, feat) in (
            ('book', book, F.book.v),
            ('chapter', chapter, F.chapter.v),
            ('verse', verse, F.verse.v),
            ('sentence', sentence, F.number.v),
            ('clause', clause, F.number.v),
            ('phrase', phrase, F.number.v),
        ):
            if first_step:
                if val == None: new_drill_nodes = drill_nodes
                else:
                    new_drill_nodes = [n for n in drill_nodes if feat(n) == str(val)]
                first_step = False
            else:
                if val == None: new_drill_nodes = drill_nodes
                else:
                    new_drill_nodes = []
                    for n in drill_nodes:
                        new_drill_nodes += [m for m in self.down.get(rtp, {}).get(n, []) if feat(m) == str(val)]
            drill_nodes = new_drill_nodes
        new_drill_nodes = []
        for n in drill_nodes:
            new_drill_nodes += [m for m in self.down.get(tp, {}).get(n, [])]
        return new_drill_nodes

