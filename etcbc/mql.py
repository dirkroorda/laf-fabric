import subprocess
from lxml import etree

MQL_FILE = 'mql/bhs3'
MQL_PROC = '/usr/local/bin/mql'
MQL_OPTS = ['--cxml', '-b', 's3', '-d']

index2node = {}
F = None
NN = None

class MQL(object):
    def __init__(self, API):
        global F
        global NN
        env = API['fabric'].lafapi.names.env
        self.data_path = '{}/{}'.format(env['work_dir'], MQL_FILE)
        self.parser = etree.XMLParser(remove_blank_text=True)
        NN = API['NN']
        F = API['F']
        for n in NN(): index2node[F.oid.v(n)] = n

    def mql(self, query):
        proc = subprocess.Popen(
            [MQL_PROC] + MQL_OPTS + [self.data_path],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        proc.stdin.write(bytes(query, encoding='utf8'))
        proc.stdin.close()
        xml = proc.stdout.read()
        sheaf = self._parse_results(xml)
        return Sheaf(sheaf)

    def _parse_results(self, xml):
        root = etree.fromstring(xml, self.parser)
        results = [MQL._parse_result(child) for child in root]
        nres = len(results)
        if nres > 1:
            print("WARNING: multiple results: {}".format(nres))
            return None
        return results[0] if nres else None
            
    def _parse_result(elem):
        results = [MQL._parse_sheaf(child) for child in elem if child.tag == 'sheaf']
        nres = len(results)
        return results[0] if nres else None

    def _parse_sheaf(elem):
        return [MQL._parse_straw(child) for child in elem]

    def _parse_straw(elem):
        return [MQL._parse_grain(child) for child in elem]

    def _parse_grain(elem):
        node = index2node[elem.attrib["id_d"] or elem.attrib["id_m"]]
        result = (node,)
        for child in elem:
            if child.tag == 'sheaf' and len(child):
                result = (node, MQL._parse_sheaf(child))
                break
        return result

    def _results_sheaf(sheaf):
        for straw in sheaf:
            for result in MQL._results_straw(straw):
                yield result

    def _results_straw(straw):
        if not(len(straw)):
            yield ()
        else:
            for t in MQL._results_grain(straw[0]):
                for a in MQL._results_straw(straw[1:]):
                    yield tuple((t,) + a)

    def _results_grain(grain):
        if len(grain) == 1:
            yield grain[0]
        else:
            for r in MQL._results_sheaf(grain[1]):
                yield (grain[0], r)
                    
    def _render_sheaf(data, indent, monadrep):
        if len(data):
            for (i, elem) in enumerate(data):
                if i>0: print("{}--".format(' '*indent))
                MQL._render_straw(elem, indent+1, monadrep)
        
    def _render_straw(data, indent, monadrep):
        if len(data):
            for elem in data:
                MQL._render_grain(elem, indent+1, monadrep)
            
    def _render_grain(data, indent, monadrep):
        if len(data) == 1:
            print("{}'{}'".format(' '*indent, monadrep(data[0])))
        else:
            print("{}[{}".format(' '*indent, F.otype.v(data[0])))
            MQL._render_sheaf(data[1], indent+1, monadrep)
            print("{}]".format(' '*indent))

    def _compact_sheaf(data, level, monadrep):
        sep = '\n' if level == 0 else ' -- '
        return sep.join([MQL._compact_straw(elem, level+1, monadrep) for elem in data])
            
    def _compact_straw(data, level, monadrep):
        return ' '.join([MQL._compact_grain(elem, level, monadrep) for elem in data])

    def _compact_grain(data, level, monadrep):
        if len(data) == 1:
            return "'{}'".format(monadrep(data[0]))
        else:
            return "[{} {}]".format(F.otype.v(data[0]), MQL._compact_sheaf(data[1], level, monadrep))

    def _compact_results(data, level, monadrep):
        sep = '\n' if level == 0 else ' -- '
        return sep.join([MQL._compact_result(elem, level+1, monadrep) for elem in data])

    def _compact_result(data, level, monadrep):
        return ' '.join([MQL._compact_resgrain(elem, level, monadrep) for elem in data])

    def _compact_resgrain(data, level, monadrep):
        if type(data) == int:
            return "'{}'".format(monadrep(data))
        else:
            return "[{} {}]".format(F.otype.v(data[0]), MQL._compact_result(data[1], level, monadrep))


class Sheaf(object):
    def __init__(self, sheaf): self.data = sheaf
    def render(self, monadrep): MQL._render_sheaf(self.data, 0, monadrep)
    def compact(self, monadrep): return MQL._compact_sheaf(self.data, 0, monadrep)
    def results(self): return MQL._results_sheaf(self.data)
    def compact_results(self, monadrep): return MQL._compact_results(MQL._results_sheaf(self.data), 0, monadrep)
