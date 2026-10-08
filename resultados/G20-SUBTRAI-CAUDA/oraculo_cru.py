import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subtrai as S
for st in sys.argv[1:]:
    import pickle
    s, pay, meta, ifk, want, skip, per, E = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'cache-{st}.pkl'), 'rb'))
    tv, fb = S.frame_values(pay); m = len(E); want = want[:m]; tv = tv[:m]
    out = {}
    for K in (1, 3):
        ao = S.oracle_a(E, want, K, ifk); best = None
        for f in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
            r = S.score(*S.receive(E, ifk, K=K, a_mode='fixed', a_fixed=ao*f, true_tones=want, upd='raw')[:3], want, tv, fb, pay)
            if best is None or r[1] > best[0][1]: best = (r, f)
        out[f'oraculo cru k=1..{K}'] = [round(100*best[0][1], 2), bool(best[0][3]), best[1]]
    if ifk:
        r = S.score(*S.receive(E, True, exclude=True, K=3, upd='raw')[:3], want, tv, fb, pay)
        out['IFK+cega k=1..3 cru'] = [round(100*r[1], 2), bool(r[3])]
    print(st, json.dumps(out), flush=True)
