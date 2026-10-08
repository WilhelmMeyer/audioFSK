import json, glob, os, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
REG = {'eco': ['161343', '161721', '161734', '161939', '162232', '162241', '162218'],
       'moderado': ['162722', '162926', '162936'],
       'limpo': ['164718', '164832', '164852']}
res = {}
for f in sorted(glob.glob(D + '/out-*.json')):
    txt = open(f).read().strip().splitlines()
    if not txt: continue
    r = json.loads(txt[-1]); res[r['stem']] = r
def reg(stem):
    for k, v in REG.items():
        if any(x in stem for x in v): return k
print('| gravacao | regime | variante | simb % | bits % | bloco |\n|---|---|---|---|---|---|')
for st, r in res.items():
    for name, v in r['rows'].items():
        if name.startswith('_'): continue
        print(f"| {st[9:]} | {reg(st)} | {name} | {100*v[0]:.1f} | {100*v[1]:.1f} | {'ok' if v[3] else 'FALHA'} |")
print()
print('checks:', {st[9:]: {k: v for k, v in r['rows'].items() if k.startswith('_')} for st, r in res.items()})
print('a finais:', {st[9:]: r['a'] for st, r in res.items()})
print()
# resumo por regime, deltas pareados de bits contra a linha base
for rg in REG:
    print(f'### {rg}')
    plain = [r for st, r in res.items() if reg(st) == rg and not r['ifk']]
    ifk = [r for st, r in res.items() if reg(st) == rg and r['ifk']]
    for grp, base, lab in ((plain, 'a atual', 'sem IFK'), (ifk, 'b IFK atual', 'IFK')):
        if not grp: continue
        names = [n for n in grp[0]['rows'] if not n.startswith('_')]
        print(f'{lab} (n={len(grp)}) | variante | simb % | bits % | blocos | dbits vs {base} (pp): media, melhor/igual/pior, pior caso')
        for n in names:
            S = np.mean([r['rows'][n][0] for r in grp]); B = np.mean([r['rows'][n][1] for r in grp])
            K = sum(r['rows'][n][3] for r in grp)
            d = np.array([r['rows'][n][1] - r['rows'][base][1] for r in grp]) * 100
            print(f'  {n:24s} {100*S:5.1f} {100*B:5.1f} {K}/{len(grp)}  {d.mean():+5.2f}  {(d>0.05).sum()}/{(abs(d)<=0.05).sum()}/{(d<-0.05).sum()}  {d.min():+5.2f}')
