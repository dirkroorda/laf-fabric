import collections
from .lib import Transcription
from .blang import booklangs, booknames

def h_esc(x): return x.replace('&', '&amp;').replace('<', '&lt;')

class Text(object):
    '''Text representations
    '''
    def __init__(self, lafapi):
        lafapi.api['fabric'].load_again({"features": ('''
            otype
            g_word_utf8 trailer_utf8
            g_qere_utf8 qtrailer_utf8
            lex_utf8
            phono phono_sep
            book chapter verse
''', '')}, annox='lexicon', add=True, verbose='INFO')
        self._verses = lafapi.data_items['zV00(verses)']
        self.lafapi = lafapi
        self.env = lafapi.names.env
        F = lafapi.api['F']
        self.transcription = Transcription()

        def get_orig(w):
            word = F.g_word_utf8.v(w)
            qere = F.g_qere_utf8.v(w)
            if qere == None:
                orig = word
                trl = F.trailer_utf8.v(w)
            else:
                orig = qere
                trl = F.qtrailer_utf8.v(w)
            origt = self.transcription.from_hebrew(orig + trl).replace('_', ' ')
            return origt

        def get_orig_p(w):
            s = F.phono_sep.v(w)
            if '.' in s: s += '\n'
            return F.phono.v(w)+s

        self._transform = collections.OrderedDict((
            ('hp', ('hebrew primary', lambda w: F.g_word_utf8.v(w)+F.trailer_utf8.v(w))),
            ('ha', ('hebrew accent',  lambda w: Transcription.to_hebrew(get_orig(w)))),
            ('hv', ('hebrew vowel',   lambda w: Transcription.to_hebrew_v(get_orig(w)))),
            ('hc', ('hebrew cons',    lambda w: Transcription.to_hebrew_c(get_orig(w)))),
            ('ea', ('trans accent',   lambda w: get_orig(w))),
            ('ev', ('trans vowel',    lambda w: Transcription.to_etcbc_v(get_orig(w)))),
            ('ec', ('trans cons',     lambda w: Transcription.to_etcbc_c(get_orig(w)))),
            ('pf', ('phono full',     lambda w: get_orig_p(w).replace('*',''))),
            ('ps', ('phono simple',   lambda w: Transcription.ph_simplify(get_orig_p(w)))),
        ))
        self._books = lafapi.data_items['zV00(books_la)']
        self.book_nodes = tuple(x[0] for x in self._books)
        self._book_name = {}
        self._book_node = {}
        self.langs = booklangs
        self.booknames = booknames
        for (bn, book_la) in enumerate(self._books):
            self._book_name.setdefault('la', {})[bn] = book_la
            self._book_node.setdefault('la', {})[book_la] = bn
        for ln in self.booknames:
            for (i, (bn, book_la)) in enumerate(self._books):
                book_ln = self.booknames[ln][i]
                self._book_name.setdefault(ln, {})[bn] = book_ln
                self._book_node.setdefault(ln, {})[book_ln] = bn

    def node_of(self, book, chapter, verse, lang='en'):
        book_node = self._book_node.get(lang, {}).get(book, None)
        return self._verses.get(book_node, {}).get(chapter, {}).get(verse, None)

    def formats(self): return self._transform

    def book_name(self, bn, lang='en'): return self._book_name.get(lang, {}).get(bn, None)
    def book_node(self, book_name, lang='en'): return self._book_node.get(lang, {}).get(book_name, None)
             
    def words(self, wnodes, fmt='ha'):
        reps = []
        fmt = fmt if fmt in self._transform else 'ha'
        make_rep = self._transform[fmt][1]
        for wnode in wnodes: reps.append(make_rep(wnode))
        return ''.join(reps)

    def verse(self, bn, ch, vs, fmt='ha', html=True, verse_label=True, format_label=True, lang='en'):
        L = self.lafapi.api['L']
        vlabel = '{} {}:{}'.format(self.book_name(bn, lang), ch, vs)
        flabel = self._transform[fmt][0]
        if verse_label: vlabel = '<td class="vl">{}</td>'.format(vlabel) if html else '{}  '.format(vlabel)
        else: vlabel = ''
        if format_label: flabel = '<td class="fl">{}</td>'.format(flabel) if html else ' [{}]'.format(flabel)
        else: flabel = ''

        text = self.words(L.d('word', self._verses[bn][ch][vs]), fmt=fmt)
        if html:
            text = '<td class="{}">{}</td>'.format(fmt[0], h_esc(text))
        else:
            if not text.endswith('\n'): text += '\n'

        total = '{}{}{}'.format(vlabel, text, flabel)
        if html: total = '<table class="t"><tr>{}</tr></table>'.format(total)
        return total

    def whole(self, fmt='ha', verse_labels=False, lang='en'):
        F = self.lafapi.api['F']
        L = self.lafapi.api['L']
        NN = self.lafapi.api['NN']
        msg = self.lafapi.api['msg']
        reps = []
        fmt = fmt if fmt in self._transform else 'ha'
        make_rep = self._transform[fmt][1]
        msg('Producing whole text of {} in format {}{}'.format(self.env['source'], fmt, ' with verse labels' if verse_labels else ''))
        for n in NN():
            wtext = ''
            if F.otype.v(n) == 'word':
                wtext = make_rep(n)
                reps.append(wtext)
            elif verse_labels and F.otype.v(n) == 'verse': reps.append('{}{} {}:{}  '.format(
                '\n' if reps and reps[-1] and reps[-1][-1] != '\n' else '',
                self.book_name(L.u('book', n), lang=lang), F.chapter.v(n), F.verse.v(n),
            ))
        return ''.join(reps)
    
    def style(self, params=None, show_params=False):
        msg = self.lafapi.api['msg']
        style_defaults = dict(
            hebrew_color='000000',
            hebrew_size='large',
            hebrew_line_height='1.8',
            etcbc_color='aa0066',
            etcbc_size='small',
            etcbc_line_height='1.5',
            phono_color='00b040',
            phono_size='medium',
            phono_line_height='1.5',
            verse_color='0000ff',
            verse_size='small',
            verse_width='5em',
            fmt_color='ccbb00',
            fmt_size='small',
            fmt_width='5em',
        )
        errors = []
        good = True
        for x in [1]:
            good = False
            if type(params) is not dict:
                errors.append('ERROR: the style parameters should be a dictionary')
                break
            thisgood = True
            for x in params:
                if x not in style_defaults:
                    errors.append('ERROR: unknown style parameter: {}'.format(x))
                    thisgood = False
            if not thisgood: break
            good = True
        if not good:
            errors.append('ERROR: wrong style specfication. Switching to default values')
            for e in errors: msg(e)
            params = dict()
        style_defaults.update(params)
        if not good or show_params:
            for x in sorted(style_defaults): msg('{} = {}'.format(x, style_defaults[x]))

        return '''
<style type="text/css">
table.t {{
    width: 100%;
}}
td.h {{
    font-family: Ezra SIL, SBL Hebrew, Verdana, sans-serif;
    font-size: {hebrew_size};
    line-height: {hebrew_line_height};
    color: #{hebrew_color};
    text-align: right;
    direction: rtl;
}}
td.e {{
    font-family: Menlo, Courier New, Courier, monospace;
    font-size: {etcbc_size};
    line-height: {etcbc_line_height};
    color: #{etcbc_color};
    text-align: left;
    direction: ltr;
}}
td.p {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {phono_size};
    line-height: {phono_line_height};
    color: #{phono_color};
    text-align: left;
    direction: ltr;
}}

td.vl {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {verse_size};
    text-align: right;
    vertical-align: top;
    color: #{verse_color};
    width: {verse_width};
    direction: ltr;
}}
td.fl {{
    font-family: Verdana, Arial, sans-serif;
    font-size: {fmt_size};
    text-align: left;
    vertical-align: top;
    color: #{fmt_color};
    width: {fmt_width};
    direction: ltr;
}}
</style>
'''.format(**style_defaults)
