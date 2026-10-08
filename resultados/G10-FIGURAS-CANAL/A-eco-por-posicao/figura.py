"""F-A: eco por posicao da caixa. (i) resposta ao impulso estimada pelo filtro
casado com modem.chirp() sobre as varreduras de sincronismo; (ii) queda do
tom anterior por atraso (1..6 simbolos).  Offline, so le captures/."""
import csv
import os
import sys

import numpy as np
from scipy.signal import hilbert, fftconvolve
from scipy.fft import next_fast_len

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(AQUI, '..'))
sys.path.insert(0, RAIZ)
import modem, recording  # noqa: E402
from plota import Fig, CORES  # noqa: E402
from sym import run  # noqa: E402

CAP = os.path.join(RAIZ, 'captures')
POS = {'1 antiga, realce ligado': ['20261008-161939-f04-16fsk', '20261008-162232-f04-16fsk-b'],
       '2 realce off, reposicionada': ['20261008-162926-f04-16fsk-v4'],
       '3 a 10 cm apontada': ['20261008-164832-f04-16fsk-10cm']}
NIVEL = {'1 antiga, realce ligado': '20261008-161343-f00-nivel',
         '2 realce off, reposicionada': '20261008-162722-f00-nivel-v3',
         '3 a 10 cm apontada': '20261008-164718-f00-nivel-10cm'}
FS = 48000


def resposta(stem):
    s, _, meta = recording.load(os.path.join(CAP, stem + '.json'))
    s = np.asarray(s, float)
    tpl = modem.chirp(FS)
    c = fftconvolve(s, tpl[::-1], mode="valid")
    env = np.abs(hilbert(c, next_fast_len(len(c))))[:len(c)] ** 2
    med = np.median(env)
    gap = int(0.3 * FS)
    p1 = int(np.argmax(env))
    m = env.copy(); m[max(0, p1 - gap):p1 + gap] = 0
    p2 = int(np.argmax(m))
    picos = sorted([p1, p2])
    out = []
    for nome, p in zip(('lider', 'final'), picos):
        a, b = p - int(0.005 * FS), p + int(0.060 * FS)
        seg = env[a:b]
        k = int(0.001 * FS)  # media de 1 ms (potencia)
        sm = np.convolve(seg, np.ones(k) / k, mode='same')
        sm = sm / sm.max()
        t = (np.arange(a, b) - p) / FS * 1000
        out.append((nome, t, 10 * np.log10(np.maximum(sm, 1e-12)), env[p] / med))
    return out


def main():
    rows = []
    fig = Fig(1000, 580, (-5, 60), (-60, 0), 'ms apos o pico da varredura', 'dB re pico (media 1 ms)',
              'F-A(i) resposta ao impulso (varredura lider)', yticks=range(-60, 1, 10),
              xticks=range(-5, 61, 5))
    fig.leg_baixo = True
    for ci, (pos, stems) in enumerate(POS.items()):
        for stem in stems:
            for nome, t, db, snr in resposta(stem):
                for tt, dd in zip(t[::12], db[::12]):
                    rows.append([pos, stem, nome, '%.3f' % tt, '%.2f' % dd])
                if nome == 'lider':
                    fig.line(t, db, CORES[ci], 1)
                    print(stem, 'pico/mediana %.0f' % snr,
                          'dB em +10/+20/+40 ms: ' + ' '.join('%.1f' % db[np.argmin(abs(t - x))] for x in (10, 20, 40)))
        fig.legenda('posicao ' + pos, CORES[ci])
    fig.salva(os.path.join(AQUI, 'fig-a1-resposta-impulso.png'))
    with open(os.path.join(AQUI, 'resposta-impulso.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['posicao', 'gravacao', 'varredura', 't_ms', 'nivel_dB']); w.writerows(rows)

    # (ii) queda do tom anterior por atraso
    lags = (1, 2, 3, 4, 5, 6)
    fig2 = Fig(1000, 560, (0.5, 6.5), (-24, 0), 'atraso (simbolos)', 'energia do tom, dB re quando ligado',
               'F-A(ii) queda do tom anterior', xticks=lags, yticks=range(-24, 1, 4))
    rows2 = []
    for ci, (pos, stem) in enumerate(NIVEL.items()):
        o, E, w, dec = run(os.path.join(CAP, stem))
        m = len(E)
        ys = []
        for L in lags:
            r = []
            for k in range(120, m - L):
                t = w[k]
                if any(abs(w[k + j] - t) <= 1 for j in range(1, L + 1)): continue
                if w[k - 1] == t: continue
                r.append(E[k + L, t] / E[k, t])
            v = 10 * np.log10(np.median(r)); ys.append(v)
            rows2.append([pos, stem, L, '%.2f' % v, len(r)])
        fig2.line(lags, ys, CORES[ci], 1, pontos=True)
        fig2.legenda('posicao ' + pos, CORES[ci])
        print(stem, ' '.join('%.1f' % y for y in ys))
    fig2.salva(os.path.join(AQUI, 'fig-a2-queda-por-atraso.png'))
    with open(os.path.join(AQUI, 'queda-por-atraso.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['posicao', 'gravacao', 'atraso_simbolos', 'queda_mediana_dB', 'n']); w.writerows(rows2)


main()
