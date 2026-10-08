"""Subtracao da cauda dos simbolos anteriores vs IFK, relogio congelado no melhor offset.

Reimplementa o MaryDemodulator (piso corrente, floor_top=1, alpha=0.02, LLR max-log)
sobre a matriz de energias por simbolo e acrescenta a subtracao. Variante (a) e
conferida contra o MaryDemodulator real (decisoes identicas).
"""
import sys, json, numpy as np
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')))
import recording, spectro, fec
from modem import MARY_TONES, MARY_REPEAT_TONE, MaryDemodulator, _UNGRAY, _GRAY

FS, SPS = 48000, 480
G = int(0.15 * SPS); NN = np.arange(G, SPS)
T17 = np.array(list(MARY_TONES) + [MARY_REPEAT_TONE])
PROBE = np.exp(-2j * np.pi * np.outer(T17, NN) / FS)
PRE = 120  # simbolos de preambulo


def energies(s, start, per, m):
    E = []
    for k in range(m):
        a = int(round(start + k * per)); seg = s[a + G:a + SPS]
        if len(seg) < len(NN): break
        E.append(np.abs(PROBE @ seg) ** 2)
    return np.array(E)


def frame_values(payload):
    bits = list(fec.preamble_bits('mary', symbol_bits=4)) + list(fec.frame(payload, repeat=1))
    return np.array([sum(int(b) << j for j, b in enumerate(bits[i:i + 4]))
                     for i in range(0, len(bits) - 3, 4)]), np.array(bits)


def align(st):
    s, pay, meta = recording.load(st + '.json'); s = np.asarray(s, float)
    ifk = bool(meta.get('ifk'))
    want = np.array(spectro.tx_tone_indices(pay, 1, ifk=ifk))
    coarse, _ = spectro.find_start(s, FS, SPS, MARY_TONES, [int(x) for x in want])
    start, hits, n = spectro.align_mary(s, meta, [int(x) for x in want], coarse, SPS)
    best = None
    for per in np.arange(479.5, 480.51, 0.05):
        for d0 in range(-24, 25, 4):
            E = energies(s, start + d0, per, len(want)); m = len(E)
            a = np.mean(E[PRE:, :16 + ifk].argmax(1) == want[PRE:m])
            if best is None or a > best[0]: best = (a, per, d0, E)
    # refinamento fino do offset
    _, per, d0, _ = best
    for dd in range(d0 - 3, d0 + 4):
        E = energies(s, start + dd, per, len(want)); m = len(E)
        a = np.mean(E[PRE:, :16 + ifk].argmax(1) == want[PRE:m])
        if a > best[0]: best = (a, per, dd, E)
    _, per, d0, E = best
    return s, pay, meta, ifk, want, int(start + d0), per, E


def llr_of(log_e, ifk, excl, prev_val):
    """max-log, igual a demodulate_soft. log_e tem 16 ou 17 entradas (por tom)."""
    if ifk:
        log_e = log_e.copy()
        if excl is not None: log_e[excl] = -np.inf
        metric = np.array([log_e[_GRAY[v]] for v in range(16)])
        metric[prev_val] = max(metric[prev_val], log_e[16])
        place = lambda v: v
    else:
        metric = log_e; place = lambda v: _GRAY[v]
    out = []
    for j in range(4):
        ones = [metric[place(v)] for v in range(16) if (v >> j) & 1]
        zeros = [metric[place(v)] for v in range(16) if not (v >> j) & 1]
        o, z = max(ones), max(zeros)
        if np.isinf(o) and np.isinf(z): out.append(0.0)
        else: out.append(np.clip(o - z, -50, 50))
    return out


def receive(E, ifk, exclude=False, K=0, a_mode='blind', a_fixed=None, true_tones=None,
            beta=0.02, upd='corr', clamp=0.1, a_max=0.5, gscale=1.0):
    """Receptor simulado.
    ifk      : o transmissor usou IFK (17 tons, tom 16 = repeticao)
    exclude  : exclui o tom detectado no simbolo anterior (IFK atual)
    K        : quantos simbolos anteriores subtrair
    a_mode   : 'blind' (estimado online), 'fixed' (a_fixed)
    true_tones: se dado, subtrai nos tons VERDADEIROS (oraculo)
    """
    m, _ = E.shape; nt = 16 + ifk
    floor = np.zeros(nt)
    num = np.zeros(K + 1); den = np.zeros(K + 1)
    a = np.zeros(K + 1) if a_fixed is None else np.r_[0.0, a_fixed][:K + 1]
    dec = np.zeros(m, int); vals = np.zeros(m, int); llr = []
    prev_idx, prev_val = None, 0
    a_hist = []
    for n in range(m):
        raw = E[n, :nt].copy(); e = raw.copy()
        src = true_tones if true_tones is not None else dec
        for k in range(1, K + 1):
            if n - k < 0: continue
            t = src[n - k]
            e[t] -= gscale * a[k] * E[n - k, t]
        fl = np.maximum(floor, 1e-30)
        if K and clamp is not None and floor.any():
            e = np.maximum(e, clamp * floor)
        e = np.maximum(e, 1e-30)
        norm = e / fl
        sc = norm.copy()
        if exclude and prev_idx is not None: sc[prev_idx] = -np.inf
        idx = int(np.argmax(sc))
        llr += llr_of(np.log(np.maximum(norm, 1e-30)), ifk, prev_idx if exclude else None, prev_val)
        # floor (como o demod: exclui o maior, alpha)
        fe = e if upd == 'corr' else raw
        if not floor.any():
            floor[:] = fe.mean()
        else:
            mask = np.ones(nt, bool); mask[int(np.argmax(fe))] = False
            floor[mask] += 0.02 * (fe[mask] - floor[mask])
        v = prev_val if (ifk and idx == 16) else _UNGRAY[idx]
        dec[n] = idx; vals[n] = v; prev_idx, prev_val = idx, v
        # estimativa cega de a_k: energia no tom decidido em n-k, quando nao venceu em n
        if a_mode == 'blind' and K:
            for k in range(1, K + 1):
                if n - k < 0: continue
                t = dec[n - k]
                if t == idx or any(dec[n - j] == t for j in range(1, k)): continue
                x = raw[t] - floor[t]          # com sinal: ruido puro tem media ~0
                num[k] += beta * (x - num[k]); den[k] += beta * (E[n - k, t] - den[k])
                if den[k] > 0: a[k] = min(max(num[k] / den[k], 0.0), a_max)
            a_hist.append(a[1:].copy())
    return dec, vals, np.array(llr), (np.array(a_hist) if a_hist else None)


