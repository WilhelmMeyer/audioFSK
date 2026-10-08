"""H04: os erros de simbolo da 16-FSK se concentram em poucos tons?

Roda da raiz do repositorio, offline (nenhum dispositivo de audio, nenhuma
porta serial):

    ./venv/bin/python -u resultados/H05-ERROS-POR-TOM/erros_por_tom.py

Para cada gravacao do corpus (cadeia linear, mode mary, sem IFK):
  1. sequencia de tons transmitida = spectro.tx_tone_indices(payload, fecrep),
     indice de TOM no ar (_GRAY[valor]), nunca o valor;
  2. inicio grosso por spectro.find_start + spectro.align_mary;
  3. grade (periodo x deslocamento) pontuada por argmax bruto no corpo, a
     MESMA grade para todas as gravacoes (uma regua so) -- o relogio nominal
     de 480 deriva ~100 amostras num quadro de 2450 simbolos entre duas
     maquinas, mais que a guarda;
  4. decisoes finais de MaryDemodulator(steer=False, skip, period) com os
     parametros padrao (o piso corrente que o receptor usa de fato).
Conta so o corpo codificado (simbolos 120.. ate o fim do quadro), fora o
preambulo de dois tons e a cauda ociosa.

Escreve, nesta pasta: simbolos.json (sequencias por gravacao, cache),
por-gravacao.csv, por-tom.csv, confusao-*.csv, resultado.json e
fig-ser-por-tom.png. Com --so-estatistica relê simbolos.json sem demodular.
"""
import argparse
import os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_v, '1')     # um processo por gravacao; BLAS em 1 fio
import csv
import glob
import json
import sys
from multiprocessing import Pool

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
sys.path.insert(0, RAIZ)
import recording  # noqa: E402
import spectro  # noqa: E402
from modem import MARY_TONES, MaryDemodulator  # noqa: E402

NT = 16
SPS = 480
G = int(0.15 * SPS)
NN = np.arange(G, SPS)
BODY0 = 120                      # fim do preambulo de dois tons
PERIODS = np.round(np.arange(479.70, 480.301, 0.05), 3)
D0S = range(-24, 25, 4)

CORPUS = {
    'B->A': ['resultados/08-MARY-GAIN/gravacao/*.json',
             'resultados/14-FEC-REP/gravacao/*.json',
             'resultados/12-13-SYNC/gravacao/*.json'],
    'A->B': ['resultados/17-SPK-LEVEL-A2B/gravacao/*-spk20-*.json'],
}


def corpus():
    out = []
    for direc, pats in CORPUS.items():
        for pat in pats:
            for p in sorted(glob.glob(os.path.join(RAIZ, pat))):
                m = json.load(open(p))
                if m.get('kind') != 'fec' or m.get('mode') != 'mary' or m.get('ifk'):
                    continue
                out.append((direc, os.path.relpath(p, RAIZ)))
    return out


def energias(s, start, per, m, probe):
    """Energia dos 16 tons em cada janela k (guarda pulada), vetorizado."""
    a = np.round(start + np.arange(m) * per).astype(int)
    ok = (a >= 0) & (a + SPS <= len(s))
    m = int(np.argmin(ok)) if not ok.all() else m
    a = a[:m]
    segs = s[a[:, None] + NN[None, :]]
    return np.abs(segs @ probe.T) ** 2


