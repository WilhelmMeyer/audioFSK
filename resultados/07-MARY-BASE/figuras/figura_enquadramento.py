"""Figura do artigo: o enquadramento da 16-FSK sobre a carga.

Espectrograma de 0,3 s sobre o bloco codificado, com o tom detectado marcado
em cada simbolo e, numa faixa acima do quadro, os quatro bits que o
transmissor enviou naquele simbolo.

    ./venv/bin/python resultados/07-MARY-BASE/figuras/figura_enquadramento.py [--stem S] [--simbolo K] [--out PNG]

A faixa de bits e dividida pelas fronteiras que o receptor de fato usou; a
grade sobre o espectrograma e de passo constante, no periodo nominal do
simbolo. Onde as duas se afastam esta o que a porta early/late corrigiu, e
esse afastamento e o que a figura tem a dizer que a figura dos tons nao diz.

Os bits anotados sao os TRANSMITIDOS. Vem do `payload_hex` da gravacao pelo
mesmo caminho do transmissor, em `fec.py`: convolucional, repeticao,
entrelacamento, com a palavra de referencia de 31 bits na frente. Nao sao os
decodificados do audio. A figura mostra o que foi enviado; o recebido
coincidir e o resultado, e nao pode ser a fonte do desenho. Por isso
`comum.alinha` so devolve um alinhamento depois que o bloco decodifica de
volta a carga gravada.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import comum
from comum import CERTO, GRADE, LARGURA, virgula
from figura_tons import desenha, legenda

NOME = '16fsk-enquadramento.png'
SIMBOLOS = 30            # 0,3 s
PRIMEIRO = 290


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stem', default=comum.PADRAO)
    ap.add_argument('--simbolo', type=int, default=PRIMEIRO)
    ap.add_argument('--out', action='append', metavar='PNG')
    args = ap.parse_args()

    a = comum.alinha(args.stem)
    k0, k1 = args.simbolo, args.simbolo + SIMBOLOS
    t0, t1 = a.tempo(k0), a.tempo(k1)
    medidas = np.array([a.tempo(k) for k in range(k0, k1 + 1)])
    nominais = a.bordas_nominais(k0, k1)

    # A faixa de rotulos vai em cima e e um eixo proprio: e ali, fora dos
    # dados, que entram os bits. Tinta sobre o cinza do espectrograma se
    # somaria a ele e viraria uma terceira cor, que nao quer dizer nada.
    fig, (bx, ax) = plt.subplots(2, 1, figsize=(LARGURA, 4.6),
                                 height_ratios=(1.0, 3.6), layout='constrained')
    desenha(fig, ax, a, k0, k1)
    ax.set_xlabel('Tempo dentro do trecho (ms)')
    legenda(ax, a, k0, k1, extras=[
        Line2D([], [], color=CERTO, linewidth=0.8,
               label='Fronteira de símbolo do receptor')])

    # Cada celula da faixa e um simbolo, e suas divisorias sao as fronteiras
    # medidas.
    for x in (medidas - t0) * 1000.0:
        bx.axvline(x, color=CERTO, linewidth=0.8)
    for k in range(k0, k1):
        centro = ((a.tempo(k) + a.tempo(k + 1)) / 2 - t0) * 1000.0
        for j, b in enumerate(a.bits[k]):
            bx.text(centro, 3 - j, str(int(b)), ha='center', va='center',
                    fontsize=6.5, color='0.15')
    bx.set_ylim(-0.8, 3.8)
    bx.set_xlim(0.0, (t1 - t0) * 1000.0)
    bx.set_yticks([])
    bx.set_xticks([])
    bx.set_ylabel('Bits\nenviados', rotation=0, ha='right', va='center',
                  labelpad=8)
    for lado in ('top', 'right', 'left'):
        bx.spines[lado].set_visible(False)
    bx.spines['bottom'].set_color(GRADE)
    # A faixa tem de ficar exatamente sobre o espectrograma, e o painel de
    # baixo perde largura para a barra de escala. Sem isto os bits saem
    # deslocados dos simbolos que rotulam.
    fig.canvas.draw()
    caixa = ax.get_position()
    alta = bx.get_position()
    bx.set_position([caixa.x0, alta.y0, caixa.width, alta.height])

    destinos = comum.grava(fig, NOME, args.out)

    larguras = np.diff([a.demod.janelas[a.simbolo0 + k] for k in range(k0, k1 + 1)])
    desvio = 1000 * np.abs(medidas - nominais)
    certos = sum(a.recebido(k) == a.tom[k] for k in range(k0, k1))
    palavra = ''.join(str(int(b)) for k in range(k0, k1) for b in a.bits[k])

    print("[enquadramento] " + ", ".join(destinos))
    for linha in comum.cabecalho(a):
        print(linha)
    print(f"    trecho: símbolos {k0} a {k1} do quadro, "
          f"{virgula(t0, 3)} a {virgula(t1, 3)} s da gravação, "
          f"{virgula(t0 - a.tempo(0), 2)} s depois do início do quadro, "
          f"{virgula(t1 - t0, 3)} s de duração")
    print(f"    símbolo nominal {a.demod.samples_per_symbol} amostras; no trecho "
          f"o receptor consumiu de {int(larguras.min())} a {int(larguras.max())}, "
          f"mediana {virgula(float(np.median(larguras)), 0)}; guarda descartada "
          f"{a.demod.guard} amostras ({virgula(1000 * a.demod.guard / a.fs, 1)} ms)")
    print(f"    fronteira medida contra grade nominal: afastamento máximo "
          f"{virgula(float(desvio.max()), 2)} ms, mediana "
          f"{virgula(float(np.median(desvio)), 2)} ms")
    print(f"    bits enviados no trecho, em ordem de fluxo: {palavra}")
    print(f"    {certos} dos {SIMBOLOS} símbolos foram decididos no tom "
          f"transmitido, e portanto todos os {4 * SIMBOLOS} bits do trecho; "
          f"no quadro inteiro, {virgula(100 * a.acertos())}% dos símbolos e "
          f"{virgula(100 * a.bits_certos())}% dos bits")


if __name__ == '__main__':
    main()
