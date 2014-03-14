import os
import imp
import sys
import time
import glob
import subprocess
import collections
from .lib import grouper

import array
import pickle

from .settings import Names
from .laf import Laf

class Feature(object):
    def __init__(self, lafapi, feature, kind):
        self.source = lafapi
        self.kind = kind
        data_items = lafapi.data_items
        label = Names.comp('F', 'main', kind, feature)
        alabel = Names.comp('F', 'annox', kind, feature)
        self.lookup = data_items[label] if label in data_items else {}
        self.alookup = data_items[alabel] if alabel in data_items else {}

    def v(self, ne):
        return self.alookup.get(ne, self.lookup(ne))

    def s(self, value=None):
        order = self.source.data_items['node_sort_inv']
        domain = sorted(set(self.lookup) + set(self.alookup), key=lambda x:order[x])
        if value == None:
            for n in domain:
                yield n
        else:
            for n in domain:
                if self.alookup.get(n, self.lookup.get(n)) == value:
                    yield n

class Connection(object):
    def __init__(self, lafapi, feature, inv):
        self.source = lafapi
        self.inv = inv
        data_items = lafapi.data_items
        label = Names.comp('C', 'main', inv, feature)
        alabel = Names.comp('C', 'annox', inv, feature)
        self.lookup = data_items[label] if label in data_items else {}
        self.alookup = data_items[alabel] if alabel in data_items else {}

    def v(self, n):
        lookup = self.lookup
        alookup = self.alookup
        for m in set(lookup.get(n, {})) | set(alookup.get(n, {})):
            yield m

    def vv(self, n):
        lookup = self.lookup
        alookup = self.alookup
        for m in set(lookup.get(n, {})) | set(alookup.get(n, {})):
            yield (m, alookup.get(n, lookup.get(n)).get(m, lookup.get(n).get(m)))

    def endnodes(self, value=None, node_set):
        visited = set()
        result = set()
        next_set = node_set
        while next_set:
            new_next_set = set()
            for node in next_set:
                visited.add(node)
                next_nodes = set(self.v(node)) if value == None else set([n[0] for n in self.vv(node) if n[1] == value])
                if next_nodes:
                    new_next_set |= next_nodes - visited
                else:
                    result.add(node)
            next_set = new_next_set
        return result

class XMLid(object):
    def __init__(self, lafapi, kind):
        self.kind = kind
        data_items = lafapi.data_items
        label = Names.comp('X', 'int', kind, ())
        rlabel = Names.comp('X', 'rep', kind, ())
        self.lookup = data_items[label] if label in data_items else {}
        self.rlookup = data_items[rlabel] if rlabel in data_items else {}

    def r(self, int_code):
        return self.rlookup[int_code]

    def i(self, xml_id):
        return self.lookup[xml_id]

class PrimaryData(object):
    def __init__(self, lafapi):
        self.all_data = lafapi.data_items['primary_data']
        self.lafapi = lafapi

    def data(self, node):
        lafapi = self.lafapi
        regions = lafapi._getitems(lafapi.data_items['node_anchor'], lafapi.data_items['node_anchor_items'], node)
        if not regions:
            return None
        all_text = self.all_data
        result = []
        for r in grouper(regions, 2):
            result.append((r[0], all_text[r[0]:r[1]]))
        return result

class Bunch(object)
    def __init__(self):
        self.item = {}

