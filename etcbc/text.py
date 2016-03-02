import collections
from .lib import Transcription

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
        self.langs = dict(
            la=('latin', 'Latina'),
            en=('english', 'English'),
            fr=('french', 'François'),
            de=('german', 'Deutsch'),
            nl=('dutch', 'Nederlands'),
            el=('greek', 'Ελληνικά'),
            he=('hebrew', 'עברית'),
            ru=('russian', 'Русский'),
            es=('spanish', 'Español'),
            ko=('korean', '한국어'),
            sw=('swahili', 'Kiswahili'),
            tr=('turkish', 'Türkçe'),
        )
        self._booknames = dict(
            en=tuple('''
                    Genesis
                    Exodus
                    Leviticus
                    Numbers
                    Deuteronomy
                    Joshua
                    Judges
                    1_Samuel
                    2_Samuel
                    1_Kings
                    2_Kings
                    Isaiah
                    Jeremiah
                    Ezekiel
                    Hosea
                    Joel
                    Amos
                    Obadiah
                    Jonah
                    Micah
                    Nahum
                    Habakkuk
                    Zephaniah
                    Haggai
                    Zechariah
                    Malachi
                    Psalms
                    Job
                    Proverbs
                    Ruth
                    Song_of_songs
                    Ecclesiastes
                    Lamentations
                    Esther
                    Daniel
                    Ezra
                    Nehemiah
                    1_Chronicles
                    2_Chronicles
                '''.strip().split()),
            nl=tuple('''
                    Genesis
                    Exodus
                    Leviticus
                    Numeri
                    Deuteronomium
                    Jozua
                    Richteren
                    1_Samuel
                    2_Samuel
                    1_Koningen
                    2_Koningen
                    Jesaja
                    Jeremia
                    Ezechiel
                    Hosea
                    Joël
                    Amos
                    Obadja
                    Jona
                    Micha
                    Nahum
                    Habakuk
                    Zefanja
                    Haggaï
                    Zacharia
                    Maleachi
                    Psalmen
                    Job
                    Spreuken
                    Ruth
                    Hooglied
                    Prediker
                    Klaagliederen
                    Esther
                    Daniel
                    Ezra
                    Nehemia
                    1_Kronieken
                    2_Kronieken
                '''.strip().split()),
            de=tuple('''
                    Genesis
                    Exodus
                    Levitikus
                    Numeri
                    Deuteronomium
                    Josua
                    Richter
                    1_Samuel
                    2_Samuel
                    1_Könige
                    2_Könige
                    Jesaja
                    Jeremia
                    Ezechiel
                    Hosea
                    Joel
                    Amos
                    Obadja
                    Jona
                    Micha
                    Nahum
                    Habakuk
                    Zefanja
                    Haggai
                    Sacharja
                    Maleachi
                    Psalmen
                    Ijob
                    Sprichwörter
                    Rut
                    Hoheslied
                    Kohelet
                    Klagelieder
                    Ester
                    Daniel
                    Esra
                    Nehemia
                    1_Chronik
                    2_Chronik
                '''.strip().split()),
            fr=tuple('''
                    Genèse
                    Exode
                    Lévitique
                    Nombres
                    Deutéronome
                    Josué
                    Juges
                    1_Samuel
                    2_Samuel
                    1_Rois
                    2_Rois
                    Isaïe
                    Jérémie
                    Ézéchiel
                    Osée
                    Joël
                    Amos
                    Abdias
                    Jonas
                    Michée
                    Nahoum
                    Habaquq
                    Sophonie
                    Aggée
                    Zacharie
                    Malachie
                    Psaumes
                    Job
                    Proverbes
                    Ruth
                    Cantique_des_Cantiques
                    Ecclésiaste
                    Lamentations
                    Esther
                    Daniel
                    Esdras
                    Néhémie
                    1_Chroniques
                    2_Chroniques
                '''.strip().split()),
            el=tuple('''
                    Γένεση
                    Έξοδος
                    Λευιτικό
                    Αριθμοί
                    Δευτερονόμιο
                    Ιησούς
                    Κριταί
                    Σαμουήλ_A'                    
                    Σαμουήλ_Β'
                    Βασιλείς_A'
                    Βασιλείς_Β'
                    Ησαΐας
                    Ιερεμίας
                    Ιεζεκιήλ
                    Ωσηέ
                    Ιωήλ
                    Αμώς
                    Οβδιού
                    Ιωνάς
                    Μιχαίας
                    Ναούμ
                    Αβακκούμ
                    Σοφονίας
                    Αγγαίος
                    Ζαχαρίας
                    Μαλαχίας
                    Ψαλμοί
                    Ιώβ
                    Παροιμίαι
                    Ρουθ
                    Άσμα_Ασμάτων
                    Εκκλησιαστής
                    Θρήνοι
                    Εσθήρ
                    Δανιήλ
                    Έσδρας
                    Νεεμίας
                    Χρονικά_Α'
                    Χρονικά_Β'
                '''.strip().split()),
            he=tuple('''
                    בראשית
                    שמות
                    ויקרא
                    במדבר
                    דברים
                    יהושע
                    שופטים
                    שמואל_א
                    שמואל_ב
                    מלכים_א
                    מלכים_ב
                    ישעיהו
                    ירמיהו
                    יחזקאל
                    הושע
                    יואל
                    עמוס
                    עובדיה
                    יונה
                    מיכה
                    נחום
                    חבקוק
                    צפניה
                    חגי
                    זכריה
                    מלאכי
                    תהילים
                    איוב
                    משלי
                    רות
                    שיר_השירים
                    קהלת
                    איכה
                    אסתר
                    דניאל
                    עזרא
                    נחמיה
                    דברי_הימים_א
                    דברי_הימים_ב
                '''.strip().split()),
            ru=tuple('''
                    Бытия
                    Исход
                    Левит
                    Числа
                    Второзаконие
                    ИисусНавин
                    КнигаСудей
                    1-я_Царств
                    2-я_Царств
                    3-я_Царств
                    4-я_Царств
                    Исаия
                    Иеремия
                    Иезекииль
                    Осия
                    Иоиль
                    Амос
                    Авдия
                    Иона
                    Михей
                    Наум
                    Аввакум
                    Софония
                    Аггей
                    Захария
                    Малахия
                    Псалтирь
                    Иов
                    Притчи
                    Руфь
                    ПесниПесней
                    Екклесиаст
                    ПлачИеремии
                    Есфирь
                    Даниил
                    Ездра
                    Неемия
                    1-я_Паралипоменон
                    2-я_Паралипоменон
            '''.strip().split()),
            es=tuple('''
                    Génesis
                    Éxodo
                    Levítico
                    Números
                    Deuteronomio
                    Josué
                    Jueces
                    1_Samuel
                    2_Samuel
                    1_Reyes
                    2_Reyes
                    Isaías
                    Jeremías
                    Ezequiel
                    Oseas
                    Joel
                    Amós
                    Abdías
                    Jonás
                    Miqueas
                    Nahúm
                    Habacuc
                    Sofonías
                    Hageo
                    Zacarías
                    Malaquías
                    Salmos
                    Job
                    Proverbios
                    Rut
                    Cantares
                    Eclesiastés
                    Lamentaciones
                    Ester
                    Daniel
                    Esdras
                    Nehemías
                    1_Crónicas
                    2_Crónicas
            '''.strip().split()),
            ko=tuple('''
                    창세기
                    탈출기
                    레위기
                    민수기
                    신명기
                    여호수아
                    재판관기
                    사무엘_첫째
                    사무엘_둘째
                     열왕기_첫째
                    열왕기_둘째
                    이사야
                    예레미야
                    에스겔
                    호세아
                    요엘
                    아모스
                    오바댜
                    요나
                    미가
                    나훔
                    하박국
                    스바냐
                    학개
                    스가랴
                    말라기
                    시편
                    욥
                    잠언
                    룻
                    솔로몬의_노래
                    전도서
                    애가
                    에스더
                    다니엘
                    에스라
                    느헤미야
                    역대기_첫째
                    역대기_둘째
            '''.strip().split()),
            sw=tuple('''
                    Mwanzo
                    Kutoka
                    Mambo_ya_Walawi
                    Hesabu
                    Kumbukumbu_la_Torati
                    Yoshua
                    Waamuzi
                    1_Samweli
                    2_Samweli
                    1_Wafalme
                    2_Wafalme
                    Isaya
                    Yeremia
                    Ezekieli
                    Hosea
                    Yoeli
                    Amosi
                    Obadia
                    Yona
                    Mika
                    Nahumu
                    Habakuki
                    Sefania
                    Hagai
                    Zekaria
                    Malaki
                    Zaburi
                    Ayubu
                    Mithali
                    Ruthi
                    Wimbo_Ulio_Bora
                    Mhubiri
                    Maombolezo
                    Esta
                    Danieli
                    Ezra
                    Nehemia
                    1_Mambo_ya_Nyakati
                    2_Mambo_ya_Nyakati
            '''.strip().split()),
            tr=tuple('''
                    Yaratılış
                    Mısır'dan_Çıkış
                    Levililer
                    Çölde_Sayım
                    Yasa'nın_Tekrar
                    Yeşu
                    Hakimler
                    1_Samuel
                    2_Samuel
                    1_Krallar
                    2_Krallar
                    Yeşaya
                    Yeremya
                    Hezekiel
                    Hoşea
                    Yoel
                    Amos
                    Ovadya
                    Yunus
                    Mika
                    Nahum
                    Habakkuk
                    Sefanya
                    Hagay
                    Zekeriya
                    Malaki
                    Mezmurlar
                    Eyüp
                    Süleyman'ın_Özdeyişleri
                    Rut
                    Ezgiler_Ezgisi
                    Vaiz
                    Ağıtlar
                    Ester
                    Daniel
                    Ezra
                    Nehemya
                    1_Tarihler
                    2_Tarihler
            '''.strip().split()),
        )
        for (bn, book_la) in enumerate(self._books):
            self._book_name.setdefault('la', {})[bn] = book_la
            self._book_node.setdefault('la', {})[book_la] = bn
        for ln in self._booknames:
            for (i, (bn, book_la)) in enumerate(self._books):
                book_ln = self._booknames[ln][i]
                self._book_name.setdefault(ln, {})[bn] = book_ln
                self._book_node.setdefault(ln, {})[book_ln] = bn

    def node_of(self, book, chapter, verse, fmt='la'):
        return self._verses.get(book, {}).get(chapter, {}).get(verse, None)

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
