import os
import collections
import re

class PX(object):
    def __init__(self, API):
        self.API = API
        self.env = API['fabric'].lafapi.names.env
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        ca_labn2id = {}
        ca_id2labn = {}

        cur_subtract = 0
        cur_chapter_cas = 0
        msg("Making mappings between clause atoms in PX and nodes in LAF")
        for n in NN():
            otype = F.otype.v(n)
            if otype == 'verse':
                cur_label = F.label.v(n)
            elif otype == 'chapter':
                cur_subtract += cur_chapter_cas
                cur_chapter_cas = 0
            elif otype == 'book':
                cur_subtract = 0
                cur_chapter_cas = 0
            elif otype == 'clause_atom':
                cur_chapter_cas += 1
                nm = int(F.number.v(n)) - cur_subtract
                ca_labn2id[(cur_label, nm)] = n
                ca_id2labn[n] = (cur_label, nm)
        msg("End making mappings: {}={} clauses".format(len(ca_labn2id), len(ca_id2labn)))
        self.ca_labn2id = ca_labn2id
        self.ca_id2labn = ca_id2labn

    def read_px(self, px_file):
        API = self.API
        msg = API['msg']
        data_dir = API['data_dir']
        data = []
        not_found = set()
        px_handle = open('{}/{}'.format(data_dir, px_file))
        ln = 0
        can = 0
        featurescan = re.compile(r'LineNr\s*([0-9]+).*?Pargr:\s*([0-9.]+)')
        cur_label = None
        data = []
        for line in px_handle:
            ln += 1
            if line.strip()[0] != '*':
                cur_label = line[0:10]
                continue
            can += 1
            features = featurescan.findall(line)
            if len(features) == 0:
                msg("Warning: line {}: no LineNr, Pargr found".format(ln))
            elif len(features) > 1:
                msg("Warning: line {}: multiple LineNr, Pargr found".format(ln))
            else:
                feature = features[0]
                the_n = feature[0]
                the_para = feature[1]
                labn = (cur_label, int(the_n))
                if labn not in self.ca_labn2id:
                    not_found.add(labn)
                    continue
                data.append((self.ca_labn2id[labn], the_n, the_para))
        px_handle.close()
        msg("Read {} paragraph annotations".format(len(data)))
        if not_found:
            msg("Could not find {} label/line entries in index: {}".format(len(not_found), sorted({lab[0] for lab in not_found})))
        else:
            msg("All label/line entries found in index")
        return data
            
    def create_annots(self, data, spec):
        API = self.API
        X = API['X']
        result = []
        result.append('''<?xml version="1.0" encoding="UTF-8"?>
    <graph xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/">
    <graphHeader>
        <labelsDecl/>
        <dependencies/>
        <annotationSpaces/>
    </graphHeader>''')
        aid = 0
        features = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: {})))
        
        (aspace1, alabel1, fname1) = spec[0]
        (aspace2, alabel2, fname2) = spec[1]
        for line in data:
            node = line[0]
            value1 = line[1]
            value2 = line[2]
            xml_id = X.r(node)
            features[aspace1][alabel1][xml_id][fname1] = value1
            features[aspace2][alabel2][xml_id][fname2] = value2
            
        for aspace in features:
            for alabel in features[aspace]:
                for xml_id in features[aspace][alabel]:
                    aid += 1
                    result.append('''<a xml:id="a{}" as="{}" label="{}" ref="{}"><fs>'''.format(aid, aspace, alabel, xml_id))
                    for fname in features[aspace][alabel][xml_id]:
                        value = features[aspace][alabel][xml_id][fname]
                        result.append('\t<f name="{}" value="{}"/>'.format(fname, value))
                    result.append('</fs></a>')
        result.append("</graph>")
        return '\n'.join(result)

    def create_header(self, annox_part):
        result = []
        result.append("""<?xml version="1.0" encoding="UTF-8"?>
    <documentHeader xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/" docId="http://persistent-identifier/?identifier=urn:nbn:nl:ui:13-xxx-999" creator="SHEBANQ" date.created="2013-12-05" version="1.0">
      <fileDesc>
        <titleStmt>
          <title>Literary annotations</title>
        </titleStmt>
        <extent count="0" unit="byte"/>
        <sourceDesc>
          <title>Biblia Hebraica Stuttgartentis</title>
          <author>tradition</author>
          <publisher>Deutsche Bibelgesellschaft</publisher>
          <pubDate value="1900-00-00">1900</pubDate>
          <pubPlace>Germany</pubPlace>
        </sourceDesc>
      </fileDesc>
      <profileDesc>
        <primaryData f.id="f.primary" loc="{source}.txt"/>
        <langUsage>
            <language iso639="hbo"/> <!-- ancient hebrew http://www-01.sil.org/iso639-3/documentation.asp?id=hbo -->
            <language iso639="arc"/> <!-- aramaic http://www-01.sil.org/iso639-3/documentation.asp?id=arc -->
        </langUsage>
        <annotations>
            <annotation f.id="f_{key}" loc="{key}.xml"/>
        </annotations>
      </profileDesc>
    </documentHeader>""".format(key=annox_part, source=self.env['source']))
        
        return '\n'.join(result)

    def deliver_annots(self, px_base, annox, annox_part, specs):
        API = self.API
        data_dir = API['data_dir']
        px_data = self.read_px(px_base)
        annox_dir = "{}/{}/annotations/{}".format(data_dir, self.env['source'], annox)
        if not os.path.exists(annox_dir): os.makedirs(annox_dir)
        with open("{}/_header_.xml".format(annox_dir), "w") as ah: ah.write(self.create_header(annox_part))
        with open("{}/{}.xml".format(annox_dir, annox_part), "w") as ah: ah.write(self.create_annots(px_data, specs))

