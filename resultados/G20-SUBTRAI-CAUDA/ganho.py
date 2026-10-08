import sys, os, json, pickle, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import subtrai as S
st = sys.argv[1]
s, pay, meta, ifk, want, skip, per, E = pickle.load(open(os.path.join(D, f'cache-{st}.pkl'), 'rb'))
tv, fb = S.frame_values(pay); m = len(E); want = want[:m]; tv = tv[:m]
# ganho g sobre o a cego: a_usado = g*a (implementado escalando a_max e o resultado)
orig = S.receive
out = {}
for g in (1, 2, 4, 8):
    def rec(E, ifk, g=g, **kw):
        # copia de receive com escala: reutiliza a_fixed=None e pos-escala via a_max
        return orig(E, ifk, **kw)
    import types
    src = open(os.path.join(D, 'subtrai.py')).read()
    r = S.score(*S.receive(E, ifk, K=3, upd='raw', a_max=0.5, gscale=g)[:3], want, tv, fb, pay) if 'gscale' in S.receive.__code__.co_varnames else None
    out[f'cega x{g}'] = [round(100*r[1], 2), bool(r[3]), round(100*r[0], 1)]
ao = S.oracle_a(E, want, 3, ifk); best = None
for f in (1, 2, 3, 4, 6, 8, 12, 16):
    r = S.score(*S.receive(E, ifk, K=3, a_mode='fixed', a_fixed=ao*f, true_tones=want, upd='raw')[:3], want, tv, fb, pay)
    if best is None or r[1] > best[0][1]: best = (r, f)
out['oraculo cru k3'] = [round(100*best[0][1], 2), bool(best[0][3]), best[1]]
print(st, json.dumps(out), flush=True)
