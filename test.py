class Names(object):
    def di2p(inv, data):
        return "{}C{}".format(
            'A' if data == 'annox' else '',
            'i' if inv else '',
        )

    def isf(fstr):
        if ',' not in fstr:
            return None
        else:
            return fstr.split(',')

    def kd2p(kind, data):
        return "{}F{}".format(
            'A' if data == 'annox' else '',
            'E' if kind == 'edge' else '',
        )

    def p2kd(pref):
        kind = 'edge' if pref.endswith('E') else 'node'
        data = 'annox' if pref.startswith('A') else 'main'
        return (kind, data)

    def f2api(feature):
        return "_".join(*feature)

    def f2con(feature, kind, data):
        return "{}: {} ({})".format(
            data,
            "_".join(*feature),
            kind,
        )

    def f2key(feature, kind, data):
        return "{}{}".format(
            Names.kd2p(kind, data),
            ','.join(*feature),
        )

    def f2file(feature, kind, data):
        return "{}{}".format(
            Names.kd2p(kind, data),
            ','.join(*feature),
        )

    def key2f(fstr):
        comps = Names.isf(fstr)
        if comps == None:
            return None
        return (comps[1:],) + Names.p2kd(comps[0])

    def file2f(fstr):
        comps = Names.isf(fstr)
        if comps == None:
            return None
        return (comps[1:],) + Names.p2kd(comps[0])

key = "AFE,shebanq,ft,part_of_speech"
print("{} => {}".format(key, Names.key2f(key)))
