"""Figura do artigo: o codificador convolucional com um exemplo numérico.

Esquema. Sete caixas com o bit que entra e os seis anteriores; cada linha de
saída marca as caixas ligadas pelo seu polinômio (171, 133, 165 em octal, como
fec._tables os aplica: o bit 6 do polinômio é o bit que entra, o bit 0 o mais
antigo) e escreve o valor que entra na conta. O resultado de cada linha é
conferido contra a tabela do próprio codificador.

    ./venv/bin/python resultados/FIG-ENLACE/figura_codificador.py
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

BITS = [1, 0, 0, 1, 0, 0, 1]          # b, b-1, ..., b-6
TEAL = '#0F5257'
GELO = '#BFDDE4'
TINTA = '#2e231b'
SAIDAS = (os.path.join(AQUI, 'codificador.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'codificador.png'))

plt.rcParams.update({'font.size': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})


def confere():
    saida, _ = fec._tables(fec.POLYS_R13)
    estado = int(''.join(map(str, BITS[1:])), 2)
    return [int(v) for v in saida[estado, BITS[0]]]


def main():
    esperado = confere()
    W, H = 3.4, 2.85                   # coordenadas em polegadas
    w, passo, x0, y0 = 0.22, 0.26, 0.66, 2.0
    xc = [x0 + j * passo + w / 2 for j in range(7)]
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])

    for j, b in enumerate(BITS):
        ax.add_patch(Rectangle((x0 + j * passo, y0), w, w, fc=GELO if j == 0 else 'white',
                               ec=TINTA, lw=0.7))
        ax.text(xc[j], y0 + w / 2, str(b), ha='center', va='center', fontsize=8,
                color=TINTA, weight='bold')
        nome = '$b$' if j == 0 else f'$b_{{-{j}}}$'
        ax.text(xc[j], y0 + w + 0.04, nome, ha='center', va='bottom', fontsize=7, color=TINTA)
    ax.text(xc[0], y0 + w + 0.24, 'bit que\nentra', ha='center', va='bottom', fontsize=7,
            linespacing=1.0, color=TINTA)
    xa, xb = x0 + passo + 0.04, x0 + 6 * passo + w
    ax.annotate('', xy=(xa, y0 + w + 0.3), xytext=(xb, y0 + w + 0.3),
                arrowprops=dict(arrowstyle='<->', color=TINTA, lw=0.6))
    ax.text((xa + xb) / 2, y0 + w + 0.34, 'bits anteriores', ha='center', va='bottom',
            fontsize=7, color=TINTA)

    xs = xb + 0.16
    for i, p in enumerate(fec.POLYS_R13):
        y = 1.78 - i * 0.44
        lig = [j for j in range(7) if (p >> (6 - j)) & 1]
        for j in lig:
            ax.plot([xc[j], xc[j]], [y0, y], color=TEAL, lw=0.6, alpha=0.5)
            ax.plot(xc[j], y, 'o', color=TEAL, ms=2.6)
            ax.text(xc[j] + 0.03, y + 0.02, str(BITS[j]), ha='left', va='bottom',
                    fontsize=7, color=TEAL)
        ax.plot([xc[lig[0]], xs - 0.07], [y, y], color=TEAL, lw=0.7)
        ax.add_patch(Circle((xs, y), 0.07, fc='white', ec=TEAL, lw=0.8))
        ax.plot([xs - 0.045, xs + 0.045], [y, y], color=TEAL, lw=0.7)
        ax.plot([xs, xs], [y - 0.045, y + 0.045], color=TEAL, lw=0.7)
        uns = sum(BITS[j] for j in lig)
        r = uns % 2
        assert r == esperado[i], (p, r, esperado)
        ax.text(xs + 0.12, y + 0.07, f'= {r}', ha='left', va='center', fontsize=8,
                color=TINTA, weight='bold')
        ax.text(xs + 0.12, y - 0.1, f'{uns} uns, {"ímpar" if r else "par"}', ha='left',
                va='center', fontsize=7, color=TINTA)
        padrao = format(p, '07b')
        assert [j for j in range(7) if padrao[j] == '1'] == lig
        for j, c in enumerate(padrao):
            ax.text(xc[j], y - 0.06, c, ha='center', va='top', fontsize=7, color='#7A8588',
                    bbox=dict(fc='white', ec='none', pad=0.4))
        for j in (0, 3):
            xm = (xc[j] + xc[j + 1]) / 2
            ax.plot([xm, xm], [y - 0.08, y - 0.19], color='#B5BEC0', lw=0.5)
        ax.text(x0 - 0.05, y - 0.13, f'{p:o} octal =', ha='right', va='center', fontsize=7,
                color='#7A8588')

    ax.text(0.05, 0.5, f'{" ".join(map(str, esperado))} vão para o ar', ha='left',
            va='center', fontsize=7.5, color=TINTA, weight='bold')
    ax.annotate('', xy=(0.27, 0.3), xytext=(0.05, 0.3),
                arrowprops=dict(arrowstyle='->', color=TINTA, lw=0.7))
    ax.text(0.33, 0.3, 'o próximo bit entra e a fila anda uma casa', ha='left',
            va='center', fontsize=7, color=TINTA)
    ax.text(0.05, 0.0, 'ou-exclusivo: 1 se a quantidade de uns é ímpar; cada caixa\n'
            'ligada vale 1 e cada não ligada vale 0, e o padrão de cada\n'
            'linha, em octal, é o nome do grupo', ha='left', va='center', fontsize=7,
            color='#5F6B6E', linespacing=1.05)

    ax.set_xlim(0, W)
    ax.set_ylim(-0.25, H - 0.05)
    ax.axis('off')
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight', pad_inches=0.03)
    print('[codificador]', ', '.join(SAIDAS), 'saida', esperado)


if __name__ == '__main__':
    main()
