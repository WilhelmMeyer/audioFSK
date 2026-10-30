"""Figura do artigo: as duas varreduras de sincronismo e a grade de símbolos.

Espectrograma de um quadro de 16-FSK gravado com as varreduras, no formato do
visor: frequência no eixo horizontal, tempo no vertical com o mais recente no
alto, e a mesma escala de cores (papel, sépia, ferrugem, baquelite, 55 dB a
partir do piso). Dois painéis: o início do quadro, com a varredura inicial, e
o fim, com a final. Sobre cada um, as fronteiras de símbolo que as varreduras
determinam: início na primeira, período (n2 - n1) / S entre as duas.

    ./venv/bin/python resultados/F04-16FSK-10CM/figuras/figura_varreduras.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, RAIZ)
import modem
import recording

STEM = os.path.join(RAIZ, 'resultados', 'F04-16FSK-10CM', 'gravacao', '20261008-172827-f04-16fsk-10cm-r1')
SAIDAS = (os.path.join(AQUI, 'varreduras-sincronismo.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'varreduras-sincronismo.png'))
FS = recording.FS
TRECHO = 0.30          # segundos mostrados em cada extremo
NPER, PASSO, NFFT = 480, 120, 4096  # janela de 10 ms, passo de 2,5 ms
FAIXA_DB = 45.0        # o visor usa 55; 45 dá contraste no papel

# A rampa do visor (visor/index.html, fazLut).
PARADAS = [(0, (239, 230, 207)), (.35, (214, 186, 140)), (.6, (178, 104, 62)),
           (.82, (110, 48, 24)), (1, (40, 28, 20))]
VISOR = LinearSegmentedColormap.from_list(
    'visor', [(t, tuple(c / 255 for c in rgb)) for t, rgb in PARADAS])
TINTA = '#2e231b'
CHEGA = '#4d6b8c'

plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


def espectrograma(x):
    jan = np.hanning(NPER)
    n = (len(x) - NPER) // PASSO
    quadros = np.stack([x[i * PASSO:i * PASSO + NPER] * jan for i in range(n)])
    e = np.abs(np.fft.rfft(quadros, NFFT, axis=1)) * 2 / jan.sum()
    f = np.fft.rfftfreq(NFFT, 1 / FS)
    t = (np.arange(n) * PASSO + NPER / 2) / FS
    return t, f, 20 * np.log10(np.maximum(e, 1e-9))


def main():
    x = recording.read(STEM + '.wav')
    meta = json.load(open(STEM + '.json'))
    span = meta['sync_span_symbols']
    sps = FS // meta['baud']
    n1, n2 = modem.find_chirp_pair(x, modem.chirp(), min_gap=int(0.5 * span * sps))
    periodo = (n2 - n1) / span
    lv = len(modem.chirp())

    t, f, db = espectrograma(x)
    teto = np.percentile(db[:, (f > 600) & (f < 3600)], 99.5)
    piso = teto - FAIXA_DB
    banda = (f >= 500) & (f <= 3600)
    a = (n1 - lv) / FS - 0.15
    b = (n2 + lv) / FS + 0.15
    sel = (t >= a) & (t <= b)

    fig, ax = plt.subplots(figsize=(3.6, 4.8))
    ax.imshow(db[sel][:, banda], aspect='auto', origin='lower', cmap=VISOR,
              vmin=piso, vmax=teto, interpolation='nearest',
              extent=(f[banda][0], f[banda][-1], t[sel][0] - a, t[sel][-1] - a))
    y1, y2 = n1 / FS - a, n2 / FS - a
    for y in (y1, y2):
        ax.axhline(y, color=CHEGA, lw=0.9)
    ax.annotate('varredura inicial', xy=(2050, y1 - lv / 2 / FS), xytext=(2300, y1 - 0.12),
                fontsize=7.5, color=TINTA, arrowprops=dict(arrowstyle='-', color=TINTA, lw=0.7),
                bbox=dict(fc='#efe6cf', ec='none', pad=0.8))
    ax.annotate('varredura final', xy=(2050, y2 + lv / 2 / FS), xytext=(2300, y2 + 0.12),
                fontsize=7.5, color=TINTA, arrowprops=dict(arrowstyle='-', color=TINTA, lw=0.7),
                bbox=dict(fc='#efe6cf', ec='none', pad=0.8))
    ax.text(560, y1 + 0.02, '$n_1$', color=CHEGA, fontsize=8, va='bottom')
    ax.text(560, y2 - 0.02, '$n_2$', color=CHEGA, fontsize=8, va='top')
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel('Tempo (s), mais recente no alto')
    ax.set_xticks([1000, 2000, 3000])
    # À direita, a contagem de símbolos pela grade de (4): início em n1, passo T.
    dir_ = ax.twinx()
    dir_.set_ylim(ax.get_ylim())
    marcas = list(range(0, int(span) + 1, 100)) + [int(span)]
    dir_.set_yticks([y1 + k * periodo / FS for k in marcas])
    dir_.set_yticklabels([str(k) for k in marcas])
    dir_.set_ylabel('Símbolo, pela grade de (4)')
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[varreduras]', ', '.join(SAIDAS))
    print(f'    n1 {n1}, n2 {n2}, S {span:.0f} símbolos, período {virgula(periodo, 3)} amostras')


if __name__ == '__main__':
    main()