def oracle_a(E, want, K, ifk):
    """a_k por minimos quadrados com tons verdadeiros e piso genie."""
    nt = 16 + ifk; m = len(E); w = want[:m]
    noi = np.array([np.median(E[PRE:][w[PRE:] != t, t]) for t in range(nt)])
    a = []
    for k in range(1, K + 1):
        xs, ys = [], []
        for n in range(PRE, m):
            t = w[n - k]
            if t == w[n] or any(w[n - j] == t for j in range(1, k)): continue
            xs.append(E[n - k, t]); ys.append(E[n, t] - noi[t])
        xs, ys = np.array(xs), np.array(ys)
        a.append(max(float(xs @ ys / (xs @ xs)), 0.0))
    return np.array(a)


def score(dec, vals, llr, want, tvals, fbits, pay):
    m = len(dec); B = np.arange(PRE, m)
    sym = np.mean(dec[B] == want[B])
    bits = 1 - np.mean([bin(int(x) ^ int(y)).count('1') for x, y in zip(vals[B], tvals[B])]) / 4
    # bits pelo sinal do LLR, frame inteiro (sync+bloco), posicao conhecida
    L = llr[PRE * 4:PRE * 4 + len(fbits) - PRE * 4]
    fb = fbits[PRE * 4:PRE * 4 + len(L)]
    sbits = np.mean((L > 0) == (fb == 1))
    st = fec.find_sync(llr)
    ok = bool(st is not None and fec.decode(llr[st:], len(pay), repeat=1) == pay)
    return sym, bits, sbits, ok


def run(st):
    import os, pickle
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache-' + st.split('/')[-1] + '.pkl')
    if os.path.exists(cache):
        s, pay, meta, ifk, want, skip, per, E = pickle.load(open(cache, 'rb'))
    else:
        s, pay, meta, ifk, want, skip, per, E = align(st)
        pickle.dump((s, pay, meta, ifk, want, skip, per, E), open(cache, 'wb'))
    tvals, fbits = frame_values(pay)
    m = len(E); want = want[:m]; tvals = tvals[:m]
    rows = {}
    # (a) receptor atual -- conferido contra o MaryDemodulator real
    if not ifk:
        d = MaryDemodulator(steer=False, skip=skip, period=per)
        real = np.array([i for i, _c, _n in d._symbols(s)][:m])
        rows['_check_a'] = float(np.mean(real[:m] == receive(E, False)[0][:len(real)]))
        rows['a atual'] = score(*receive(E, False)[:3], want, tvals, fbits, pay)
    else:
        d = MaryDemodulator(steer=False, skip=skip, period=per, ifk=True)
        real = np.array([i for i, _c, _n in d._symbols(s)][:m])
        rows['_check_b'] = float(np.mean(real == receive(E, True, exclude=True)[0][:len(real)]))
        rows['b IFK atual'] = score(*receive(E, True, exclude=True)[:3], want, tvals, fbits, pay)
        rows['a IFK sem exclusao'] = score(*receive(E, True)[:3], want, tvals, fbits, pay)
    ahist = {}
    for K in (1, 2, 3):
        dec, vals, llr, ah = receive(E, ifk, K=K)
        rows[f'c/d cega k=1..{K}'] = score(dec, vals, llr, want, tvals, fbits, pay)
        ahist[K] = ah[-1].round(4).tolist()
        rows[f'cega k=1..{K} piso cru'] = score(*receive(E, ifk, K=K, upd='raw')[:3], want, tvals, fbits, pay)
        if ifk:
            rows[f'IFK + cega k=1..{K}'] = score(*receive(E, True, exclude=True, K=K)[:3], want, tvals, fbits, pay)
    for K in (1, 3):
        ao = oracle_a(E, want, K, ifk)
        best = None
        for f in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
            r = score(*receive(E, ifk, K=K, a_mode='fixed', a_fixed=ao * f, true_tones=want)[:3], want, tvals, fbits, pay)
            if best is None or r[0] > best[0][0]: best = (r, f)
        rows[f'e oraculo k=1..{K}'] = best[0]
        ahist[f'oraculo{K}'] = (ao * best[1]).round(4).tolist()
    return dict(stem=st.split('/')[-1], ifk=ifk, period=per, skip=skip, rows=rows, a=ahist)


if __name__ == '__main__':
    out = []
    for st in sys.argv[1:]:
        r = run('captures/' + st if '/' not in st else st)
        out.append(r)
        print(json.dumps(r, default=lambda x: x if not isinstance(x, (np.floating, np.bool_)) else x.item()), flush=True)
