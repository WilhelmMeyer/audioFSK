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
AJUSTE = {0: -2.6, 2: 0.6}   # rótulos do início, que se encostam
FASES = [(0, 13.9, 'saudação'), (13.9, 54.1, 'sondagem\ne contratos'),
         (54.1, 113.4, 'dados em\npare-e-espere')]


def main():
    fig, ax = plt.subplots(figsize=(3.4, 5.2))
    xs = {C: 0.0, O: 1.0}
    for x in xs.values():
        ax.plot([x, x], [0, 118], color=TEAL, lw=1.0)
    ax.text(0, -3, 'Estação que\nchama', ha='center', va='bottom', fontsize=8, color=TEAL)
    ax.text(1, -3, 'Estação que\nescuta', ha='center', va='bottom', fontsize=8, color=TEAL)
    t = 0.90                       # a chamada sai em 0,90 s do chamador
    for i, (de, lido, rot, falhou) in enumerate(TURNOS):
        fim = lido - DESLOC if de == C else lido
        para = O if de == C else C
        cor = FALHA if falhou else TEAL
        ax.annotate('', xy=(xs[para], fim), xytext=(xs[de], t),
                    arrowprops=dict(arrowstyle='-|>', color=cor, lw=0.8, mutation_scale=6,
                                    shrinkA=0, shrinkB=0, ls='--' if falhou else '-'))
        ym = (t + fim) / 2 + AJUSTE.get(i, 0)
        ax.text(0.5, ym, rot, ha='center', va='center', fontsize=6.2, color=cor,
                bbox=dict(boxstyle='square,pad=0.08', fc='white', ec='none'))
        t = fim
    for a, b, nome in FASES:
        ax.plot([-0.30, -0.36, -0.36, -0.30], [a + 0.8, a + 0.8, b - 0.8, b - 0.8],
                color=TEAL, lw=0.7)
        ax.text(-0.40, (a + b) / 2, nome, ha='right', va='center', fontsize=7, color=TEAL)
    ax.set_ylim(118, -12)
    ax.set_xlim(-1.15, 1.15)
    ax.set_xticks([])
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position('right')
    ax.set_ylabel('Tempo (s)')
    for s in ('top', 'left', 'bottom'):
        ax.spines[s].set_visible(False)
    ax.spines['right'].set_bounds(0, 118)
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[negociacao]', ', '.join(SAIDAS))


if __name__ == '__main__':
    main()
