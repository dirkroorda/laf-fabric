import collections
import copy
from .lib import monad_set, object_rank

class Tree(object):
    def __init__(self, API, otypes=None):
        API['fabric'].load_again({"features": ("otype monads minmonad","mother.")}, add=True)
        self.API = API
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        if otypes == None:
            otypes = sorted(object_rank, key=lambda x: object_rank[x])
        msg("Start computing parent and children relations for objects of type {}".format(', '.join(otypes)))
        otype_set = set(otypes)
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
        msg("Restructuring clauses: deep copying tree relations")
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

        msg("Pass 0: Storing mother relationship")
        for c in NN(test=F.otype.v, value='clause'):
            lms = list(C.mother_.v(c))
            ms = len(lms)
            if ms:
                mother[c] = lms[0]
        msg("{} clauses have a mother".format(len(mother)))

        msg("Pass 1: all clauses except those of type Coor")
        motherless = set()
        for cnode in NN(test=F.otype.v, value='clause'):
            cclass = ccr_class[F.clause_constituent_relation.v(cnode)]
            if cclass == 'n' or cclass == 'x': pass
            elif cclass == 'p' or cclass == 'c':
                if cnode not in mother:
                    motherless.add(cnode)
                    continue
                mnode = mother[cnode]
                mtype = F.otype.v(mnode)
                pnode = rparent[cnode]
                if mnode not in rparent:
                    msg("Should not happen: node without parent: [{} {}]({}) =mother=> [{} {}]({}) =/=> parent".format(
                        'clause', F.monads.v(cnode), cnode, mtype, F.monads.v(mnode), mnode
                    ))
                pmnode = rparent[mnode]
                pchildren = rchildren[pnode]
                mchildren = rchildren[mnode]
                pmchildren = rchildren[pmnode]
                deli = pchildren.index(cnode)
                if mtype == 'word':
                    if pnode != pmnode:
                        rparent[cnode] = pmnode
                        del pchildren[deli:deli+1]
                        pmchildren.append(cnode)
                else:
                    if pnode != mnode:
                        rparent[cnode] = mnode
                        del pchildren[deli:deli+1]
                        mchildren.append(cnode)
        msg("Pass 2: clauses of type Coor only")
        for cnode in NN(test=F.otype.v, value='clause'):
            cclass = ccr_class[F.clause_constituent_relation.v(cnode)]
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
        msg("Mothers applied. Found {} motherless clauses.".format(len(motherless)))
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

        def _debug_write_tree(node, indent, kind):
            otype = F.otype.v(node)
            children = self.rchildren if kind == 'r' else self.echildren 
            sisters = self.sisters
            elder_sister = self.elder_sister
            mother = self.mother
            ccr = ''
            ccr_sep = ''
            mspec = ''
            if otype == 'clause':
                ccr = F.clause_constituent_relation.v(node)
                if ccr != None and ccr != 'none':
                    ccr_sep = '.'
                else:
                    ccr = ''
                    ccr_sep = ''
                if kind == 'e':
                    if node in mother:
                        mspec = '=> ({:>3})'.format(rep(mother[node]))
                elif kind == 'r':
                    if node in elder_sister:
                        mspec = '=> ({:>3})'.format(rep(elder_sister[node]))
            monads = F.monads.v(node)
            rangesi = [[int(a)-bmonad for a in r.split('-')] for r in monads.split(',')] 
            monadss = ','.join('-'.join(str(a) for a in r) for r in rangesi)

            result.append("{:<30} {:<10}] ({:>3}) {:<8} <{}>\n".format("{}[{:<10}".format(indent, "{}{}{}".format(otype, ccr_sep, ccr)), monadss, rep(node), mspec, ','.join("{:>3}".format(rep(c)) for c in children[node])))
            if node in children:
                for cnode in children[node]:
                    _debug_write_tree(cnode, indent + '  ', kind)
            if kind == 'r' and node in sisters:
                for snode in sisters[node]:
                    _debug_write_tree(snode, indent + '*', kind)
        _fillids(node)
        _debug_write_tree(node, '', kind)
        if legenda:
            result.append("\nstart monad = {}\n\n".format(bmonad))
            result.append("{:>3} = {:>8} {:>8}\n".format('#', 'bhs_oid', 'laf_nid'))
            for (n, s) in sorted(ids.items(), key=lambda x: x[1]):
                result.append("{:>3} = {:>8} {:>8}\n".format(s, F.oid.v(n), n))
        return ''.join(result)

    def write_tree(self, node, kind, get_tag, rev=False):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.otype.v(node)
        children = self.rchildren if kind == 'r' else self.echildren 
        sisters = self.sisters

        words = []
        sequential = []
        def _write_tree(node, kind):
            (tag, pos, monad, text, is_word) = get_tag(node)
            if is_word:
                sequential.append(("W", len(words)))
                words.append((monad, text, pos))
            else: sequential.append(("O", tag))
            has_sisters = node in sisters and len(sisters[node])
            if kind == 'r' and has_sisters:
                sequential.append(("O", 'Ccoor'))
                for c in children[node]: _write_tree(c, kind)
                sequential.append(("C", 'Ccoor'))
                for s in sisters[node]: _write_tree(s, kind)
            else:
                for c in children[node]: _write_tree(c, kind)
            if not is_word: sequential.append(("C", tag))

        def do_sequential():
            word_perm = {}
            new_words = sorted(enumerate(words), key=lambda x: x[1][0])
            word_reps = []
            for (nn, (on, (monad, text, pos))) in enumerate(new_words):
                word_perm[on] = nn
                word_reps.append(text)
            word_rep = ' '.join(word_reps)
                            
            result = []
            for (code, info) in sequential:
                if code == 'O' or code == 'C':
                    if code == 'O': result.append('({}'.format(info))
                    else: result.append(')')
                elif code == 'W':
                    nn = word_perm[info]
                    pos = words[info][2]
                    result.append('({} {})'.format(pos, nn))
            result.append("\t{}".format(word_rep[::-1] if rev else word_rep))
            return ''.join(result)

        _write_tree(node, kind)
        return do_sequential()

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

    def get_sentence(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.otype.v(node)
        parent = self.rparent if kind == 'r' else self.eparent 
        children = self.rchildren if kind == 'r' else self.echildren 
        if otype == 'sentence': return node
        if node in parent: return self.get_sentence(parent[node], kind)
        if kind == 'r':
            if node in elder_sister: return self.get_sentence(elder_sister[node], kind)
        return (node, otype)
    