def analisa(item):
    direc, rel = item
    s, pay, meta = recording.load(os.path.join(RAIZ, rel))
    s = np.asarray(s, dtype=np.float64)
    rep = meta.get('fec_repeat', 1) or 1
    want = np.array(spectro.tx_tone_indices(pay, rep), dtype=int)
    coarse, _ = spectro.find_start(s, meta['fs'], SPS, MARY_TONES, list(want))
    start, _hits, _n = spectro.align_mary(s, meta, list(want), coarse, SPS)
    probe = np.exp(-2j * np.pi * np.outer(np.array(MARY_TONES, float), NN) / meta['fs'])
    best = None
    for per in PERIODS:
        for d0 in D0S:
            E = energias(s, start + d0, per, len(want), probe)
            m = len(E)
            if m <= BODY0 + 40:
                continue
            a = float(np.mean(E[BODY0:].argmax(1) == want[BODY0:m]))
            if best is None or a > best[0]:
                best = (a, float(per), int(d0))
    _a, per, d0 = best
    print(f"  {rel} pronto", flush=True)
    d = MaryDemodulator(steer=False, skip=int(start + d0), period=per,
                        fs=meta['fs'], baud=meta['baud'])
    dec = []
    for i in range(0, len(s), 2048):
        dec += [o[0] for o in d._symbols(s[i:i + 2048])]
    dec = np.array(dec[:len(want)], dtype=int)
    m = len(dec)
    w = want[:m]
    body = np.arange(BODY0, m)
    ok = dec[body] == w[body]
    half = len(body) // 2
    return dict(
        direcao=direc, gravacao=rel, campanha=rel.split('/')[1],
        rotulo=meta.get('label', ''), ganho=meta.get('gain'), fecrep=rep,
        sync_chirp=bool(meta.get('sync_chirp')),
        pico=float(np.max(np.abs(s))), inicio=int(start + d0), periodo=per,
        simbolos=int(len(body)), erros=int((~ok).sum()),
        acerto_1a_metade=float(ok[:half].mean()),
        acerto_2a_metade=float(ok[half:].mean()),
        enviado=[int(x) for x in w[body]],
        detectado=[int(x) for x in dec[body]],
        anterior=[int(x) for x in w[body - 1]],
    )


# ---------------------------------------------------------------- estatistica

def por_tom(recs):
    sent = np.concatenate([r['enviado'] for r in recs])
    det = np.concatenate([r['detectado'] for r in recs])
    prev = np.concatenate([r['anterior'] for r in recs])
    err = det != sent
    isi = err & (det == prev)
    n = np.bincount(sent, minlength=NT)
    e = np.bincount(sent[err], minlength=NT)
    ei = np.bincount(sent[isi], minlength=NT)
    fw = np.bincount(det[err], minlength=NT)          # vitorias falsas
    notsent = len(sent) - n
    conf = np.zeros((NT, NT), int)
    np.add.at(conf, (sent, det), 1)
    return dict(n=n, e=e, e_isi=ei, fw=fw, notsent=notsent, conf=conf,
                total=len(sent), erros=int(err.sum()), isi=int(isi.sum()))


def share_worst(e, k):
    return float(np.sort(e)[::-1][:k].sum() / max(e.sum(), 1))


def share_worst_rate(n, e, k):
    """Fracao dos erros nos k tons de maior SER (nao de mais erros)."""
    ser = e / np.maximum(n, 1)
    worst = np.argsort(ser)[::-1][:k]
    return float(e[worst].sum() / max(e.sum(), 1)), worst


def permuta(recs, rng):
    """Mesmas gravacoes com os rotulos de tom embaralhados dentro de cada
    gravacao: cada simbolo mantem seu acerto/erro, perde o tom. Hipotese nula
    de que o tom nao importa."""
    out = []
    for r in recs:
        sent = np.array(r['enviado'])
        err = np.array(r['detectado']) != sent
        perm = rng.permutation(len(sent))
        s2 = sent[perm]
        out.append(dict(enviado=s2, detectado=np.where(err, (s2 + 1) % NT, s2),
                        anterior=np.full(len(s2), -2)))
    return out


def ser_tom_por_grav(r):
    sent = np.asarray(r['enviado'])
    err = np.asarray(r['detectado']) != sent
    n = np.bincount(sent, minlength=NT)
    e = np.bincount(sent[err], minlength=NT)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(n > 0, e / np.maximum(n, 1), np.nan), n, e


def spearman(a, b):
    from scipy.stats import spearmanr
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 5 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return np.nan
    return float(spearmanr(a[ok], b[ok]).correlation)


