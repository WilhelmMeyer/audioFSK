"""Figura do artigo: o quadro codificado no tempo.

Esquema, não gravação. Um bloco de 48 bytes em 16-FSK, sem repetição,
com as varreduras de sincronismo, em escala: as contagens vêm de fec.py
(preâmbulo, palavra de referência, bloco codificado, final ocioso) e de
modem.py / console.py (varredura de 80 ms, silêncio de 30 ms, símbolo de 10 ms).
O codificador está em figura_codificador.py.

    ./venv/bin/python resultados/FIG-ENLACE/figura_quadro.py
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import fec
import modem
from console import SYNC_HUSH

NBYTES, REP, BITS = 48, 1, 4
TEAL = '#0F5257'
TEAL_MED = '#2E7D82'
GELO = '#BFDDE4'
CINZA = '#C9D3D6'
TINTA = '#2e231b'
SAIDAS = (os.path.join(AQUI, 'quadro-codificado.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'quadro-codificado.png'))

plt.rcParams.update({'font.size': 7.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})


def virgula(v, casas=0):
    return f'{v:.{casas}f}'.replace('.', ',')


def trechos():
    """(rótulo, duração em ms, cor) de cada trecho do quadro, na ordem do ar."""
    ms_sim = 1000 / 100
    pre = len(fec.preamble_bits('mary', symbol_bits=BITS)) / BITS
    sync = len(fec.SYNC)
    corpo = len(fec.frame(bytes(NBYTES), repeat=REP))
    codif = corpo - sync
    ocioso = fec.frame_symbols(NBYTES, REP, BITS) - pre - -(-corpo // BITS)
    assert pre + -(-corpo // BITS) + ocioso == fec.frame_symbols(NBYTES, REP, BITS)
    varr = modem.SYNC_CHIRP[2] * 1000
    sil = SYNC_HUSH * 1000
    return [
        ('varredura', varr, TEAL_MED),
        ('', sil, None),
        (f'preâmbulo\n{pre:.0f}\nsímbolos', pre * ms_sim, CINZA),
        (f'palavra de\nreferência\n{sync} bits', sync / BITS * ms_sim, TEAL),
        (f'bloco codificado\ne entrelaçado\n{NBYTES * 8} bits de dados\n{codif} bits no ar',
         codif / BITS * ms_sim, GELO),
        ('final\nocioso', ocioso * ms_sim, CINZA),
        ('', sil, None),
        ('varredura', varr, TEAL_MED),
    ], codif


def fila(ax):
    partes, _ = trechos()
    t = 0
    for i, (rot, d, cor) in enumerate(partes):
        if cor:
            ax.add_patch(Rectangle((t, 0), d, 2, fc=cor, ec=TINTA, lw=0.6))
        meio = t + d / 2
        if rot.startswith('bloco') or rot.startswith('preâmbulo'):
            ax.text(meio, 1.0, rot, ha='center', va='center', fontsize=7, color=TINTA, linespacing=1.05)
        elif rot:
            acima = rot.startswith('palavra') or rot == 'varredura'
            y = 2.3 if acima else -0.3
            ax.annotate(rot, xy=(meio, 2 if acima else 0), xytext=(meio, y),
                        ha='center', va='bottom' if acima else 'top', fontsize=7,
                        color=TINTA, arrowprops=dict(arrowstyle='-', color=TINTA, lw=0.6))
        t += d
    ax.set_xlim(-30, t + 30)
    ax.set_ylim(-1.6, 4.0)
    ax.set_yticks([])
    for s in ('left', 'right', 'top'):
        ax.spines[s].set_visible(False)
    total = (fec.frame_symbols(NBYTES, REP, BITS) * 10 + 2 * (modem.SYNC_CHIRP[2] + SYNC_HUSH) * 1000)
    ax.set_xlabel(f'Tempo (ms); quadro de {virgula(total)} ms, {NBYTES} bytes', fontsize=7.5)
    ax.set_xticks([0, 1000, 2000, 3000, 4000])
    ax.tick_params(labelsize=7)
    return t


def main():
    fig, a1 = plt.subplots(figsize=(3.4, 1.75))
    t = fila(a1)
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    _, codif = trechos()
    print('[quadro]', ', '.join(SAIDAS))
    print(f'    total {t:.0f} ms; bits codificados {codif}')


if __name__ == '__main__':
    main()
