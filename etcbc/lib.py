class Transcription(object):
    decomp = {
        '\u05E9\u05C1': "\uFB2A",
        '\u05E9\u05C2': "\uFB2B",
    }
    mapping = {
        '>': "\u05D0",
        'B': "\u05D1",
        'G': "\u05D2",
        'D': "\u05D3",
        'H': "\u05D4",
        'W': "\u05D5",
        'Z': "\u05D6",
        'X': "\u05D7",
        'V': "\u05D8",
        'J': "\u05D9",
        'K': "\u05DB",
        'L': "\u05DC",
        'M': "\u05DE",
        'N': "\u05E0",
        'S': "\u05E1",
        '<': "\u05E2",
        'P': "\u05E4",
        'Y': "\u05E6",
        'Q': "\u05E7",
        'R': "\u05E8",
        'C': "\uFB2A",
        'F': "\uFB2B",
        'T': "\u05EA",
        'p': "\u05E3",
        'm': "\u05DD",
        'n': "\u05DF",
        'k': "\u05DA",
        'y': "\u05E5",
        '_': "-",
        '-': "-",
        '[': "[",
        ']': "]",
        '/': "/",
        ' ': " ",
        '\0': "",
        '(': "\u0028",
        ')': "\u0029",
    }

    def __init__(self):
        self.mappingi = dict((v,k) for (k,v) in Transcription.mapping.items())

    def _comp(s):
        for (d, c) in Transcription.decomp.items(): s = s.replace(d, c)
        return s
    def _decomp(s): 
        for (d, c) in Transcription.decomp.items(): s = s.replace(c, d)
        return s

    def hebrew(self, word):
        return Transcription._decomp(''.join(self.mapping.get(x, x) for x in Transcription._comp(word)))
    def trans(self, word):
        return ''.join(self.mappingi.get(x, x) for x in Transcription._comp(word))
