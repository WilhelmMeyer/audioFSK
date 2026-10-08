import sys, json, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
from sym import run, T
import recording
for st in sys.argv[1:]:
    o, E, w, dec = run(st)
    m = len(E); body = np.arange(m) >= 120
    # decay of a tone after it stops: energy at lag L / energy when on
    res = {}
    for L in (1, 2, 3, 4, 6):
        r = []
        for k in range(120, m - L):
            t = w[k]
            if any(abs(w[k+j] - t) <= 1 for j in range(1, L+1)): continue
            if k > 0 and w[k-1] == t: continue
            r.append(E[k+L, t] / E[k, t])
        res[L] = round(10*np.log10(np.median(r)), 1)
    # floor ratio: tone energy when absent for >=6 symbols around, / on-level
    fl = []
    for k in range(126, m):
        t = w[k-6]
        if all(abs(w[k-j] - t) > 1 for j in range(0, 6)) and True:
            pass
    # error rate as function of whether prev tone is within the "strong" vs current
    pc = []
    for k in range(121, m):
        if w[k-1] != w[k]:
            pc.append((10*np.log10(E[k-1, w[k-1]]/E[k, w[k]]), dec[k] == w[k]))
    pc = np.array(pc)
    bins = [-40, -6, 0, 6, 40]
    pr = []
    for a, b in zip(bins[:-1], bins[1:]):
        s = (pc[:, 0] >= a) & (pc[:, 0] < b)
        pr.append((f'{a}..{b}', int(s.sum()), round(1 - pc[s, 1].mean(), 2) if s.sum() else None))
    # repeated-symbol pairs have no ISI: accuracy when w[k]==w[k-1]
    same = [dec[k] == w[k] for k in range(121, m) if w[k-1] == w[k]]
    diff = [dec[k] == w[k] for k in range(121, m) if w[k-1] != w[k]]
    print(o['stem'], 'period', round(o['period'], 2), 'acc raw', round(o['raw_acc_body'], 3),
          'decay dB by lag(sym)', res, 'acc same-prev', round(np.mean(same), 2), len(same),
          'acc diff-prev', round(np.mean(diff), 3), 'err vs prevOn/curOn dB', pr,
          'cat', o['cat'], 'time', o['time'], 'prev/cur early,late', round(o['prev/cur early_dB'], 1), round(o['prev/cur late_dB'], 1),
          'tail', o['tail_10ms'][:40:3], 'floorEnd', o['floor_end_dB'])
