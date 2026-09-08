"""Desenho da bancada: duas maquinas, alto-falante, microfone e o ar entre elas.

Nao e medida, e esquema. Existe porque o texto descreve o arranjo em prosa e o
leitor precisa ver de onde sai e onde entra o som.

O microfone aparece como externo, ligado por cabo a maquina que grava, porque
assim o caminho do sinal fica visivel; na bancada foi o interno dela.

O cabo serial de controle NAO aparece, por decisao do autor: ele nao conduz
dado da medida e desenha-lo sugeriria que conduz.

    ./venv/bin/python artigo/figura_bancada.py
"""

import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Wedge

AQUI = pathlib.Path(__file__).resolve().parent
SAIDA = AQUI / 'figuras' / 'bancada.png'

TINTA = '#1B7F79'
CINZA = '0.35'


def maquina(eixo, x, y, rotulo):
    """Um notebook visto de lado: base e tela."""
    eixo.add_patch(FancyBboxPatch((x, y), 1.9, 0.16, boxstyle='round,pad=0.02',
                                  fc='0.92', ec=CINZA, lw=1.2))
    eixo.add_patch(FancyBboxPatch((x + 0.12, y + 0.16), 1.66, 0.8,
                                  boxstyle='round,pad=0.02',
                                  fc='white', ec=CINZA, lw=1.2))
    eixo.text(x + 0.95, y + 1.12, rotulo, ha='center', va='bottom', fontsize=10)


def alto_falante(eixo, x, y):
    eixo.add_patch(plt.Rectangle((x, y), 0.34, 0.5, fc='0.85', ec=CINZA, lw=1.2))
    eixo.add_patch(plt.Circle((x + 0.17, y + 0.32), 0.1, fc='white', ec=CINZA, lw=1.0))
    eixo.add_patch(plt.Circle((x + 0.17, y + 0.12), 0.05, fc='white', ec=CINZA, lw=1.0))
    for r in (0.16, 0.26, 0.36):
        eixo.add_patch(Wedge((x + 0.34, y + 0.3), r, -35, 35, width=0.015,
                             fc=TINTA, ec=TINTA))
    eixo.text(x + 0.17, y - 0.12, 'alto-falante', ha='center', va='top', fontsize=9)


def microfone(eixo, x, y):
    eixo.add_patch(FancyBboxPatch((x, y), 0.16, 0.34, boxstyle='round,pad=0.03',
                                  fc='0.85', ec=CINZA, lw=1.2))
    eixo.text(x + 0.08, y - 0.14, 'microfone', ha='center', va='top', fontsize=9)


def main():
    fig, eixo = plt.subplots(figsize=(6.3, 2.6), layout='constrained')

    maquina(eixo, 0.2, 0.75, 'máquina que transmite')
    maquina(eixo, 4.6, 0.75, 'máquina que grava')
    alto_falante(eixo, 2.35, 0.85)
    microfone(eixo, 4.05, 0.95)

    # cada transdutor ligado a sua maquina
    eixo.plot([2.1, 2.35], [0.93, 0.93], color=CINZA, lw=1.2)
    eixo.plot([4.21, 4.72], [1.05, 1.05], color=CINZA, lw=1.2)

    # o ar
    eixo.annotate('', xy=(4.0, 1.15), xytext=(2.9, 1.15),
                  arrowprops=dict(arrowstyle='-|>', color=TINTA, lw=1.6))
    eixo.text(3.45, 1.42, 'transmissão de dados\nem meio acústico', ha='center',
              fontsize=9.5, color=TINTA, linespacing=1.3)

    eixo.set_xlim(0, 6.7)
    eixo.set_ylim(0.35, 2.6)
    eixo.axis('off')
    SAIDA.parent.mkdir(exist_ok=True)
    fig.savefig(SAIDA, dpi=300)
    print('escrito', SAIDA)


if __name__ == '__main__':
    main()
