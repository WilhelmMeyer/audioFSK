"""Validacao fora da amostra da variante congelada de G20 (sem reajuste).
Congelado: receive(E, ifk, K=3, upd='raw', gscale=4) com os defaults de subtrai.py
(beta=0.02, clamp=0.1, a_max=0.5). Oraculo como ganho.py (K=3, piso cru, grade 1..16 por bits)."""
import sys, os, json, pickle, numpy as np
sys.dont_write_bytecode = True
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(D, '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))  # raiz do repositorio
import subtrai as S
from modem import MaryDemodulator

def run(st):
    cache = os.path.join(D, 'cache-' + st + '.pkl')
    if os.path.exists(cache):
        s, pay, meta, ifk, want, skip, per, E = pickle.load(open(cache, 'rb'))
    else:
        s, pay, meta, ifk, want, skip, per, E = S.align('captures/' + st)
        pickle.dump((s, pay, meta, ifk, want, skip, per, E), open(cache, 'wb'))
    tv, fb = S.frame_values(pay); m = len(E); want = want[:m]; tv = tv[:m]
    sc = lambda r: [float(x) for x in S.score(*r[:3], want, tv, fb, pay)]
    R = {}
    if not ifk:
        d = MaryDemodulator(steer=False, skip=skip, period=per)
        real = np.array([i for i, _c, _n in d._symbols(s)][:m])
        R['_check'] = float(np.mean(real == S.receive(E, False)[0][:len(real)]))
        R['a'] = sc(S.receive(E, False))
    else:
        d = MaryDemodulator(steer=False, skip=skip, period=per, ifk=True)
        real = np.array([i for i, _c, _n in d._symbols(s)][:m])
        R['_check'] = float(np.mean(real == S.receive(E, True, exclude=True)[0][:len(real)]))
        R['b'] = sc(S.receive(E, True, exclude=True))
        R['a'] = sc(S.receive(E, True))                       # 17 tons sem exclusao
        R['b+d'] = sc(S.receive(E, True, exclude=True, K=3, upd='raw', gscale=4))
        R['b+d1'] = sc(S.receive(E, True, exclude=True, K=3, upd='raw'))
    R['c'] = sc(S.receive(E, ifk, K=1, upd='raw'))
    R['d1'] = sc(S.receive(E, ifk, K=3, upd='raw'))
    dec, vals, llr, ah = S.receive(E, ifk, K=3, upd='raw', gscale=4)
    R['d'] = sc((dec, vals, llr))
    ao = S.oracle_a(E, want, 3, ifk); best = None
    for f in (1, 2, 4, 6, 8, 12, 16):
        r = sc(S.receive(E, ifk, K=3, a_mode='fixed', a_fixed=ao * f, true_tones=want, upd='raw'))
        if best is None or r[1] > best[0][1]: best = (r, f)
    R['e'] = best[0]
    return dict(stem=st, ifk=ifk, per=float(per), skip=int(skip), rows=R,
                a_final=ah[-1].round(4).tolist(), oracle_f=best[1],
                peak=meta.get('peak'), rms=meta.get('rms'))

if __name__ == '__main__':
    for st in sys.argv[1:]:
        out = os.path.join(D, 'out-' + st + '.json')
        r = run(st); json.dump(r, open(out, 'w')); print(json.dumps(r), flush=True)
