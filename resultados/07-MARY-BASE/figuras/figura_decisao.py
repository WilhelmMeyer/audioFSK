"""Figura do artigo: a decisao da 16-FSK em um simbolo.

Os dezesseis tons na janela em que o receptor decidiu um simbolo: o
transmitido e os quinze calados. Em cima, a energia medida em cada tom e o
piso corrente dele; embaixo, a mesma medida contada do proprio piso, que e o
numero que a decisao usa.

    ./venv/bin/python resultados/07-MARY-BASE/figuras/figura_decisao.py [--stem S] [--simbolo K] [--out PNG]

A barra sobe do piso do proprio tom ate a energia medida, entao o comprimento
dela e a grandeza comparada, e a diferenca entre a barra do tom detectado e a
do segundo colocado e a margem anotada. Foi para isso que o piso entrou na
figura: o canal e um pente, o ruido de fundo varia de tom para tom, e comparar
alturas absolutas nao e o que o receptor faz.

A linha liga os dezesseis pontos medidos, e nao e a FFT densa da janela. A
FFT densa foi tentada: com 408 amostras e sem janelamento, cada tom vira um
montinho de 118 Hz de largura com covas fundas dos dois lados, que e o formato
da janela e nao o canal, e ocupa a figura falando de uma coisa que a decisao
nao olha. O detector le dezesseis numeros por simbolo, tirados de
`MaryDemodulator._energies`, e sao esses que a figura desenha.

O simbolo desenhado por padrao nao e escolhido a mao. E o simbolo do trecho
das outras duas figuras cuja margem esta mais perto da mediana do bloco, entre
os que saem certos e em que a energia bruta e a normalizada concordam sobre os
dois primeiros colocados. Ou seja, uma decisao comum, e nao a mais folgada nem
a mais apertada.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator

import comum
from comum import (CERTO, CONTORNO, CURVA, ERRADO, GRADE, LARGURA,
                   MARY_TONES, NEGATIVO, virgula)

NOME = '16fsk-decisao.png'
TRECHO = (290, 320)      # o mesmo das outras duas figuras


def db(v):
    return 10.0 * np.log10(np.maximum(np.asarray(v, dtype=np.float64), 1e-30))


def margens(a):
    """Margem de decisao de cada simbolo do quadro, em dB."""
    fora = []
    for j in range(a.simbolos):
        n = a.norma(j)
        o = np.argsort(n)
        fora.append(float(db(n[o[-1]]) - db(n[o[-2]])))
    return np.array(fora)


def tipico(a, margem, k0, k1):
    """O simbolo comum do trecho: margem mais perto da mediana do bloco.

    Com duas condicoes, e nenhuma delas escolhe pelo resultado da figura: o
    simbolo tem de sair certo, e os dois primeiros colocados tem de ser os
    mesmos em energia bruta e depois da divisao pelo piso. A segunda existe
    para que a barra desenhada e a margem anotada falem do mesmo par de tons.
    """
    alvo = float(np.median(margem))
    melhor = None
    for j in range(k0, k1):
        if a.recebido(j) != a.tom[j]:
            continue
        n, e = a.norma(j), a.energia(j)
        o, oe = np.argsort(n), np.argsort(e)
        if o[-1] != oe[-1] or o[-2] != oe[-2]:
            continue
        d = abs(margem[j] - alvo)
        if melhor is None or d < melhor[0]:
            melhor = (d, j)
    if melhor is None:
        raise SystemExit("[decisão] nenhum símbolo comum no trecho")
    return melhor[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stem', default=comum.PADRAO)
    ap.add_argument('--simbolo', type=int, default=None)
    ap.add_argument('--out', action='append', metavar='PNG')
    args = ap.parse_args()

    a = comum.alinha(args.stem)
    margem_bloco = margens(a)
    k = args.simbolo if args.simbolo is not None else tipico(a, margem_bloco,
                                                             *TRECHO)
    i0, i1 = a.janela(k)

    energia, piso, norma = db(a.energia(k)), db(a.piso(k)), a.norma(k)
    ordem = np.argsort(norma)
    detectado, segundo = int(ordem[-1]), int(ordem[-2])
    margem = float(db(norma[detectado]) - db(norma[segundo]))

    # Dois paineis alinhados na frequencia. Em cima o que chegou, que e um
    # espectro; embaixo a grandeza que decide, que e a energia de cada tom
    # contada do proprio piso. Sao a mesma banda e o mesmo instante, e por
    # isso partilham o eixo x; sao quantidades diferentes, e por isso nao
    # partilham o y.
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(LARGURA, 4.6), sharex=True,
                                 height_ratios=(1.25, 1.0), layout='constrained')

    # Uma cor por tom, e a mesma nos dois paineis: e o mesmo tom nos dois, e
    # duas cores diferentes para ele fariam a figura parecer falar de duas
    # coisas. O transmitido, os calados que ainda assim chegaram acima do
    # proprio piso, e os calados que ficaram abaixo dele.
    alturas = db(norma)
    cores = [a.cor(k) if i_t == a.tom[k]
             else (ERRADO if alturas[i_t] > 0 else NEGATIVO)
             for i_t in range(len(MARY_TONES))]

    # Os dezesseis pontos medidos ligados por retas, e nao a FFT densa da
    # janela. A FFT densa foi tentada e desenha um montinho de 118 Hz de
    # largura em cada tom, com covas fundas entre eles: e o formato de uma
    # janela de 408 amostras sem janelamento, nao o canal, e ocupa a figura
    # falando de uma coisa que a decisao nao olha. O detector le dezesseis
    # numeros, e e isso que a linha liga. Ela cai sobre o topo de cada barra
    # por construcao, e tem a mesma forma da linha do piso, que ja era isso.
    ax.plot(MARY_TONES, energia, color=CURVA, linewidth=1.0, zorder=2)
    ax.vlines(MARY_TONES, piso, energia, color=cores, linewidth=2.2, zorder=3)
    ax.plot(MARY_TONES, piso, color=GRADE, linewidth=0.8,
            linestyle=(0, (3, 2)), zorder=4)
    ax.plot([MARY_TONES[detectado]], [energia[detectado]], linestyle='none',
            marker='o', markersize=7, markerfacecolor=a.cor(k),
            markeredgecolor=CONTORNO, markeredgewidth=1.0, zorder=6)
    ax.set_ylabel('Energia na janela\nde decisão (dB)')
    ax.legend(handles=[
        Line2D([], [], color=CURVA, linewidth=1.0,
               label='Energia medida, tom a tom'),
        Line2D([], [], color=GRADE, linewidth=0.8, linestyle=(0, (3, 2)),
               label='Piso corrente de cada tom'),
    ], loc='lower left', bbox_to_anchor=(0.0, 1.01), frameon=False, ncols=2,
        handletextpad=0.6, columnspacing=1.6, borderpad=0.0, fontsize=7.5)

    # As barras: energia de cada tom acima do proprio piso, que e o numero
    # comparado. Mesma espessura e mesmas cores do painel de cima, porque sao
    # os mesmos dezesseis tons medidos na mesma janela; o que muda de um
    # painel para o outro e de onde a barra e contada.
    bx.vlines(MARY_TONES, 0.0, alturas, color=cores, linewidth=2.2, zorder=3)
    bx.axhline(0.0, color=GRADE, linewidth=0.8, zorder=2)

    # A margem, marcada aqui e nao no painel de cima: e a diferenca entre
    # duas barras, e so aqui as duas alturas sao comparaveis a olho.
    xv, xs = MARY_TONES[detectado], MARY_TONES[segundo]
    x_seta = (xv + xs) / 2
    # Uma linha de chamada por barra, e nao so pela mais alta: a flecha mede
    # a distancia entre duas alturas, entao as duas precisam estar marcadas
    # ou ela parece medir de um valor ate coisa nenhuma.
    for x_tom, altura in ((xv, alturas[detectado]), (xs, alturas[segundo])):
        bx.plot(sorted((x_tom, x_seta)), [altura, altura], color='0.15',
                linewidth=0.6, linestyle=(0, (1, 2)), zorder=4)
    # `shrinkA`/`shrinkB` em zero: o padrao recua alguns pontos em cada ponta
    # e a flecha fica sem encostar nas duas linhas que ela liga.
    bx.annotate('', xy=(x_seta, alturas[detectado]),
                xytext=(x_seta, alturas[segundo]),
                arrowprops=dict(arrowstyle='<->', linewidth=0.9, color='0.15',
                                shrinkA=0, shrinkB=0), zorder=5)
    bx.annotate(f"{virgula(margem)} dB",
                xy=(x_seta + 60, (alturas[detectado] + alturas[segundo]) / 2),
                ha='left', va='center', fontsize=8.5)
    bx.set_ylabel('Energia acima do\npróprio piso (dB)')
    bx.set_ylim(float(alturas.min()) - 2.0, float(alturas.max()) + 3.0)
    bx.legend(handles=[
        Line2D([], [], color=CERTO, linewidth=2.6, label='Tom transmitido'),
        Line2D([], [], color=ERRADO, linewidth=2.6,
               label='Tom calado, acima do próprio piso'),
        Line2D([], [], color=NEGATIVO, linewidth=2.6,
               label='Tom calado, abaixo do próprio piso'),
    ], loc='upper left', bbox_to_anchor=(0.0, -0.42), frameon=False, ncols=3,
        handletextpad=0.6, columnspacing=1.2, borderpad=0.0, fontsize=7.5)

    bx.set_xlim(min(MARY_TONES) - 200, max(MARY_TONES) + 200)
    bx.set_xlabel('Frequência dos dezesseis tons (Hz)')
    bx.set_xticks(list(MARY_TONES))
    bx.set_xticklabels([virgula(v, 0) for v in MARY_TONES], fontsize=6.5,
                       rotation=90)
    for eixo in (ax, bx):
        eixo.yaxis.set_major_locator(MultipleLocator(10))
        eixo.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))

    destinos = comum.grava(fig, NOME, args.out)

    bruta = np.argsort(a.energia(k))
    espalha = [float(db(a.piso(j)).max() - db(a.piso(j)).min())
               for j in range(a.simbolos)]

    print("[decisão] " + ", ".join(destinos))
    for linha in comum.cabecalho(a):
        print(linha)
    print(f"    símbolo {k} do quadro, {virgula(a.tempo(k), 3)} s da gravação; "
          f"janela {i0}–{i1}, {i1 - i0} amostras")
    print(f"    transmitido tom {a.tom[k]} ({virgula(MARY_TONES[a.tom[k]], 0)} Hz), "
          f"bits {''.join(str(int(b)) for b in a.bits[k])}; detectado tom "
          f"{detectado} ({virgula(MARY_TONES[detectado], 0)} Hz)")
    print(f"    margem sobre o segundo colocado {virgula(margem)} dB; mediana "
          f"do bloco {virgula(float(np.median(margem_bloco)))} dB "
          f"({virgula(float(np.percentile(margem_bloco, 10)))} a "
          f"{virgula(float(np.percentile(margem_bloco, 90)))} dB entre os decis)")
    print(f"    o tom detectado é também o mais forte em energia bruta neste "
          f"símbolo (tom {int(bruta[-1])}), como pede a escolha do símbolo comum")
    print(f"    piso deste símbolo: {virgula(float(piso.max() - piso.min()))} dB "
          f"entre o tom de piso mais alto e o mais baixo; mediana do bloco "
          f"{virgula(float(np.median(espalha)))} dB")


if __name__ == '__main__':
    main()
