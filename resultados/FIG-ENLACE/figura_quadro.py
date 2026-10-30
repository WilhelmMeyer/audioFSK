"""Figura do artigo: o quadro codificado no tempo e o codificador convolucional.

Esquema, não gravação. Em cima, um bloco de 48 bytes em 16-FSK, sem repetição,
com as varreduras de sincronismo, em escala: as contagens vêm de fec.py
(preâmbulo, palavra de referência, bloco codificado, final ocioso) e de
modem.py / console.py (varredura de 80 ms, silêncio de 30 ms, símbolo de 10 ms).
Embaixo, o codificador de taxa 1/3 e comprimento de restrição 7, com as
ligações dos polinômios 171, 133 e 165 (octal) como fec._tables as aplica:
o bit 6 do polinômio é o bit que entra, o bit 0 o mais antigo dos seis.

    ./venv/bin/python resultados/FIG-ENLACE/figura_quadro.py
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

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


def codificador(ax):
    w, h, x0, y0 = 1.0, 0.7, 0.6, 3.7
    nomes = ['bit que\nentra'] + [''] * 6
    for j in range(7):
        x = x0 + j * (w + 0.25)
        ax.add_patch(Rectangle((x, y0), w, h, fc=GELO if j == 0 else 'white', ec=TINTA, lw=0.7))
        ax.text(x + w / 2, y0 + h / 2, '$b$' if j == 0 else f'$b_{{-{j}}}$', ha='center',
                va='center', fontsize=8, color=TINTA)
    ax.annotate('', xy=(x0, y0 + h / 2), xytext=(x0 - 0.55, y0 + h / 2),
                arrowprops=dict(arrowstyle='->', color=TINTA, lw=0.7))
    xa, xb = x0 + 1 * (w + 0.25), x0 + 6 * (w + 0.25) + w
    ax.annotate('', xy=(xa, y0 + h + 0.25), xytext=(xb, y0 + h + 0.25),
                arrowprops=dict(arrowstyle='<->', color=TINTA, lw=0.6))
    ax.text(x0 + w / 2, y0 + h + 0.12, 'bit que\nentra', ha='center', va='bottom', fontsize=7, linespacing=1.05)
    ax.text((xa + xb) / 2, y0 + h + 0.33, 'os seis bits anteriores', ha='center',
            va='bottom', fontsize=7)
    xs = xb + 0.7
    for i, p in enumerate(fec.POLYS_R13):
        y = 2.9 - i * 1.05
        tapx = [x0 + j * (w + 0.25) + w / 2 for j in range(7) if (p >> (6 - j)) & 1]
        for x in tapx:
            ax.plot([x, x], [y0, y], color=TEAL, lw=0.7)
            ax.plot(x, y, 'o', color=TEAL, ms=2.6)
        ax.plot([tapx[0], xs - 0.22], [y, y], color=TEAL, lw=0.7)
        ax.add_patch(Circle((xs, y), 0.22, fc='white', ec=TEAL, lw=0.8))
        ax.text(xs, y - 0.01, '+', ha='center', va='center', fontsize=9, color=TEAL)
        ax.annotate('', xy=(xs + 0.6, y), xytext=(xs + 0.22, y),
                    arrowprops=dict(arrowstyle='->', color=TEAL, lw=0.7))
        ax.text(xs + 0.68, y, f'bit {i + 1}, {p:o} octal', ha='left', va='center',
                fontsize=7, color=TINTA, linespacing=1.05)
    ax.text(xs + 0.68, 2.9 + 0.45, 'bits emitidos', ha='left', va='bottom', fontsize=7, color=TINTA)
    ax.text(xs, 2.9 - 3 * 1.05 + 0.35, '+  ou-exclusivo', ha='center', va='center', fontsize=7, color=TEAL)
    ax.set_xlim(-0.2, xs + 3.3)
    ax.set_ylim(-0.1, 5.1)
    ax.set_aspect('equal')
    ax.axis('off')


def main():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.4, 3.6),
                                 gridspec_kw=dict(height_ratios=[1, 1.05]))
    t = fila(a1)
    codificador(a2)
    fig.tight_layout(h_pad=0.6)
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    _, codif = trechos()
    print('[quadro]', ', '.join(SAIDAS))
    print(f'    total {t:.0f} ms; bits codificados {codif}')


if __name__ == '__main__':
    main()
