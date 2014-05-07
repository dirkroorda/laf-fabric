import collections
import copy
from .lib import monad_set, object_rank

class Tree(object):
    def __init__(self, API, otypes=None, clause_type=None, phrase_type=None,
            ccr_feature='clause_constituent_relation', pt_feature='phrase_type', pos_feature='part_of_speech', mother_feature="mother."
        ):
        node_features = "otype monads minmonad {} {}".format(
            ccr_feature if ccr_feature != None else '',
            pt_feature if pt_feature != None else '',
            pos_feature if pos_feature != None else ''
        )
        edge_features = mother_feature if mother_feature != None else ''
        API['fabric'].load_again({"features":
            (node_features, edge_features)}, add=True)
        self.API = API
        self.ccr_feature = ccr_feature
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        if otypes == None: otypes = sorted(object_rank, key=lambda x: object_rank[x])
        if clause_type == None: clause_type = 'clause'
        if phrase_type == None: phrase_type = 'phrase'
        self.root_type = otypes[0]
        self.leaf_type = otypes[-1]
        self.clause_type = clause_type
        self.phrase_type = phrase_type
        msg("Start computing parent and children relations for objects of type {}".format(', '.join(otypes)))
        otype_set = set(otypes)
        self.otype_set = otype_set
        base_type = otypes[-1]
        cur_stack = []
        eparent = {}
        echildren = collections.defaultdict(lambda: [])
        nn = 0
        cn = 0
        chunk = 100000
        for node in NN():
            otype = F.otype.v(node)
            if otype not in otype_set: continue
            nn += 1
            cn += 1
            if cn == chunk:
                msg("{} nodes".format(nn))
                cn = 0
            nm_set = monad_set(F.monads.v(node))
            nm_min = min(nm_set)
            nm_max = max(nm_set)
            ls = len(cur_stack)
            tobe_removed = set()
            for si in range(ls):
                act_on = ls -si - 1
                (snode, sm_set, sm_max) = cur_stack[act_on]
                if nm_min > sm_max:
                    tobe_removed.add(act_on)
                    continue
                if nm_set <= sm_set:
                    eparent[node] = snode
                    echildren[snode].append(node)
                    break;
            cur_stack = [cur_stack[i] for i in range(len(cur_stack)) if i not in tobe_removed]
            if otype != base_type: cur_stack.append((node, nm_set, nm_max))
        msg("{} nodes: {} have parents and {} have children".format(nn, len(eparent), len(echildren)))
        self.eparent = eparent
        self.echildren = echildren
        self.elder_sister = {}
        self.rparent = {}
        self.rchildren = {}
        self.sisters = {}
        self.elder_sister = {}
        self.mother = {}

    def restructure_clauses(self, ccr_class):
        API = self.API
        NN = API['NN']
        F = API['F']
        C = API['C']
        msg = API['msg']
        msg("Restructuring {}s: deep copying tree relations".format(self.clause_type))
        rparent = copy.deepcopy(self.eparent)
        rchildren = copy.deepcopy(self.echildren)
        sisters = collections.defaultdict(lambda: [])
        elder_sister = {}
        mother = {}
        self.rparent = rparent
        self.rchildren = rchildren
        self.sisters = sisters
        self.elder_sister = elder_sister
        self.mother = mother
        if self.ccr_feature == None: return

        msg("Pass 0: Storing mother relationship")
        moutside = collections.defaultdict(lambda: 0)
        mo = 0
        mf = C.item['mother_'].v
        for c in NN(test=F.otype.v, value=self.clause_type):
            lms = list(mf(c))
            ms = len(lms)
            if ms:
                m = lms[0]
                mtype = F.otype.v(m)
                if mtype in self.otype_set: mother[c] = m
                else:
                    moutside[mtype] += 1
                    mo += 1
        msg("{} {}s have a mother".format(len(mother), self.clause_type))
        if mo:
            msg("{} {}s have mothers of types outside {}.\nThese mother relationships will be ignored".format(mo, self.clause_type, self.otype_set))
            for mt in sorted(moutside):
                msg("{} mothers point to {} nodes".format(moutside[mt], mt), withtime=False)
        else:
            msg("All {}s have mothers of types in {}".format(self.clause_type, self.otype_set))

        msg("Pass 1: all {}s except those of type Coor".format(self.clause_type))
        motherless = set()
        ccrf = F.item[self.ccr_feature].v
        for cnode in NN(test=F.otype.v, value=self.clause_type):
            cclass = ccr_class[ccrf(cnode)]
            if cclass == 'n' or cclass == 'x': pass
            elif cclass == 'r':
                if cnode not in mother:
                    motherless.add(cnode)
                    continue
                mnode = mother[cnode]
                mtype = F.otype.v(mnode)
                pnode = rparent[cnode]
                if mnode not in rparent:
                    msg("Should not happen: node without parent: [{} {}]({}) =mother=> [{} {}]({}) =/=> parent".format(
                        self.clause_type, F.monads.v(cnode), cnode, mtype, F.monads.v(mnode), mnode
                    ))
                pmnode = rparent[mnode]
                pchildren = rchildren[pnode]
                mchildren = rchildren[mnode]
                pmchildren = rchildren[pmnode]
                deli = pchildren.index(cnode)
                if mtype == self.leaf_type:
                    if pnode != pmnode:
                        rparent[cnode] = pmnode
                        del pchildren[deli:deli+1]
                        pmchildren.append(cnode)
                else:
                    if pnode != mnode:
                        rparent[cnode] = mnode
                        del pchildren[deli:deli+1]
                        mchildren.append(cnode)
        msg("Pass 2: {}s of type Coor only".format(self.clause_type))
        for cnode in NN(test=F.otype.v, value=self.clause_type):
            cclass = ccr_class[ccrf(cnode)]
            if cclass != 'x': continue
            if cnode not in mother:
                motherless.add(cnode)
                continue
            mnode = mother[cnode]
            pnode = rparent[cnode]
            pchildren = rchildren[pnode]
            deli = pchildren.index(cnode)
            sisters[mnode].append(cnode)
            elder_sister[cnode] = mnode
            del rparent[cnode]
            del pchildren[deli:deli+1]
        sister_count = collections.defaultdict(lambda: 0)
        for n in sisters:
            sns = sisters[n]
            sister_count[len(sns)] += 1
        msg("Mothers applied. Found {} motherless {}s.".format(len(motherless), self.clause_type))
        ts = 0
        for l in sorted(sister_count):
            c = sister_count[l]
            ts += c * l
            msg("{} nodes have {} sisters".format(c, l))
        msg("There are {} sisters, {} nodes have sisters.".format(ts, len(sisters)))
        motherless = None

    def relations(self): return {
        'eparent': self.eparent,
        'echildren': self.echildren,
        'rparent': self.rparent,
        'rchildren': self.rchildren,
        'sisters': self.sisters,
        'elder_sister': self.elder_sister,
        'mother': self.mother,
    }

    def debug_write_tree(self, node, kind, legenda=False):
        API = self.API
        F = API['F']
        msg = API['msg']
        result = []
        ids = {}
        maxid = 0
        bmonad = int(F.minmonad.v(node))

        def rep(n):
            if n in ids: return ids[n]
            nonlocal maxid
            maxid += 1
            ids[n] = maxid
            return maxid

        def _fillids(node):
            otype = F.otype.v(node)
            parent = self.eparent 
            mother = self.mother
            children = self.echildren 
            if node in mother: rep(mother[node])
            rep(node)
            if node in children:
                for cnode in children[node]:
                    _fillids(cnode)

        def _debug_write_tree(node, level, indent, kind):
            otype = F.otype.v(node)
            children = self.rchildren if kind == 'r' else self.echildren 
            sisters = self.sisters
            elder_sister = self.elder_sister
            mother = self.mother
            subtype = ''
            subtype_sep = ''
            mspec = ''
            if otype == self.clause_type:
                ccrf = F.item[self.ccr_feature].v
                subtype = ccrf(node)
                if subtype != None and subtype != 'none':
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
                if kind == 'e':
                    if node in mother:
                        mspec = '=> ({:>3})'.format(rep(mother[node]))
                elif kind == 'r':
                    if node in elder_sister:
                        mspec = '=> ({:>3})'.format(rep(elder_sister[node]))
            elif otype == self.phrase_type:
                subtype = F.phrase_type.v(node)
                if subtype != None:
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
            elif otype == self.leaf_type:
                posf = F.item[self.pos_feature].v
                subtype = posf(node)
                if subtype != None:
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
            monads = F.monads.v(node)
            rangesi = [[int(a)-bmonad for a in r.split('-')] for r in monads.split(',')] 
            monadss = ','.join('-'.join(str(a) for a in r) for r in rangesi)

            result.append("{:>2}{:<30} {:<10}] ({:>3}) {:<8} <{}>\n".format(
                level,
                "{}[{:<10}".format(indent, "{}{}{}".format(otype, subtype_sep, subtype)),
                monadss, rep(node), mspec,
                ','.join("{:>3}".format(rep(c)) for c in children[node]),
            ))
            has_sisters = node in sisters and len(sisters[node])
            has_children = node in children and len(children[node])
            if kind == 'r' and has_sisters:
                for cnode in children[node]: _debug_write_tree(cnode, level + 1, indent + '  ', kind)
                for snode in sisters[node]: _debug_write_tree(snode, level, indent + '*', kind)
            elif has_children:
                for cnode in children[node]: _debug_write_tree(cnode, level + 1, indent + '  ', kind)
        _fillids(node)
        _debug_write_tree(node, 0, '', kind)
        if legenda:
            result.append("\nstart monad = {}\n\n".format(bmonad))
            result.append("{:>3} = {:>8} {:>8}\n".format('#', 'bhs_oid', 'laf_nid'))
            for (n, s) in sorted(ids.items(), key=lambda x: x[1]):
                result.append("{:>3} = {:>8} {:>8}\n".format(s, F.oid.v(n), n))
        return ''.join(result)

    def write_tree(self, node, kind, get_tag, rev=False, leafnumbers=True):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.otype.v(node)
        children = self.rchildren if kind == 'r' else self.echildren 
        sisters = self.sisters
        bmonad = int(F.minmonad.v(node))

        words = []
        sequential = []
        def _write_tree(node, kind):
            (tag, pos, monad, text, is_word) = get_tag(node)
            if is_word:
                sequential.append(("W", len(words)))
                words.append((monad - bmonad, text, pos))
            else: sequential.append(("O", tag))
            has_sisters = node in sisters and len(sisters[node])
            has_children = node in children and len(children[node])
            if kind == 'r' and has_sisters:
                sequential.append(("O", 'Ccoor'))
                for c in children[node]: _write_tree(c, kind)
                sequential.append(("C", 'Ccoor'))
                for s in sisters[node]: _write_tree(s, kind)
            elif has_children:
                for c in children[node]: _write_tree(c, kind)
            if not is_word: sequential.append(("C", tag))

        def do_sequential():
            if leafnumbers: word_rep = ' '.join(x[1] for x in sorted(words, key=lambda x: x[0]))
            else: word_rep = ' '.join(str(x[0]) for x in words)
                            
            tree_rep = []
            for (code, info) in sequential:
                if code == 'O' or code == 'C':
                    if code == 'O': tree_rep.append('({}'.format(info))
                    else: tree_rep.append(')')
                elif code == 'W':
                    (monad, text, pos) = words[info]
                    leaf = monad if leafnumbers else text[::-1] if rev else text
                    tree_rep.append('({} {})'.format(pos, leaf))
            return (''.join(tree_rep), word_rep[::-1] if rev and leafnumbers else word_rep, bmonad) 

        _write_tree(node, kind)
        return do_sequential()

    def depth(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        def _depth(node, kind):
            parent = self.rparent if kind == 'r' else self.eparent 
            children = self.rchildren if kind == 'r' else self.echildren 
            sisters = self.sisters
            elder_sister = self.elder_sister
            has_sisters =  node in sisters and len(sisters[node])
            has_children = node in children and len(children[node])
            cdepth = 1 + max(_depth(c, kind) for c in children[node]) if has_children else 0
            sdepth = 1 + max(_depth(s, kind) for s in sisters[node]) if has_sisters else 0
            if kind == 'e': return cdepth
            elif kind == 'r': return max(cdepth + 1, sdepth) if has_sisters else cdepth
        return _depth(node, kind)

    def get_leaves(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        result = []

        def _get_leaves(node, kind):
            parent = self.rparent if kind == 'r' else self.eparent 
            children = self.rchildren if kind == 'r' else self.echildren 
            sisters = self.sisters
            elder_sister = self.elder_sister
            if node in children and len(children[node]) > 0:
                for cnode in children[node]:
                    _get_leaves(cnode, kind)
            else: result.append(node)
            if kind == 'r' and node in sisters:
                for snode in sisters[node]:
                    _get_leaves(snode, kind)
        _get_leaves(node, kind)
        return result

    def get_root(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.otype.v(node)
        parent = self.rparent if kind == 'r' else self.eparent 
        children = self.rchildren if kind == 'r' else self.echildren 
        if node in parent: return self.get_root(parent[node], kind)
        if kind == 'r':
            if node in elder_sister: return self.get_root(elder_sister[node], kind)
        return (node, otype)
    
