"""Figura do artigo: um quadro curto entre as duas varreduras de sincronismo.

Sintético, não gravação: o próprio modulador do sistema gera varredura inicial,
silêncio, 16 símbolos de 16-FSK (8 bytes), silêncio e varredura final, sem
passar por alto-falante, ar ou microfone. Curto de propósito, para que cada
símbolo apareça. Formato do visor: frequência na horizontal, tempo na vertical
com o mais recente no alto, rampa de cores do visor/index.html. Largura de uma
coluna (3,5 pol. = 8,8 cm, sem redução no documento) e ~5 cm de altura. As linhas
horizontais são as fronteiras de símbolo pela grade T = (n2 - n1) / S, com n1 e
n2 achados por modem.find_chirp_pair, como o receptor faz.

    ./venv/bin/python resultados/FIG-SINCRONISMO/figura_sincronismo.py
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import modem

FS = 48000
DADOS = b'audioFSK'          # 8 bytes, 16 símbolos
HUSH = 0.01
FMIN, FMAX = 600, 3600
SAIDAS = (os.path.join(AQUI, 'sincronismo-varreduras.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'sincronismo-varreduras.png'))
PARADAS = [(0, (239, 230, 207)), (.35, (214, 186, 140)), (.6, (178, 104, 62)),
           (.82, (110, 48, 24)), (1, (40, 28, 20))]
VISOR = LinearSegmentedColormap.from_list(
    'visor', [(t, tuple(c / 255 for c in rgb)) for t, rgb in PARADAS])
TINTA = '#2e231b'
CHEGA = '#4d6b8c'
NPER, PASSO, NFFT = 240, 12, 4096

plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})


def main():
    mod = modem.MaryModulator(fs=FS)
    sps = mod.samples_per_symbol
    dados = mod.modulate(DADOS) * 0.5
    S = len(dados) // sps + 2 * int(round(HUSH * FS / sps))
    v = modem.chirp(fs=FS) * 0.5
    z = np.zeros(int(HUSH * FS))
    borda = np.zeros(int(0.01 * FS))
    x = np.concatenate([borda, v, z, dados, z, v, borda])
    x = x + np.random.default_rng(1).normal(0, 1e-4, len(x))
    n1, n2 = modem.find_chirp_pair(x, modem.chirp(fs=FS), min_gap=int(0.5 * S * sps))
    T = (n2 - n1) / S

    jan = np.hanning(NPER)
    nq = (len(x) - NPER) // PASSO
    q = np.stack([x[i * PASSO:i * PASSO + NPER] * jan for i in range(nq)])
    db = 20 * np.log10(np.maximum(np.abs(np.fft.rfft(q, NFFT, axis=1)) * 2 / jan.sum(), 1e-9))
    f = np.fft.rfftfreq(NFFT, 1 / FS)
    t = (np.arange(nq) * PASSO + NPER / 2) / FS * 1e3
    b = (f >= FMIN) & (f <= FMAX)
    teto = np.percentile(db[:, b], 99.5)

    fig, ax = plt.subplots(figsize=(3.5, 2.05))
    ax.imshow(db[:, b], aspect='auto', origin='lower', cmap=VISOR, vmin=teto - 40, vmax=teto,
              interpolation='nearest', extent=(f[b][0], f[b][-1], t[0], t[-1]))
    for k in range(S + 1):
        ax.axhline((n1 + k * T) / FS * 1e3, color=CHEGA, lw=0.35, alpha=0.6)
    y1, y2 = n1 / FS * 1e3, n2 / FS * 1e3
    for y, nome in ((y1, '$n_1$'), (y2, '$n_2$')):
        ax.axhline(y, color=CHEGA, lw=1.0)
        ax.text(FMAX + 30, y, nome, color=CHEGA, fontsize=8, va='center', ha='left')
    lv = len(v) / FS * 1e3
    # Rótulos no triângulo vazio ao lado de cada varredura, dentro da área.
    ax.text(FMIN + 60, y1 - lv * 0.3, 'varredura inicial', fontsize=7.5, color=TINTA,
            va='center', ha='left')
    ax.text(FMAX - 60, y2 + lv * 0.3, 'varredura final', fontsize=7.5, color=TINTA,
            va='center', ha='right')
    # Seta acima do tom mais agudo (3325 Hz), rótulo na margem, entre n1 e n2.
    ax.annotate('', xy=(FMAX - 35, y2), xytext=(FMAX - 35, y1),
                arrowprops=dict(arrowstyle='<->', color=TINTA, lw=0.8))
    ax.text(FMAX + 40, (y1 + y2) / 2, f'$S$ = {S}', rotation=90, va='center', ha='left',
            fontsize=7.5, color=TINTA)
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel('Tempo (ms)')
    ax.set_xticks([1000, 2000, 3000])
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[sincronismo]', ', '.join(SAIDAS))
    print(f'    S {S}, n1 {n1}, n2 {n2}, T {T:.3f} amostras')


if __name__ == '__main__':
    main()
