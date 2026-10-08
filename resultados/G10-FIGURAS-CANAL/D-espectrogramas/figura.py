"""F-D: 0.5 s do meio da rajada, com eco (posicao 1) e limpo (10 cm).
Janela Hann de 408 amostras (a do detector: um simbolo menos a guarda), passo
96 amostras (2 ms), banda 700-3600 Hz, cada painel normalizado ao proprio pico,
escala de 40 dB. Reaproveita spectro.spectrogram e spectro.colourise.
O CSV traz o nivel (dB re pico do painel) nos 16 tons por coluna de tempo."""
import csv, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, RAIZ)
import recording  # noqa: E402
from modem import MARY_TONES  # noqa: E402
from spectro import spectrogram, colourise, write_png, draw_text  # noqa: E402

CAP = os.path.join(RAIZ, 'captures')
PAIN = [('posicao 1: eco', '20261008-161343-f00-nivel'), ('posicao 3: 10 cm, limpo', '20261008-164718-f00-nivel-10cm')]
FS, LO, HI, WIN, HOP, SECS, RANGE = 48000, 700.0, 3600.0, 408, 96, 0.5, 40.0
ROWS = 290
XS = 3
cols = (int(SECS * FS) - WIN) // HOP + 1
paineis, csvrows = [], []
for rot, stem in PAIN:
    r = recording.read(os.path.join(CAP, stem + '.wav'))
    x = np.asarray(r[0] if isinstance(r, tuple) else r, float)
    nb = len(x) // 480
    en = (x[:nb * 480].reshape(nb, 480) ** 2).mean(1)
    on = np.where(en > en.max() * 10 ** (-20 / 10))[0]
    mid = int((on[0] + on[-1]) / 2 * 480)
    a = mid - int(SECS * FS) // 2
    seg = x[a:a + int(SECS * FS)]
    db = spectrogram(seg, FS, LO, HI, cols, ROWS, win=WIN)
    db -= db.max()
    paineis.append((rot, stem, db, a / FS))
    n = np.arange(WIN); tap = np.hanning(WIN)
    pr = np.exp(-2j * np.pi * np.outer(MARY_TONES, n) / FS) * tap
    lv = np.array([np.abs(pr @ seg[c * HOP:c * HOP + WIN]) ** 2 for c in range(cols)])
    lv = 10 * np.log10(np.maximum(lv, 1e-20)); lv -= lv.max()
    for c in range(cols):
        csvrows.append([stem, '%.4f' % ((a + c * HOP) / FS)] + ['%.1f' % v for v in lv[c]])
    print(rot, stem, 'janela comeca em %.2f s' % (a / FS))
ESQ, TOPO, GAP = 70, 34, 40
PH = ROWS
W = ESQ + cols * XS + 20
H = TOPO + len(paineis) * (PH + GAP) + 20
img = np.full((H, W, 3), 255, np.uint8)
for i, (rot, stem, db, t0) in enumerate(paineis):
    y0 = TOPO + i * (PH + GAP)
    v = np.clip((db + RANGE) / RANGE, 0, 1)
    img[y0:y0 + PH, ESQ:ESQ + cols * XS] = np.repeat(colourise(v[::-1]), XS, axis=1)  # freq alta em cima
    draw_text(img, ESQ, y0 - 16, rot + '  (' + stem[9:] + ')', (35, 35, 35), 1)
    for t in MARY_TONES:
        y = y0 + int((HI - t) / (HI - LO) * (PH - 1))
        img[y:y + 1, ESQ - 6:ESQ] = (60, 60, 60)
    for f in (1000, 2000, 3000):
        y = y0 + int((HI - f) / (HI - LO) * (PH - 1))
        draw_text(img, 14, y - 3, str(f), (35, 35, 35), 1)
    # barra de 10 ms (um simbolo = 480 amostras = 10 ms) e de 100 ms
    xb = ESQ + cols - 5 - 10 * 48 // HOP * 5
    img[y0 + PH + 8:y0 + PH + 10, ESQ:ESQ + 100 * 48 * XS // HOP] = (35, 35, 35)
    draw_text(img, ESQ + 100 * 48 * XS // HOP + 6, y0 + PH + 5, '100 ms (10 simbolos)', (35, 35, 35), 1)
draw_text(img, ESQ, 8, 'F-D espectrogramas (f em Hz, marcas = 16 tons, 40 dB abaixo do pico do painel)', (35, 35, 35), 1)
write_png(os.path.join(AQUI, 'fig-d-espectrogramas.png'), img)
with open(os.path.join(AQUI, 'nivel-nos-tons.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['gravacao', 't_s'] + [str(t) for t in MARY_TONES]); w.writerows(csvrows)