class LafAPI(Laf):
    def __init__(self, settings):
        Laf.__init__(self, settings)
        self.result_files = []
        cur_dir = os.getcwd()
        task_dir = self.settings['locations']['task_dir']
        task_include_dir = None if task_dir == '<' else task_dir if task_dir.startswith('/') else '{}/{}'.format(cur_dir, task_dir)
        if task_include_dir != None:
            sys.path.append(task_include_dir)

    def API(self):
        api = {}
        api.update(self._api_fcxp())
        api.update(self._api_nodes())
        api.update(self._api_io())
        self._api_prep(api)
        return api

    def_api_fcxp(self):
        env = self.settings.env
        data_items = self.data_items

        api = {
            'F': Bunch(),
            'FE': Bunch(),
            'C': Bunch(),
            'Ci': Bunch(),
        }

        features = {'node': set(), 'edge': set()}
        connections = {False: set(), True: set()}

        for dkey in data_items:
            (d, start, end, comps) = Names.decomp(dkey)
            if d == 'F':
                features[end].add(comps)
            elif d == 'C':
                connections[end].add(comps)
            elif d == 'X':
                api[dkey] = XMLid(self, end)
            elif d == 'primary_data':
                api['P'] = PrimaryData(self)

        for kind in features:
            for feat in features[kind]:
                name = Names.apiname(feat) 
                obj = Feature(self, feat, kind)
                dest = api['FE'] if kind == 'edge' else api['F']
                dest.item[name] = obj
                setattr(dest, name, obj)

        for inv in connections:
            for conn in connections[inv]:
                name = Names.apiname(conn) 
                obj = Connection(self, conn, inv)
                dest = api['Ci'] if inv else api['C']
                dest.item[name] = obj
                setattr(dest, name, obj)

        loadables = set()
        for data in ('main', 'annox')
            for feat_path in glob.glob('{}/*'.format(env['{}_compiled_dir'.format(data)])):
                loadables.add(os.path.basename(feat_path))

        all_features = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        for filename in loadables:
            (d, start, end, comps) = Names.decomp(filename)
            if d != 'F': continue
            (namespace, label, name) = comps
            all_features[end][namespace].add("{}.}".format(label, name))

        def feature_list(kind):
            result = []
            for namespace in sorted(all_features[kind]):
                result.append((namespace, sorted(all_features[kind][namespace])))

        prep = lambda task, lab, myfile: self.prep_data(api, task, lab, myfile)

        api.update({
            'Fall_node': feature_list['node'],
            'Fall_edge': feature_list['node'],
        })

    def _api_prep(self, api):
        def prep_data(method, lab, myfile):
            '''Loads custom data from disk, if present. If not prepares custom data and stores it on disk.

            LAF-Fabric cannot precompute application specific data.
            If an application needs to compute data over and over again, it may ask LAF-Fabric to store it alongside the compiled data.
            For example, the order of nodes by LAF-Fabric is rather crude, an application may provide a better ordering.

            Only data that is anticipated by LAF-Fabric can be stored in this way. 
            The intention is that you can override LAF-Fabric data, not that you add arbitrary data.
            If LAF-Fabric does not know your data, you can store it easily outside LAF-Fabric.

            Args:
                api (dict):
                    the LAF-Fabric api. Needed by *method*.
                method (callable):
                    Custom function defined in an other application that computes the new data.
                    It will be passed the *api* parameter, so that the function has access to all LAF-Fabric's data and methods.
                lab (string):
                    label, known by LAF-Fabric (defined in the attribute ``preparables``.
                    The custom data will be stored under this label.
                myfile (string):
                    Full path to the file that defined the *method* function.
                    In order to decide whether the custom data is still up to date,
                    the modification times of this file and the custom data file will be compared.
            '''

            if lab not in self.preparables:
                self.progress("WARNING: Cannot prepare data in {}.".format(lab))
                return
            lab_type = self.preparables[lab]
            if lab_type == 'array':
                self.data_items[lab] = array.array('I')
            else:
                self.data_items[lab] = {}
            b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
            s_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.TEXT_EXT)
            up_to_date = os.path.exists(b_path) and os.path.exists(s_path) and os.path.getmtime(b_path) >= os.path.getmtime(myfile)
            if up_to_date:
                self.progress("LOADING {} (prepared)".format(lab), verbose='INFO')
                with open(s_path, 'r', encoding="utf-8") as x: n = int(x.read())
                b_handle = gzip.open(b_path, "rb")
                self.data_items[lab].fromfile(b_handle, n)
            else:
                self.progress("PREPARING {}".format(lab), verbose='INFO')
                self.data_items[lab] = method(api)
                self.progress("WRITING {} (prepared)".format(lab), verbose='INFO')
                with open(s_path, "w", encoding='utf-8') as x: x.write(str(len(self.data_items[lab])))
                b_handle = gzip.open(b_path, "wb", compresslevel=GZIP_LEVEL)
                self.data_items[lab].tofile(b_handle)
                b_handle.close()

    def _api_nodes(self):
        data_items = self.data_items
        node_anchor_min = data_items["node_anchor_min"]
        node_anchor_max = data_items["node_anchor_max"]

        def before(nodea, nodeb):
            if node_anchor_min[nodea] == node_anchor_max[nodea] or node_anchor_min[nodeb] == node_anchor_max[nodeb]: return None
            if node_anchor_min[nodea] < node_anchor_min[nodeb]: return True
            if node_anchor_min[nodea] > node_anchor_min[nodeb]: return False
            if node_anchor_max[nodea] > node_anchor_max[nodeb]: return True
            if node_anchor_max[nodea] < node_anchor_max[nodeb]: return False
            return None

        def next_node(test=None, value=None, values=None, extrakey=None):
            class Extra_key(object):
                __slots__ = ['value', 'amin', 'amax']
                def __init__(self, node):
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = extrakey(node)

                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        self.value == other.value
                    )
                __hash__ = None

            original = data_items['node_sort']
            new = data_items['node_resorted'] if 'node_resorted' in data_items else original
            given = new if new else original

            if extrakey != None:
                self.progress("Resorting {} nodes...".format(len(given)))
                given = sorted(given, key=Extra_key)
                self.progress("Done")

            if test != None:
                test_values = {}
                if value != None:
                    test_values[value] = None
                if values != None:
                    for val in values:
                        test_values[val] = None
                for node in given:
                    if test(node) in test_values:
                        yield node
            else:
                for node in given:
                    yield node

        def no_next_event(key=None, simplify=None):
            self.progress("ERROR: Node events not available because primary data is not loaded.")
            return None

        def next_event(key=None, simplify=None):
            class Additional_key(object):
                __slots__ = ['value', 'kind', 'amin', 'amax']
                def __init__(self, event):
                    (node, kind) = event
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = key(node) * (-1 if kind < 2 else 1)
                    self.kind = kind

                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        (self.kind != other.kind and (self.amin != self.amax or other.amin != other.amax)) or
                        self.value == other.value
                    )
                __hash__ = None

            nodes = data_items["node_events_n"]
            kinds = data_items["node_events_k"]
            node_events = data_items["node_events"]
            node_events_items = data_items["node_events_items"]
            bufferevents = collections.deque([(-1, [])], 2)
            
            active = {}
            for anchor in range(len(node_events)):
                event_ids = self._getitems(node_events, node_events_items, anchor)
                if len(event_ids) == 0:
                    continue
                eventset = []
                for event_id in event_ids:
                    node = nodes[event_id]
                    if key == None or key(node) != None:
                        eventset.append((nodes[event_id], kinds[event_id]))
                if not eventset:
                    continue
                if key != None:
                    eventset = sorted(eventset, key=Additional_key)
                if simplify == None:
                    yield (anchor, eventset)
                    continue

                bufferevents.append([anchor, eventset])
                if bufferevents[0][0] == -1:
                    continue
                (this_anchor, these_events) = bufferevents[0]
                (next_anchor, next_events) = bufferevents[1]
                deleted = {}
                for (n, kind) in these_events:
                    if simplify(n):
                        if kind == 3:
                            deleted[n] = None
                        elif kind == 2:
                            active[n] = False
                        elif kind == 1:
                            active[n] = True
                        elif kind == 0:
                            active[n] = True
                for n in deleted:
                    if n in active:
                        del active[n]
                if True not in active.values():
                    weed = collections.defaultdict(lambda: False)
                    for (n, k) in these_events:
                        if k == 2:
                            weed[n] = None
                    for (n, k) in next_events:
                        if k == 1:
                            if n in weed:
                                weed[n] = True
                    if True in weed.values():
                        bufferevents[0][1] = [(n, k) for (n, k) in these_events if not (k == 2 and weed[n])] 
                        bufferevents[1][1] = [(n, k) for (n, k) in next_events if not (k == 1 and weed[n])] 
                yield (bufferevents[0])
            yield (bufferevents[1])

        api.update({
            'BF':      before
            'NN':      next_node,
            'NE':      next_event if 'node_events' in data_items else no_next_event,
            'prep':    prep,
        })

    def _api_io(self):
        env = self.settings.env
        task_dir = env['task_dir']

        def add_output(file_name):
            result_file = "{}/{}".format(task_dir, file_name)
            handle = open(result_file, "w", encoding="utf-8")
            self.result_files.append(handle)
            return handle

        def add_input(file_name):
            result_file = "{}/{}".format(task_dir, file_name)
            handle = open(result_file, "r", encoding="utf-8")
            self.result_files.append(handle)
            return handle

        def result(file_name=None):
            if file_name == None:
                return task_dir
            else:
                return "{}/{}".format(task_dir, file_name)

        def finish_task():
            for handle in self.result_files:
                if handle and not handle.closed:
                    handle.close()
            self.result_files = []
            self.flush_logfile()

            msg = []
            self.progress("Results directory:\n{}".format(task_dir))
            for name in sorted(os.listdir(path=task_dir)):
                path = "{}/{}".format(task_dir, name) 
                size = os.path.getsize(path)
                mtime = time.ctime(os.path.getmtime(path))
                msg.append("{:<30} {:>12} {}".format(name, size, mtime))
            self.progress("\n".join(msg), withtime=False)
            self.finish_logfile()

        api = {
            'infile':  add_input,
            'outfile': add_output,
            'my_file': result,
            'msg':     self.progress,
        }
        return api

    def _getitems(self, data, data_items, elem):
        data_items_index = data[elem]
        n_items = data_items[data_items_index]
        return data_items[data_items_index + 1:data_items_index + 1 + n_items]

    def __del__(self):
        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Laf.__del__(self)


