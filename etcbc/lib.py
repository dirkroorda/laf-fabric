class Transcription(object):
    decomp = {
        '\u05E9\u05C1': "\uFB2A",
        '\u05E9\u05C2': "\uFB2B",
    }
    hebrew_mapping = {
        '>': "\u05D0", # alef
        'B': "\u05D1", # bet
        'G': "\u05D2", # gimel
        'D': "\u05D3", # dalet
        'H': "\u05D4", # he
        'W': "\u05D5", # vav
        'Z': "\u05D6", # zayin
        'X': "\u05D7", # het
        'V': "\u05D8", # tet
        'J': "\u05D9", # yod
        'K': "\u05DB", # kaf
        'L': "\u05DC", # lamed
        'M': "\u05DE", # mem
        'N': "\u05E0", # nun
        'S': "\u05E1", # samekh
        '<': "\u05E2", # ayin
        'P': "\u05E4", # pe
        'Y': "\u05E6", # tsadi
        'Q': "\u05E7", # qof
        'R': "\u05E8", # resh
        'C': "\uFB2A", # shin
        'F': "\uFB2B", # sin
        'T': "\u05EA", # tav
        'p': "\u05E3", # pe final
        'm': "\u05DD", # mem final
        'n': "\u05DF", # nun final
        'k': "\u05DA", # kaf final
        'y': "\u05E5", # tsadi final
        '&': "\u05BE", # maqaf
    }

    syriac_mapping = {
        '>': "\u0710", # alaph
        'B': "\u0712", # beth
        'G': "\u0713", # gamal
        'D': "\u0715", # dalat
        'H': "\u0717", # he
        'W': "\u0718", # waw
        'Z': "\u0719", # zain
        'X': "\u071A", # heth
        'V': "\u071B", # teth
        'J': "\u071D", # yudh
        'K': "\u071F", # kaph
        'L': "\u0720", # lamadh
        'M': "\u0721", # mim
        'N': "\u0722", # nun
        'S': "\u0723", # semkath
        '<': "\u0725", # e
        'P': "\u0726", # pe
        'Y': "\u0728", # sadhe
        'Q': "\u0729", # qaph
        'R': "\u072A", # rish
        'C': "\u072B", # shin
        'T': "\u072C", # taw
        's': "\u0724", # semkath final
        'p': "\u0727", # pe reversed
    }

    def __init__(self):
        self.hebrew_mappingi = dict((v,k) for (k,v) in Transcription.hebrew_mapping.items())

    def _comp(s):
        for (d, c) in Transcription.decomp.items(): s = s.replace(d, c)
        return s
    def _decomp(s): 
        for (d, c) in Transcription.decomp.items(): s = s.replace(c, d)
        return s

    def to_hebrew(self, word): return Transcription._decomp(''.join(self.hebrew_mapping.get(x, x) for x in Transcription._comp(word)))
    def from_hebrew(self, word): return ''.join(self.hebrew_mappingi.get(x, x) for x in Transcription._comp(word))
    def to_syriac(self, word): return Transcription._decomp(''.join(self.syriac_mapping.get(x, x) for x in Transcription._comp(word)))
    def from_syriac(self, word): return ''.join(self.syriac_mappingi.get(x, x) for x in Transcription._comp(word))


def monad_set(monadsrep):
    monads = set()
    for rng in monadsrep.split(','):
        bounds = rng.split('-')
        if len(bounds) == 2:
            for j in range(int(bounds[0]), int(bounds[1]) + 1): monads.add(j)
        else: monads.add(int(bounds[0]))
    return monads

object_rank = {
    'book': -4,
    'chapter': -3,
    'verse': -2,
    'half_verse': -1,
    'sentence': 1,
    'sentence_atom': 2,
    'clause': 3,
    'clause_atom': 4,
    'phrase': 5,
    'phrase_atom': 6,
    'subphrase': 7,
    'word': 8,
}

