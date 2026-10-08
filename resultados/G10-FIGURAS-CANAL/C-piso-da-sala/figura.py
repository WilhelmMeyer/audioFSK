"""F-C: piso da sala. Welch (Hann, 8192 amostras = 5.9 Hz/bin, 50% de
sobreposicao) de duas gravacoes de silencio: ar-condicionado ligado e desligado.
As faixas dos 16 tons (+-40 Hz) vao marcadas e a potencia em cada uma tabelada."""
import csv, os, sys
import numpy as np
from scipy.signal import welch
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(AQUI, '..')); sys.path.insert(0, RAIZ)
import recording  # noqa: E402
from modem import MARY_TONES  # noqa: E402
from plota import Fig, CORES  # noqa: E402

CAP = os.path.join(RAIZ, 'captures')
GRAV = [('ar-condicionado ligado', '20261008-160944-f00-piso'), ('silencio', '20261008-161258-f00-piso')]
FS = 48000
LO, HI = 300, 4000
curvas = []
for rot, stem in GRAV:
    r = recording.read(os.path.join(CAP, stem + '.wav'))
    x = np.asarray(r[0] if isinstance(r, tuple) else r, float)
    f, p = welch(x, FS, window='hann', nperseg=8192)
    curvas.append((rot, stem, f, 10 * np.log10(p + 1e-30), 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-30)))
sel = (curvas[0][2] >= LO) & (curvas[0][2] <= HI)
ymax = 10 * np.ceil(max(c[3][sel].max() for c in curvas) / 10)
ymin = ymax - 70
fig = Fig(1100, 580, (LO, HI), (ymin, ymax), 'f (Hz)', 'densidade de potencia (dB re 1/Hz, fs=1)',
          'F-C piso da sala (faixas dos 16 tons em cinza)', xticks=range(500, HI + 1, 500), yticks=np.arange(ymin, ymax + 1, 10))
for t in MARY_TONES:
    a, b = fig.px(t - 40), fig.px(t + 40)
    fig.img[fig.y0 + 1:fig.y1, a:b + 1] = np.minimum(fig.img[fig.y0 + 1:fig.y1, a:b + 1], 235)
fig.frame()
rows = []
for i, (rot, stem, f, db, rms) in enumerate(curvas):
    m = (f >= LO) & (f <= HI)
    fig.line(f[m], db[m], CORES[i], 1)
    fig.legenda('%s (rms %.1f dBFS)' % (rot, rms), CORES[i])
    pw = 10 ** (db / 10)
    for t in MARY_TONES:
        mm = (f >= t - 40) & (f <= t + 40)
        rows.append([rot, stem, t, '%.2f' % (10 * np.log10(pw[mm].mean()))])
    print(rot, stem, 'rms dBFS %.1f' % rms, 'media nas faixas dos tons %.1f dB' % np.mean([float(r[3]) for r in rows if r[0] == rot]))
fig.salva(os.path.join(AQUI, 'fig-c-piso-da-sala.png'))
with open(os.path.join(AQUI, 'piso-por-tom.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['condicao', 'gravacao', 'tom_Hz', 'densidade_media_dB_na_faixa_40Hz']); w.writerows(rows)
# diferenca ligado - silencio por tom
d = {}
for r in rows: d.setdefault(r[0], []).append(float(r[3]))
dif = np.array(d['ar-condicionado ligado']) - np.array(d['silencio'])
print('diferenca ligado-silencio por tom (dB):', ' '.join('%.1f' % v for v in dif))