def estabilidade(recs):
    """Media, sobre pares de gravacoes, da correlacao de Spearman entre SER
    por tom e da sobreposicao dos 3 piores tons."""
    sers = [ser_tom_por_grav(r)[0] for r in recs]
    rho, ov = [], []
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            rho.append(spearman(sers[i], sers[j]))
            wi = set(np.argsort(np.nan_to_num(sers[i], nan=-1))[::-1][:3])
            wj = set(np.argsort(np.nan_to_num(sers[j], nan=-1))[::-1][:3])
            ov.append(len(wi & wj))
    return float(np.nanmean(rho)), float(np.mean(ov))


def validacao_cruzada(recs, rng, nsplit=400, k=3):
    """Escolhe os k piores tons numa metade das gravacoes, mede na outra.

    Contrafactual: os simbolos que cairiam nos k tons evitados passam a ter a
    SER media dos outros 13 tons da metade de teste. Devolve (SER de teste
    como esta, SER de teste com o mapa) medias sobre as particoes, mais a
    fracao de particoes em que o mapa ajudou."""
    base, mapa, ganhou = [], [], 0
    idx = np.arange(len(recs))
    for _ in range(nsplit):
        rng.shuffle(idx)
        h = len(idx) // 2
        tr = por_tom([recs[i] for i in idx[:h]])
        te = por_tom([recs[i] for i in idx[h:]])
        ser_tr = tr['e'] / np.maximum(tr['n'], 1)
        worst = np.argsort(ser_tr)[::-1][:k]
        keep = np.setdiff1d(np.arange(NT), worst)
        b = te['e'].sum() / te['n'].sum()
        mp = te['e'][keep].sum() / te['n'][keep].sum()
        base.append(b)
        mapa.append(mp)
        ganhou += mp < b
    return float(np.mean(base)), float(np.mean(mapa)), ganhou / nsplit


