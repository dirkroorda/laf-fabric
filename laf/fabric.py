import os
import glob
import collections
from .lib import make_array_inverse
from .names import Names
from .data import LafData
from .elements import Feature, Connection, XMLid, PrimaryData

class LafAPI(LafData):
    '''Makes all API methods available.
    ``API()`` returns a dict keyed by mnemonics and valued by API methods.
    '''
    def __init__(self, names):
        self.names = names
        self.stamp = names.stamp
        LafData.__init__(self)
        self.result_files = []

    def API(self):
        self.api = {}
        self._api_fcxp()
        self._api_nodes()
        self._api_io()
        self._api_prep()
        return self.api

    def _api_fcxp(self):
        data_items = self.data_items
        api = {
            'F': Bunch(),
            'FE': Bunch(),
            'C': Bunch(),
            'Ci': Bunch(),
        }
        features = {'n': set(), 'e': set()}
        connections = {'f': set(), 'b': set()}
        xmlmaps = {'n': set(), 'e': set()}
        for dkey in data_items:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dgroup == 'F': features[dkind].add(dcomps)
            elif dgroup == 'C': connections[ddir].add(dcomps)
            elif dgroup == 'X': xmlmaps[dkind].add(dcomps)
            elif dgroup == 'P' and dcomps[0] == 'primary_data': api['P'] = PrimaryData(self)
        self.feature_abbs = collections.defaultdict(lambda: set())
        self.feature_abb = {}
        for kind in sorted(features):
            for feat in sorted(features[kind]):
                name = Names.apiname(feat) 
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb:
                        self.feature_abbs[abb].add(name)
                        self.feature_abb[abb] = name
        for abb in self.feature_abbs:
            expansions = self.feature_abbs[abb]
            chosen = self.feature_abb[abb]
            if len(expansions) > 1:
                self.stamp.Imsg("Feature {} refers to {}, not to {}".format(abb, chosen, ', '.join(sorted(expansions - set([chosen])))))
        for kind in features:
            for feat in features[kind]:
                name = Names.apiname(feat) 
                obj = Feature(self, feat, kind)
                dest = api['FE'] if kind == 'e' else api['F']
                dest.item[name] = obj
                setattr(dest, name, obj)
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb and self.feature_abb.get(abb, '') == name: setattr(dest, abb, obj)
        for inv in connections:
            for feat in connections[inv]:
                name = Names.apiname(feat) 
                obj = Connection(self, feat, inv)
                dest = api['C'] if inv == 'f' else api['Ci'] if inv == 'b' else None
                dest.item[name] = obj
                setattr(dest, name, obj)
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb and self.feature_abb.get(abb, '') == name: setattr(dest, abb, obj)
        for kind in xmlmaps:
            for comp in xmlmaps[kind]:
                obj = XMLid(self, kind)
                dest = 'XE' if kind == 'e' else 'X'
                api[dest] = obj
        loadables = set()
        for origin in ('m', 'a'):
            for feat_path in glob.glob('{}/*'.format(self.names.env['{}_compiled_dir'.format(origin)])):
                filename = os.path.basename(feat_path)
                if filename.startswith(('_', 'A', 'Z')): continue
                loadables.add('{}{}'.format(origin, filename))
        all_features = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        for filename in loadables:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(filename)
            if dgroup != 'F': continue
            (namespace, label, name) = dcomps
            all_features[dkind][namespace].add("{}.{}".format(label, name))

        def feature_list(kind):
            result = []
            for namespace in sorted(all_features[kind]):
                result.append((namespace, sorted(all_features[kind][namespace])))
            return result

        def pretty_fl(flist):
            result = []
            for ((namespace, features)) in flist:
                result.append('{}:'.format(namespace))
                for feature in features:
                    result.append('\t{}:'.format(feature))
            return '\n'.join(result)

        api.update({
            'F_all': feature_list('n'),
            'fF_all': pretty_fl(feature_list('n')),
            'FE_all': feature_list('e'),
            'fFE_all': pretty_fl(feature_list('e')),
        })
        self.api.update(api)

    def _api_prep(self):
        data_items = self.data_items
        api = self.api
        api['make_array_inverse'] = make_array_inverse
        api['data_items'] = data_items

    def _api_nodes(self):
        data_items = self.data_items
        node_anchor_min = data_items[Names.comp('mG00', ('node_anchor_min',))]
        node_anchor_max = data_items[Names.comp('mG00', ('node_anchor_max',))]

        def before(nodea, nodeb):
            if node_anchor_min[nodea] == node_anchor_max[nodea] or node_anchor_min[nodeb] == node_anchor_max[nodeb]: return None
            if node_anchor_min[nodea] < node_anchor_min[nodeb]: return True
            if node_anchor_min[nodea] > node_anchor_min[nodeb]: return False
            if node_anchor_max[nodea] > node_anchor_max[nodeb]: return True
            if node_anchor_max[nodea] < node_anchor_max[nodeb]: return False
            return None

        def next_node(nodes=None, test=None, value=None, values=None, extrakey=None):
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

            order = data_items[Names.comp('mG00', ('node_sort',))]
            order_key = data_items[Names.comp('mG00', ('node_sort_inv',))]
            the_nodes = sorted(nodes, key=lambda x: order_key[x]) if nodes else order

            if extrakey != None:
                self.stamp.Imsg("Resorting {} nodes...".format(len(the_nodes)))
                the_nodes = sorted(the_nodes, key=Extra_key)
                self.stamp.Imsg("Done")
            if test != None:
                test_values = set(([value] if value != None else []) + (list(values) if values != None else []))
                if len(test_values):
                    for node in the_nodes:
                        if test(node) in test_values: yield node
                else:
                    for node in the_nodes:
                        if test(node): yield node
            else:
                for node in the_nodes: yield node

        def no_next_event(key=None, simplify=None):
            self.stamp.Emsg("Node events not available because primary data is not loaded.")
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

            nodes = data_items[Names.comp('mP00', ('node_events_n',))]
            kinds = data_items[Names.comp('mP00', ('node_events_k',))]
            node_events = data_items[Names.comp('mP00', ('node_events',))]
            node_events_items = data_items[Names.comp('mP00', ('node_events_items',))]
            bufferevents = collections.deque([(-1, [])], 2)

            active = {}
            for anchor in range(len(node_events)):
                event_ids = self._getitems(node_events, node_events_items, anchor)
                if len(event_ids) == 0: continue
                eventset = []
                for event_id in event_ids:
                    node = nodes[event_id]
                    if key == None or key(node) != None: eventset.append((nodes[event_id], kinds[event_id]))
                if not eventset: continue
                if key != None: eventset = sorted(eventset, key=Additional_key)
                if simplify == None:
                    yield (anchor, eventset)
                    continue
                bufferevents.append([anchor, eventset])
                if bufferevents[0][0] == -1: continue
                (this_anchor, these_events) = bufferevents[0]
                (next_anchor, next_events) = bufferevents[1]
                deleted = {}
                for (n, kind) in these_events:
                    if simplify(n):
                        if kind == 3: deleted[n] = None
                        elif kind == 2: active[n] = False
                        elif kind == 1: active[n] = True
                        elif kind == 0: active[n] = True
                for n in deleted:
                    if n in active: del active[n]
                if True not in active.values():
                    weed = collections.defaultdict(lambda: False)
                    for (n, k) in these_events:
                        if k == 2: weed[n] = None
                    for (n, k) in next_events:
                        if k == 1:
                            if n in weed: weed[n] = True
                    if True in weed.values():
                        bufferevents[0][1] = [(n, k) for (n, k) in these_events if not (k == 2 and weed[n])] 
                        bufferevents[1][1] = [(n, k) for (n, k) in next_events if not (k == 1 and weed[n])] 
                yield (bufferevents[0])
            yield (bufferevents[0])

        self.api.update({
            'BF':      before,
            'NN':      next_node,
            'NE':      next_event if Names.comp('mP00', ('node_events',)) in data_items else no_next_event,
        })

    def _api_io(self):
        task_dir = self.names.env['task_dir']

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
            if file_name == None: return task_dir
            else: return "{}/{}".format(task_dir, file_name)

        api = {
            'infile':  add_input,
            'outfile': add_output,
            'close':   self.finish_task,
            'my_file': result,
            'msg':     self.stamp.raw_msg,
        }
        self.api.update(api)

    def _getitems(self, data, data_items, elem):
        data_items_index = data[elem]
        n_items = data_items[data_items_index]
        return data_items[data_items_index + 1:data_items_index + 1 + n_items]

    def __del__(self):
        for handle in self.result_files:
            if handle and not handle.closed: handle.close()
        LafData.__del__(self)

