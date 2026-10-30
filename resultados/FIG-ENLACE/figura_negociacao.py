"""Figura do artigo: uma sessão do enlace negociado, no tempo.

Sessão 3 do H07-ENLACE-MODOS (2026-10-22, 16-FSK, ~2 m), reconstruída dos dois
diários (chamador e ouvinte). Cada seta vai de quem transmite, no instante em
que acabou de ler o turno anterior, a quem recebe, no instante em que leu o
quadro. O relógio do ouvinte foi trazido ao do chamador pela chamada: o
ouvinte a ouviu em 8,92 s do seu relógio, emitida em 0,90 s do chamador, e o
OLA lido em 15,40 s confirma o deslocamento (DESLOC = 7,8 s). Escala real.

    ./venv/bin/python resultados/FIG-ENLACE/figura_negociacao.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
SAIDAS = (os.path.join(AQUI, 'negociacao.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'negociacao.png'))
TEAL = '#0F5257'
CINZA = '#C9D3D6'
FALHA = '#B5462F'
DESLOC = 7.8

plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 7.5, 'axes.linewidth': 0.7,
                     'savefig.dpi': 300, 'figure.dpi': 300})

C, O = 'C', 'O'      # chamador, ouvinte
# (de, t_leitura_no_destino em s do relógio de quem leu, rótulo, falhou)
# Tempos copiados dos diários: chamador 20261022-163530, ouvinte 20261022-163524.
# O quadro ilegível entra pela linha "turno: -, 1 ilegível(is)" (107,95 s do ouvinte),
# fim da leitura; o "em 103,13 s" do diário é onde o quadro começava.
TURNOS = [
    (C, 8.92, 'chamada', False),
    (O, 3.41, 'resposta', False),
    (C, 15.40, 'saudação', False),
    (O, 13.91, 'saudação', False),
    (C, 34.18, 'sondagem', False),
    (O, 46.38, 'contrato e sondagem', False),
    (C, 61.91, 'contrato e dados', False),
    (O, 59.90, 'dados', False),
    (C, 70.40, 'dados', False),
    (O, 68.91, 'dados', False),
    (C, 78.93, 'dados', False),
    (O, 76.42, 'confirmação', False),
    (C, 85.93, 'dados', False),
    (O, 83.41, 'confirmação', False),
    (C, 92.93, 'dados', False),
    (O, 90.92, 'confirmação', False),
    (C, 99.93, 'dados', False),
    (O, 97.92, 'confirmação', False),
    (C, 107.95, 'dados, ilegível', True),
    (O, 105.94, 'pedido de novo', False),
    (C, 114.90, 'retransmissão', False),
    (O, 113.41, 'confirmação', False),
]
FASES = [(0, 13.9, 'saudação'), (13.9, 54.1, 'sondagem e\ncontratos'),
         (54.1, 113.4, 'dados em pare-e-espere')]
# só o quadro ilegível leva rótulo; as fases nomeiam o resto, e o texto descreve cada turno
ROTULOS = {18: 'ilegível'}


def main():
    # tempo na horizontal, para a figura caber baixa na coluna
    fig, ax = plt.subplots(figsize=(3.4, 1.75))
    ys = {C: 1.0, O: 0.0}
    for y in ys.values():
        ax.plot([0, 118], [y, y], color=TEAL, lw=1.0)
    ax.text(-2, 1, 'chama', ha='right', va='center', fontsize=7, color=TEAL)
    ax.text(-2, 0, 'escuta', ha='right', va='center', fontsize=7, color=TEAL)
    t = 0.90                       # a chamada sai em 0,90 s do chamador
    for i, (de, lido, rot, falhou) in enumerate(TURNOS):
        fim = lido - DESLOC if de == C else lido
        para = O if de == C else C
        cor = FALHA if falhou else TEAL
        ax.annotate('', xy=(fim, ys[para]), xytext=(t, ys[de]),
                    arrowprops=dict(arrowstyle='-|>', color=cor, lw=0.7, mutation_scale=5,
                                    shrinkA=0, shrinkB=0, ls='--' if falhou else '-'))
        if i in ROTULOS:
            ax.text((t + fim) / 2, 0.5, ROTULOS[i], ha='center', va='center', fontsize=5.8,
                    color=cor, linespacing=1.0,
                    bbox=dict(boxstyle='square,pad=0.06', fc='white', ec='none'))
        t = fim
    for a, b, nome in FASES:
        ax.plot([a + 0.6, a + 0.6, b - 0.6, b - 0.6], [1.12, 1.18, 1.18, 1.12],
                color=TEAL, lw=0.7)
        x, ha = ((b - 1, 'right') if a == 0 else ((a + b) / 2, 'center'))
        ax.text(x, 1.24, nome, ha=ha, va='bottom', fontsize=6.5, color=TEAL, linespacing=1.0)
    ax.set_xlim(-14, 120)
    ax.set_ylim(-0.12, 1.6)
    ax.set_yticks([])
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel('Tempo (s)')
    for lado in ('top', 'left', 'right'):
        ax.spines[lado].set_visible(False)
    ax.spines['bottom'].set_bounds(0, 118)
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[negociacao]', ', '.join(SAIDAS))


if __name__ == '__main__':
    main()
