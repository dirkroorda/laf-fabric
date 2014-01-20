import sys
import re
import collections

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
                "ft.part_of_speech,phrase_dependent_part_of_speech,noun_type,tense,text,lexeme_utf8,surface_consonants",
                "sft.book",
            ],
            "edge": [
            ],
        },
    },
}

def task(laftask):
    '''Collect frequency data of common nouns in Esther per bible book.

    This is part of reproducing results in Martijn Naaijer's thesis.

    We count lexemes of common nouns throughout the bible
    and we deliver a table of counts of all lexemes and a table of
    frequencies of lexemes restricted to the common nouns of Esther.

    When counting lexemes, we count the occurrences of *words*.
    If *word1* and *word2* have *n1* and *n2* occurrences, and both
    have the same *lexeme*, then *lexeme* has *n1* plus *n2*
    occurrences.

    When we compute frequencies, we divide lexeme occurrences as defined
    above by the total number of word occurrences.

    Returns:
        lexemes_all.txt (file): a table of all lexemes, ordered by bible book, with the number
        of occurrences in that bible book.

    Returns:
        lexemes_esther.txt (file): a matrix with as rows the lexemes of
        common nouns in Esther and as columns the books of the bible.
        A cell contain the frequency of that lexeme in that book multiplied by 1000 
    '''
    (msg, P, NN, F, X) = laftask.API()

    lexemes = collections.defaultdict(lambda:collections.defaultdict(lambda:0))

    out_all = laftask.add_output("participles.txt")

    wordscan = re.compile(r'>W?JB')
    for node in NN():
        this_type = F.shebanq_db_otype.v(node)
        if this_type == "word":
            surface_cons = F.shebanq_ft_surface_consonants.v(node)
            if wordscan.match(surface_cons):
                p_o_s = F.shebanq_ft_part_of_speech.v(node)
                pp_o_s = F.shebanq_ft_part_of_speech.v(node)
                tense = F.shebanq_ft_tense.v(node)
                out_all.write("{}\t{}\t{}\t{}\n".format(F.shebanq_ft_text.v(node), p_o_s, pp_o_s, tense))