class Bunch(object):
    def __init__(self): self.item = {}

class LafFabric(object):
    '''Process manager.

    ``load(params)``: given the source, annox and task, loads the data, assembles the API, and returns the API.
    '''
    def __init__(self, work_dir=None, laf_dir=None, save=False, verbose=None):
        self.lafapi = LafAPI(Names(work_dir, laf_dir, save, verbose))
        self.lafapi.stamp.reset()
        self.api = {}

    def load(self, source, annox, task, load_dict, compile_main=False, compile_annox=False, verbose=None):
        self.api.clear()
        lafapi = self.lafapi
        self.lafapi.stamp.reset()
        if verbose: self.lafapi.stamp.set_verbose(verbose)
        lafapi.stamp.Nmsg("LOADING API: please wait ... ")
        lafapi.names.setenv(source=source, annox=annox, task=task)
        env = lafapi.names.env
        req_items = {}
        lafapi.names.request_init(req_items)
        if 'primary' in load_dict and load_dict['primary']: req_items['mP00'] = True
        if 'xmlids' in load_dict:
            for kind in [k[0] for k in load_dict['xmlids'] if load_dict['xmlids'][k]]:
                for ddir in ('f', 'b'): req_items['mX{}{}'.format(kind, ddir)].append(())
        if 'features' in load_dict: LafFabric._request_features(load_dict['features'], req_items, annox!=env['empty'])
        lafapi.adjust_all(source, annox, task, req_items, {'m': compile_main, 'a': compile_annox})
        self.api.update(lafapi.API())
        if 'prepare' in load_dict: lafapi.prepare_all(self.api, load_dict['prepare'])
        lafapi.stamp.Imsg("DATA LOADED FROM SOURCE {} AND ANNOX {} FOR TASK {}".format(env['source'], env['annox'], env['task']))
        lafapi.stamp.reset()
        self.localnames = '\n'.join(["{key} = {{var}}.api['{key}']".format(key=key) for key in self.api])
        return self.api

    def load_again(self, load_dict, compile_main=False, compile_annox=False, verbose=None):
        env = self.lafapi.names.env
        return self.load(env['source'], env['annox'], env['task'], load_dict, compile_main=compile_main, compile_annox=compile_annox, verbose=verbose)

    def _request_features(feat_dict, req_items, also_from_annox):
        for aspace in feat_dict:
            for kind in feat_dict[aspace]:
                for line in feat_dict[aspace][kind]:
                    (alabel, fnamestring) = line.split('.')
                    fnames = fnamestring.split(',')
                    for fname in fnames:
                        the_feature = (aspace, alabel, fname)
                        for origin in ['m'] + (['a'] if also_from_annox else []):
                            req_items['{}F{}0'.format(origin, kind[0])].append(the_feature)
                            if kind[0] == 'e':
                                for ddir in ('f', 'b'): req_items['{}C0{}'.format(origin, ddir)].append(the_feature)
