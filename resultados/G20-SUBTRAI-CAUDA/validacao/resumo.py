import json, glob, numpy as np, pickle, os
D = os.path.dirname(os.path.abspath(__file__))
res = [json.load(open(f)) for f in sorted(glob.glob(D + '/out-*.json'))]
for r in res:
    s, pay, meta, *_ = pickle.load(open(D + '/cache-' + r['stem'] + '.pkl', 'rb'))
    assert len(s) == meta['samples'], r['stem']
def grp(st):
    return 'g03' if 'g03' in st else ('f06' if 'f06' in st else ('f00' if 'f00' in st else 'f04'))
P = lambda v: f"{100*v[0]:.1f} / {100*v[1]:.2f} / {'ok' if v[3] else 'FALHA'}"
print('checks', {r['stem'][9:]: r['rows']['_check'] for r in res})
print('\n## Plain\n| gravacao | pico | (a) atual | (c) k=1 cega | k=1..3 ×1 | **(d) k=1..3 ×4** | (e) oraculo (fator) | Δbits d-a | a_k final |\n|---|---|---|---|---|---|---|---|---|')
for r in sorted(res, key=lambda r: (grp(r['stem']), r['stem'])):
    if r['ifk']: continue
    R = r['rows']
    print(f"| {r['stem'][9:]} | {r['peak']:.2f} | {P(R['a'])} | {P(R['c'])} | {P(R['d1'])} | **{P(R['d'])}** | {P(R['e'])} (×{r['oracle_f']}) | {100*(R['d'][1]-R['a'][1]):+.2f} | {r['a_final']} |")
print('\n## IFK\n| gravacao | (b) IFK atual | IFK + k=1..3 ×1 | IFK + k=1..3 ×4 | 17 tons s/ exclusao | 17 tons + (c) k=1 | 17 tons + k=1..3 ×1 | 17 tons + (d) ×4 | oraculo (17 t) |\n|---|---|---|---|---|---|---|---|---|')
for r in res:
    if not r['ifk']: continue
    R = r['rows']
    print(f"| {r['stem'][9:]} | {P(R['b'])} | {P(R['b+d1'])} | {P(R['b+d'])} | {P(R['a'])} | {P(R['c'])} | {P(R['d1'])} | {P(R['d'])} | {P(R['e'])} (×{r['oracle_f']}) |")
def summ(rs, base, names):
    print(f'n={len(rs)} | variante | simb % | bits % | blocos | Δbits vs {base} media | melhor/igual/pior | pior Δ | ok->FALHA')
    for n in names:
        S = np.mean([r['rows'][n][0] for r in rs]); B = np.mean([r['rows'][n][1] for r in rs])
        K = sum(r['rows'][n][3] for r in rs)
        d = np.array([r['rows'][n][1] - r['rows'][base][1] for r in rs]) * 100
        lost = [r['stem'][9:] for r in rs if r['rows'][base][3] and not r['rows'][n][3]]
        print(f'| {n} | {100*S:.2f} | {100*B:.2f} | {int(K)}/{len(rs)} | {d.mean():+.2f} | {(d>0.05).sum()}/{(abs(d)<=0.05).sum()}/{(d<-0.05).sum()} | {d.min():+.2f} | {lost} |')
for g in ('f00', 'f04', 'g03'):
    print('\n###', g); summ([r for r in res if grp(r['stem']) == g], 'a', ['a', 'c', 'd1', 'd', 'e'])
print('\n### f00+f04'); summ([r for r in res if grp(r['stem']) in ('f00', 'f04')], 'a', ['a', 'c', 'd1', 'd', 'e'])
print('\n### f06'); summ([r for r in res if r['ifk']], 'b', ['b', 'b+d1', 'b+d', 'a', 'c', 'd1', 'd', 'e'])
