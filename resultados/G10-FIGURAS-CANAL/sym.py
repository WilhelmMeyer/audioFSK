import sys, json, numpy as np
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import recording, spectro, fec
from modem import MARY_TONES, MaryDemodulator
T = np.array(MARY_TONES); NT = 16
def run(stem):
    samples, payload, meta = recording.load(stem + '.json')
    samples = np.asarray(samples, float)
    fs, sps = meta['fs'], 480
    want = np.array(spectro.tx_tone_indices(payload, meta.get('fec_repeat', 1) or 1))
    coarse, _ = spectro.find_start(samples, fs, sps, MARY_TONES, list(want))
    start, hits, n = spectro.align_mary(samples, meta, list(want), coarse, sps)
    g = int(0.15 * sps); nn = np.arange(g, sps)
    probe = np.exp(-2j*np.pi*np.outer(T, nn)/fs)
    # period search
    best = None
    for per in np.arange(479.7, 480.31, 0.05):
        for d0 in range(-24, 25, 4):
            E = []
            for k in range(len(want)):
                a = int(round(start + d0 + k*per))
                seg = samples[a+g:a+sps]
                if len(seg) < len(nn): break
                E.append(np.abs(probe@seg)**2)
            E = np.array(E); m = len(E)
            acc = np.mean(E.argmax(1) == want[:m])
            if best is None or acc > best[0]: best = (acc, per, d0, E)
    acc, per, d0, E = best
    m = len(E); w = want[:m]
    # floor-normalised (genie noise floor)
    noi = np.array([np.median(E[w != t, t]) for t in range(NT)])
    sig = np.array([np.median(E[w == t, t]) if np.any(w == t) else np.nan for t in range(NT)])
    dec_raw = E.argmax(1); dec_n = (E/noi).argmax(1)
    body = np.arange(m) >= 120
    out = dict(stem=stem.split('/')[-1], start=start, period=per, d0=d0, n=m)
    for name, dec in (('raw', dec_raw), ('norm', dec_n)):
        ok = dec == w
        out[name+'_acc_body'] = ok[body].mean(); out[name+'_acc_pre'] = ok[~body].mean()
    dec = dec_n
    err = np.where((dec != w) & body)[0]
    prev = np.r_[-1, w[:-1]]; nxt = np.r_[w[1:], -1]
    cat = dict(prev=0, next=0, d1=0, d2=0, other=0)
    for k in err:
        r = dec[k]
        if r == prev[k]: cat['prev'] += 1
        elif r == nxt[k]: cat['next'] += 1
        elif abs(r - w[k]) == 1: cat['d1'] += 1
        elif abs(r - w[k]) == 2: cat['d2'] += 1
        else: cat['other'] += 1
    out['nerr'] = len(err); out['cat'] = {k: round(v/len(err), 3) for k, v in cat.items()}
    # chance for prev given random: prev differs from w with prob ~15/16 -> 1/15
    # leak: energy at previous tone (prev != cur) over noise floor, vs non-tx tone over floor
    kk = [k for k in range(121, m) if prev[k] != w[k] and nxt[k] != w[k] and nxt[k] != prev[k]]
    lp = np.array([E[k, prev[k]]/noi[prev[k]] for k in kk])
    ln = np.array([E[k, nxt[k]]/noi[nxt[k]] for k in kk])
    ls = np.array([E[k, w[k]]/noi[w[k]] for k in kk])
    out['leak_prev_dB'] = 10*np.log10(np.median(lp)); out['leak_next_dB'] = 10*np.log10(np.median(ln))
    out['sig_over_floor_dB'] = 10*np.log10(np.median(ls))
    # P(error | prev tone) ; errors where receiver picked prev tone vs P(random)
    # per tone
    pt = []
    for t in range(NT):
        s = body & (w == t)
        pt.append((t, int(s.sum()), round(1 - np.mean(dec[s] == t), 3) if s.sum() else None,
                   round(10*np.log10(sig[t]), 1), round(10*np.log10(sig[t]/noi[t]), 1)))
    out['per_tone'] = pt
    # over time (body deciles)
    bi = np.where(body)[0]
    out['time'] = [round(float(np.mean(dec[c] == w[c])), 3) for c in np.array_split(bi, 8)]
    # within-window echo: split window into early/late halves, leak of prev tone
    h = (sps - g)//2
    pe = probe[:, :h]; pl = probe[:, h:]
    lr = []
    for k in kk:
        a = int(round(start + d0 + k*per))
        s1 = samples[a+g:a+g+h]; s2 = samples[a+g+h:a+g+2*h]
        e1 = np.abs(pe@s1)**2; e2 = np.abs(pl@s2)**2
        lr.append((e1[prev[k]]/e1[w[k]], e2[prev[k]]/e2[w[k]]))
    lr = np.array(lr)
    out['prev/cur early_dB'] = 10*np.log10(np.median(lr[:, 0])); out['prev/cur late_dB'] = 10*np.log10(np.median(lr[:, 1]))
    # tail: band envelope after last symbol
    end = int(round(start + d0 + len(want)*per))
    from scipy.signal import butter, sosfiltfilt
    sos = butter(6, [800, 3400], btype='band', fs=fs, output='sos')
    y = sosfiltfilt(sos, samples)
    win = 480
    env = np.array([np.mean(y[i:i+win]**2) for i in range(0, len(y)-win, win)])
    envdb = 10*np.log10(env + 1e-20)
    floor = np.median(envdb[-20:]) if len(envdb) > 20 else None
    i0 = end//win
    tail = envdb[i0-3:i0+60]
    out['env_before_end_dB'] = round(float(np.median(envdb[i0-60:i0-10])), 1)
    out['floor_end_dB'] = round(float(floor), 1)
    out['tail_10ms'] = [round(float(x), 1) for x in tail[:40]]
    return out, E, w, dec
if __name__ == '__main__':
    for st in sys.argv[1:]:
        o, *_ = run(st)
        print(json.dumps(o, default=float))
