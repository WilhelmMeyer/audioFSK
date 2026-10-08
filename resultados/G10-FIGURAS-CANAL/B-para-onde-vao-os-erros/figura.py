"""F-B: para onde vao os simbolos errados da 16-FSK, sem e com IFK, a 2 distancias.
Classes (nesta ordem de precedencia, decidido vs transmitido): tom de n-1, tom
de n-2, vizinho +-1 do transmitido, tom de repeticao (so IFK, 17o tom), outro.
Relogio: busca de periodo/offset por argmax bruto, depois MaryDemodulator sem
gate (steer=False), como em ifk.py da sessao de diagnostico."""
import csv
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(AQUI, '..'))
sys.path.insert(0, RAIZ)
import recording, spectro  # noqa: E402
from modem import MARY_TONES, MARY_REPEAT_TONE, MaryDemodulator  # noqa: E402
from plota import Fig, CORES, draw_text, TEXTO  # noqa: E402

FS, SPS = 48000, 480
G = int(0.15 * SPS)
NN = np.arange(G, SPS)
T17 = np.array(list(MARY_TONES) + [MARY_REPEAT_TONE])
PROBE = np.exp(-2j * np.pi * np.outer(T17, NN) / FS)
CAP = os.path.join(RAIZ, 'captures')
PARES = [('antiga', '20261008-162232-f04-16fsk-b', '20261008-162241-f06-16fsk-ifk'),
         ('10 cm', '20261008-164832-f04-16fsk-10cm', '20261008-164852-f06-16fsk-ifk-10cm')]
CLASSES = ['n-1', 'n-2', 'vizinho', 'repeticao', 'outro']


def energias(s, start, per, m):
    E = []
    for k in range(m):
        a = int(round(start + k * per)); seg = s[a + G:a + SPS]
        if len(seg) < len(NN): break
        E.append(np.abs(PROBE @ seg) ** 2)
    return np.array(E)


def analisa(stem):
    s, pay, meta = recording.load(os.path.join(CAP, stem + '.json')); s = np.asarray(s, float)
    ifk = bool(meta.get('ifk'))
    want = np.array(spectro.tx_tone_indices(pay, 1, ifk=ifk))
    coarse, _ = spectro.find_start(s, FS, SPS, MARY_TONES, [int(x) for x in want])
    start, hits, n = spectro.align_mary(s, meta, [int(x) for x in want], coarse, SPS)
    best = None
    for per in np.arange(479.7, 480.31, 0.05):
        for d0 in range(-24, 25, 4):
            E = energias(s, start + d0, per, len(want)); m = len(E)
            a = np.mean(E[120:].argmax(1) == want[120:m])
            if best is None or a > best[0]: best = (a, per, d0)
    _, per, d0 = best
    d = MaryDemodulator(steer=False, skip=int(start + d0), period=per, ifk=ifk)
    dec = np.array([o[0] for o in d._symbols(s)][:len(want)])
    m = len(dec); w = want[:m]
    B = np.arange(120, m)
    prev = np.r_[-1, w[:-1]]; prev2 = np.r_[-1, -1, w[:-2]]
    err = B[dec[B] != w[B]]
    cont = dict.fromkeys(CLASSES, 0)
    for k in err:
        r = dec[k]
        if r == prev[k]: cont['n-1'] += 1
        elif r == prev2[k]: cont['n-2'] += 1
        elif r < 16 and w[k] < 16 and abs(r - w[k]) == 1: cont['vizinho'] += 1
        elif r == 16: cont['repeticao'] += 1
        else: cont['outro'] += 1
    return dict(stem=stem, ifk=ifk, periodo=per, simbolos=len(B), erros=len(err),
                taxa_simbolo=len(err) / len(B), cont=cont)


def main():
    res = []
    fig = Fig(1100, 580, (0, 4), (0, 70), '', 'fracao dos simbolos errados (%)',
              'F-B destino dos simbolos errados', xticks=[], yticks=range(0, 71, 10), base=96)
    csvrows = []
    x = 0.12
    for gi, (pos, sem, com) in enumerate(PARES):
        for ci, (rot, stem) in enumerate((('sem IFK', sem), ('com IFK', com))):
            r = analisa(stem)
            print(pos, rot, stem, 'per %.2f' % r['periodo'], 'erros %d/%d = %.1f%%' % (r['erros'], r['simbolos'], 100 * r['taxa_simbolo']),
                  {k: round(100 * v / max(r['erros'], 1), 1) for k, v in r['cont'].items()})
            for k in CLASSES:
                csvrows.append([pos, rot, stem, k, r['cont'][k], r['erros'], r['simbolos'],
                                '%.2f' % (100 * r['cont'][k] / max(r['erros'], 1)), '%.2f' % (100 * r['taxa_simbolo'])])
            # uma barra por classe, empilhadas lado a lado dentro do grupo
            x0 = gi * 2 + ci
            for j, k in enumerate(CLASSES):
                v = 100 * r['cont'][k] / max(r['erros'], 1)
                bx0 = x0 + 0.1 + j * 0.15 / 1.0
                px0, px1 = fig.px(bx0), fig.px(bx0 + 0.13)
                fig.img[fig.py(v):fig.y1, px0:px1] = CORES[j]
            draw_text(fig.img, fig.px(x0 + 0.1) - 4, fig.y1 + 8, rot, TEXTO, 1)
            draw_text(fig.img, fig.px(x0 + 0.1) - 4, fig.y1 + 20, '%d erros/%d' % (r['erros'], r['simbolos']), TEXTO, 1)
            draw_text(fig.img, fig.px(x0 + 0.1) - 4, fig.y1 + 32, '(%.0f%% dos simb.)' % (100 * r['taxa_simbolo']), TEXTO, 1)
        draw_text(fig.img, fig.px(gi * 2 + 0.5), fig.y1 + 56, 'posicao ' + pos, TEXTO, 2)
    for j, k in enumerate(CLASSES):
        fig.legenda({'n-1': 'tom de n-1', 'n-2': 'tom de n-2', 'vizinho': 'vizinho +-1 do transmitido',
                     'repeticao': 'tom de repeticao (IFK)', 'outro': 'outro'}[k], CORES[j], x=fig.x1 - 330)
    fig.salva(os.path.join(AQUI, 'fig-b-destino-dos-erros.png'))
    with open(os.path.join(AQUI, 'destino-dos-erros.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['posicao', 'condicao', 'gravacao', 'classe', 'n_erros_classe', 'n_erros', 'n_simbolos', 'pct_dos_erros', 'pct_simbolos_errados'])
        w.writerows(csvrows)


main()
