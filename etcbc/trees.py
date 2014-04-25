import collections
from .lib import monad_set, object_rank

class Tree(object):
    def __init__(self, API, otypes=None):
        API['fabric'].load_again({"features": {"shebanq": {"node": ["db.otype,monads",]}}}, add=True)
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        if otypes == None:
            otypes = sorted(object_rank, key=lambda x: object_rank[x])
        msg("Start computing parent and children relations for objects of type {}".format(', '.join(otypes)))
        otype_set = set(otypes)
        base_type = otypes[-1]
        cur_stack = []
        parent = {}
        children = collections.defaultdict(lambda: [])
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
                    parent[node] = snode
                    children[snode].append(node)
                    break;
            cur_stack = [cur_stack[i] for i in range(len(cur_stack)) if i not in tobe_removed]
            if otype != base_type: cur_stack.append((node, nm_set, nm_max))
        msg("{} nodes: {} have parents and {} have children".format(nn, len(parent), len(children)))
        self.parent = parent
        self.children = children

    def embedding(self): return (self.parent, self.children)
