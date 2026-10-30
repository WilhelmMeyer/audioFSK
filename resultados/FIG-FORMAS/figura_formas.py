"""Figura do artigo: o que cada uma das quatro formas emite para o mesmo byte.

Esquema, não gravação: para os bits 1011 0010, marca em cada símbolo as
frequências que soam, com os tons tirados de modem.py (Bell 202, MFSK_TONES_0/1,
MARY_TONES e gray_table). Eixo horizontal em símbolos; a duração do símbolo
está no título de cada painel.

    ./venv/bin/python resultados/FIG-FORMAS/figura_formas.py
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import modem

BITS = [1, 0, 1, 1, 0, 0, 1, 0]
TEAL = '#0F5257'
CINZA = '#C9D3D6'
SAIDAS = (os.path.join(AQUI, 'formas-transmissao.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'formas-transmissao.png'))

plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})


def formas():
    t0, t1 = modem.MFSK_TONES_0, modem.MFSK_TONES_1
    todos5 = sorted(t0 + t1)
    fsk = [((1200 if b else 2200),) for b in BITS]
    vot = [tuple(t1 if b else t0) for b in BITS]
    grupos = [BITS[0:5], BITS[5:8] + [0, 0]]
    par = [tuple((t1 if b else t0)[i] for i, b in enumerate(g)) for g in grupos]
    gray = modem.gray_table(4)
    nib = [BITS[0:4], BITS[4:8]]
    mary = [(modem.MARY_TONES[gray[int(''.join(map(str, n)), 2)]],) for n in nib]
    return [
        ('2-FSK: 1 bit por símbolo, símbolo de 0,83 ms', fsk, (1200, 2200),
         [str(b) for b in BITS]),
        ('5×2-FSK votada: o mesmo bit nos 5 pares, símbolo de 10 ms', vot, todos5,
         [str(b) for b in BITS]),
        ('5×2-FSK multicanal: 5 bits por símbolo, um por par, símbolo de 10 ms', par, todos5,
         [''.join(map(str, grupos[0])), ''.join(map(str, BITS[5:8])) + ' + 2 bits seguintes']),
        ('16-FSK: 4 bits por símbolo em um tom, símbolo de 10 ms', mary, modem.MARY_TONES,
         [''.join(map(str, n)) for n in nib]),
    ]


def main():
    fig, eixos = plt.subplots(4, 1, figsize=(6.3, 5.6), sharex=False)
    for ax, (titulo, simbolos, grade, rotulos) in zip(eixos, formas()):
        for f in grade:
            ax.axhline(f, color=CINZA, lw=0.5, zorder=0)
        for k, tons in enumerate(simbolos):
            for f in tons:
                ax.plot([k + 0.08, k + 0.92], [f, f], color=TEAL, lw=3.2,
                        solid_capstyle='butt', zorder=2)
            ax.text(k + 0.5, 3650, rotulos[k], ha='center', va='bottom', fontsize=7.5,
                    color=TEAL)
        for k in range(len(simbolos) + 1):
            ax.axvline(k, color='0.75', lw=0.5, ls=':', zorder=1)
        ax.set_xlim(0, max(len(simbolos), 2))
        ax.set_ylim(500, 3950)
        ax.set_xticks([k + 0.5 for k in range(len(simbolos))])
        ax.set_xticklabels([str(k + 1) for k in range(len(simbolos))])
        ax.set_yticks([1000, 2000, 3000])
        ax.set_ylabel('Hz')
        ax.set_title(titulo, fontsize=8.5, loc='left')
        for lado in ('top', 'right'):
            ax.spines[lado].set_visible(False)
    eixos[-1].set_xlabel('Símbolo; acima de cada símbolo, os bits que ele carrega')
    fig.tight_layout(h_pad=0.9)
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[formas]', ', '.join(SAIDAS))


if __name__ == '__main__':
    main()