def estatistica(recs, rng, nperm=2000):
    pt = por_tom(recs)
    n, e = pt['n'], pt['e']
    ser = e / np.maximum(n, 1)
    ser_all = pt['erros'] / pt['total']
    out = dict(gravacoes=len(recs), simbolos=pt['total'], erros=pt['erros'],
               ser=ser_all, erros_isi=pt['isi'])
    for k in (3, 5):
        sh, worst = share_worst_rate(n, e, k)
        null = []
        for _ in range(nperm if k == 3 else nperm // 4):
            pp = por_tom(permuta(recs, rng))
            null.append(share_worst_rate(pp['n'], pp['e'], k)[0])
        keep = np.setdiff1d(np.arange(NT), worst)
        out[f'pior{k}'] = dict(
            tons_hz=[MARY_TONES[t] for t in worst], indices=[int(t) for t in worst],
            fracao_erros=sh, uniforme=k / NT,
            nula_media=float(np.mean(null)),
            nula_p95=float(np.percentile(null, 95)),
            p_valor=float(np.mean(np.array(null) >= sh)),
            ser_sem_eles_in_sample=float(e[keep].sum() / n[keep].sum()))
    rho, ov = estabilidade(recs)
    nr, no = [], []
    for _ in range(200):
        a, b = estabilidade(permuta(recs, rng))
        nr.append(a)
        no.append(b)
    out['estabilidade'] = dict(spearman_medio=rho, spearman_nulo=float(np.mean(nr)),
                               spearman_nulo_p95=float(np.percentile(nr, 95)),
                               sobreposicao_pior3=ov,
                               sobreposicao_nula=float(np.mean(no)),
                               sobreposicao_nula_p95=float(np.percentile(no, 95)),
                               sobreposicao_acaso=9 / 16)
    # metades por campanha: o mesmo tom ruim aparece em campanhas diferentes?
    camp = {}
    for r in recs:
        camp.setdefault(r['campanha'], []).append(r)
    out['por_campanha'] = {}
    for c, rs in camp.items():
        p = por_tom(rs)
        s = p['e'] / np.maximum(p['n'], 1)
        out['por_campanha'][c] = dict(gravacoes=len(rs), simbolos=p['total'],
                                      ser=p['erros'] / p['total'],
                                      pior3_hz=[MARY_TONES[t] for t in np.argsort(s)[::-1][:3]],
                                      ser_por_tom=[float(x) for x in s])
    for k in (3, 5):
        b, m, g = validacao_cruzada(recs, rng, k=k)
        out[f'cv_pior{k}'] = dict(ser_teste=b, ser_teste_com_mapa=m,
                                  reducao_relativa=1 - m / b, fracao_particoes_melhor=g)
    # Fora-uma-campanha: o mapa vem das OUTRAS sessoes, o teste e a sessao
    # deixada de fora. E o que um mapa fixo (de fabrica) faria; a validacao
    # cruzada acima mistura sessoes nas duas metades e mede o que um mapa
    # medido na propria sessao faria.
    if len(camp) > 1:
        out['fora_uma_campanha'] = {}
        for c in camp:
            tr = por_tom([r for r in recs if r['campanha'] != c])
            te = por_tom(camp[c])
            s_tr = tr['e'] / np.maximum(tr['n'], 1)
            d = {}
            for k in (3, 5):
                worst = np.argsort(s_tr)[::-1][:k]
                keep = np.setdiff1d(np.arange(NT), worst)
                d[f'pior{k}_hz'] = [MARY_TONES[t] for t in worst]
                d[f'ser_com_mapa_pior{k}'] = float(te['e'][keep].sum() / te['n'][keep].sum())
            d['ser_teste'] = te['erros'] / te['total']
            s_te = te['e'] / np.maximum(te['n'], 1)
            d['spearman_treino_teste'] = spearman(s_tr, s_te)
            out['fora_uma_campanha'][c] = d
    # Mapa de contrato: medido na PRIMEIRA gravacao de cada sessao (ordem
    # cronologica), aplicado as seguintes da mesma sessao. Mais a estabilidade
    # dentro da sessao (Spearman medio entre pares de gravacoes da campanha).
    out['mapa_da_primeira'] = {}
    for c, rs in camp.items():
        rs = sorted(rs, key=lambda r: os.path.basename(r['gravacao']))
        d = dict(spearman_dentro=estabilidade(rs)[0] if len(rs) > 1 else None)
        if len(rs) > 1:
            tr = por_tom(rs[:1])
            te = por_tom(rs[1:])
            s_tr = tr['e'] / np.maximum(tr['n'], 1)
            d['ser_teste'] = te['erros'] / te['total']
            for k in (3, 5):
                worst = np.argsort(s_tr)[::-1][:k]
                keep = np.setdiff1d(np.arange(NT), worst)
                d[f'pior{k}_hz'] = [MARY_TONES[t] for t in worst]
                d[f'ser_com_mapa_pior{k}'] = float(te['e'][keep].sum() / te['n'][keep].sum())
        # O mesmo, treinando em CADA gravacao da sessao por vez (nao so na
        # primeira) e testando nas demais: media e faixa.
        if len(rs) > 1:
            for k in (3, 5):
                base, mapa = [], []
                for i in range(len(rs)):
                    tr = por_tom([rs[i]])
                    te = por_tom(rs[:i] + rs[i + 1:])
                    s_tr = tr['e'] / np.maximum(tr['n'], 1)
                    keep = np.setdiff1d(np.arange(NT), np.argsort(s_tr)[::-1][:k])
                    base.append(te['erros'] / te['total'])
                    mapa.append(te['e'][keep].sum() / te['n'][keep].sum())
                d[f'cada_uma_pior{k}'] = dict(ser_teste=float(np.mean(base)),
                                              ser_com_mapa=float(np.mean(mapa)),
                                              min=float(np.min(mapa)), max=float(np.max(mapa)))
        out['mapa_da_primeira'][c] = d
    out['por_tom'] = [dict(indice=t, hz=MARY_TONES[t], simbolos=int(n[t]), erros=int(e[t]),
                           ser=float(ser[t]), erros_isi=int(pt['e_isi'][t]),
                           ser_sem_isi=float((e[t] - pt['e_isi'][t]) / max(n[t], 1)),
                           vitorias_falsas=int(pt['fw'][t]),
                           taxa_vitoria_falsa=float(pt['fw'][t] / max(pt['notsent'][t], 1)))
                      for t in range(NT)]
    out['confusao'] = pt['conf'].tolist()
    return out


def figura(res, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dirs = list(res)
    fig, axs = plt.subplots(len(dirs), 1, figsize=(10, 3.4 * len(dirs)), sharex=True)
    x = np.arange(NT)
    for ax, d in zip(np.atleast_1d(axs), dirs):
        r = res[d]
        pt = r['por_tom']
        ser = np.array([p['ser'] for p in pt]) * 100
        isi = np.array([p['erros_isi'] / max(p['simbolos'], 1) for p in pt]) * 100
        nsym = np.array([p['simbolos'] for p in pt])
        worst = set(r['pior3']['indices'])
        cor = ['#c8553d' if t in worst else '#3b6ea8' for t in range(NT)]
        ax.bar(x, ser - isi, color=cor, width=0.75, label='outros erros', zorder=3)
        ax.bar(x, isi, bottom=ser - isi, color=cor, alpha=0.45, width=0.75, zorder=3,
               label='detectou o tom do simbolo anterior')
        m = r['ser'] * 100
        lo = 100 * (r['ser'] - 1.96 * np.sqrt(r['ser'] * (1 - r['ser']) / nsym.mean()))
        hi = 100 * (r['ser'] + 1.96 * np.sqrt(r['ser'] * (1 - r['ser']) / nsym.mean()))
        ax.axhspan(lo, hi, color='0.85', zorder=0, label='faixa de 95% se todos fossem iguais')
        ax.axhline(m, color='0.3', lw=1, ls='--', label=f'SER media {m:.1f}%')
        ax.set_ylabel('SER por tom enviado (%)')
        ax.set_title(f"{d}: {r['gravacoes']} gravacoes, {r['simbolos']} simbolos; "
                     f"3 piores (vermelho) = {100*r['pior3']['fracao_erros']:.0f}% dos erros "
                     f"(nula {100*r['pior3']['nula_media']:.0f}%)", fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(fontsize=8, frameon=False, loc='upper left')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{f}' for f in MARY_TONES], rotation=45)
    ax.set_xlabel('tom transmitido (Hz)')
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--so-estatistica', action='store_true')
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    cache = os.path.join(AQUI, 'simbolos.json')
    if args.so_estatistica:
        recs = json.load(open(cache))
    else:
        items = corpus()
        print(f"{len(items)} gravacoes")
        with Pool(args.jobs) as p:
            recs = p.map(analisa, items)
        json.dump(recs, open(cache, 'w'))
    with open(os.path.join(AQUI, 'por-gravacao.csv'), 'w', newline='') as f:
        cols = ['direcao', 'gravacao', 'rotulo', 'ganho', 'fecrep', 'sync_chirp', 'pico',
                'inicio', 'periodo', 'simbolos', 'erros', 'acerto_1a_metade',
                'acerto_2a_metade']
        wr = csv.writer(f)
        wr.writerow(cols + ['ser'])
        for r in recs:
            wr.writerow([r[c] for c in cols] + [r['erros'] / r['simbolos']])
            print(f"{r['direcao']} {os.path.basename(r['gravacao']):<42} per {r['periodo']:.2f} "
                  f"pico {r['pico']:.2f} SER {100*r['erros']/r['simbolos']:5.1f}% "
                  f"metades {100*r['acerto_1a_metade']:.0f}/{100*r['acerto_2a_metade']:.0f}")
    rng = np.random.default_rng(20261008)
    res = {}
    for d in CORPUS:
        rs = [r for r in recs if r['direcao'] == d]
        res[d] = estatistica(rs, rng)
    json.dump(res, open(os.path.join(AQUI, 'resultado.json'), 'w'), indent=1)
    with open(os.path.join(AQUI, 'por-tom.csv'), 'w', newline='') as f:
        wr = csv.writer(f)
        keys = list(res['B->A']['por_tom'][0])
        wr.writerow(['direcao'] + keys)
        for d in res:
            for p in res[d]['por_tom']:
                wr.writerow([d] + [p[k] for k in keys])
    for d in res:
        tag = d.replace('->', '2')
        with open(os.path.join(AQUI, f'confusao-{tag}.csv'), 'w', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['enviado\\detectado'] + list(MARY_TONES))
            for t, row in zip(MARY_TONES, res[d]['confusao']):
                wr.writerow([t] + row)
    figura(res, os.path.join(AQUI, 'fig-ser-por-tom.png'))
    for d, r in res.items():
        print(f"\n== {d}: {r['gravacoes']} gravacoes, {r['simbolos']} simbolos, "
              f"SER {100*r['ser']:.1f}%, {100*r['erros_isi']/max(r['erros'],1):.0f}% dos erros "
              f"no tom anterior")
        for k in (3, 5):
            w = r[f'pior{k}']
            cv = r[f'cv_pior{k}']
            print(f"  piores {k}: {w['tons_hz']} -> {100*w['fracao_erros']:.1f}% dos erros "
                  f"(uniforme {100*w['uniforme']:.1f}%, nula {100*w['nula_media']:.1f}%, "
                  f"p95 {100*w['nula_p95']:.1f}%, p={w['p_valor']:.3f}); SER sem eles "
                  f"in-sample {100*w['ser_sem_eles_in_sample']:.1f}%; validacao cruzada "
                  f"{100*cv['ser_teste']:.1f}% -> {100*cv['ser_teste_com_mapa']:.1f}% "
                  f"({100*cv['reducao_relativa']:.0f}% a menos, melhor em "
                  f"{100*cv['fracao_particoes_melhor']:.0f}% das particoes)")
        s = r['estabilidade']
        print(f"  estabilidade: Spearman medio entre gravacoes {s['spearman_medio']:.2f} "
              f"(nula {s['spearman_nulo']:.2f}, p95 {s['spearman_nulo_p95']:.2f}); "
              f"sobreposicao dos 3 piores {s['sobreposicao_pior3']:.2f} "
              f"(nula {s['sobreposicao_nula']:.2f}, p95 {s['sobreposicao_nula_p95']:.2f})")
        for c, v in r['por_campanha'].items():
            print(f"  {c:<22} {v['gravacoes']:2d} grav {v['simbolos']:6d} simb "
                  f"SER {100*v['ser']:.1f}% piores {v['pior3_hz']}")
        for c, v in r.get('fora_uma_campanha', {}).items():
            print(f"  fora {c:<18} mapa {v['pior3_hz']}: SER {100*v['ser_teste']:.1f}% -> "
                  f"{100*v['ser_com_mapa_pior3']:.1f}% (pior3), "
                  f"{100*v['ser_com_mapa_pior5']:.1f}% (pior5); Spearman treino/teste "
                  f"{v['spearman_treino_teste']:.2f}")
        for c, v in r['mapa_da_primeira'].items():
            if 'ser_teste' in v:
                print(f"  1a de {c:<17} mapa {v['pior3_hz']}: SER {100*v['ser_teste']:.1f}% -> "
                      f"{100*v['ser_com_mapa_pior3']:.1f}% (pior3), "
                      f"{100*v['ser_com_mapa_pior5']:.1f}% (pior5); Spearman dentro "
                      f"{v['spearman_dentro']:.2f}")
                for k in (3, 5):
                    q = v[f'cada_uma_pior{k}']
                    print(f"      treino em cada uma, pior{k}: {100*q['ser_teste']:.1f}% -> "
                          f"{100*q['ser_com_mapa']:.1f}% (faixa {100*q['min']:.1f}-{100*q['max']:.1f}%)")
        print("  tom    n    SER  sem-ISI  vit.falsa")
        for p in r['por_tom']:
            print(f"  {p['hz']:5d} {p['simbolos']:5d} {100*p['ser']:5.1f}% "
                  f"{100*p['ser_sem_isi']:5.1f}%  {100*p['taxa_vitoria_falsa']:5.2f}%")


if __name__ == '__main__':
    main()
