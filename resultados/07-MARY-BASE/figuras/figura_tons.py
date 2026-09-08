"""Figura do artigo: a 16-FSK no ar, um tom por vez.

Espectrograma de 0,3 s de uma gravacao de `resultados/07-MARY-BASE/`, com os
dezesseis tons no eixo de frequencia e, sobre cada simbolo, o tom que o
receptor detectou. Mostra o que a camada faz: em cada simbolo sona exatamente
um dos dezesseis tons, e ele troca a cada 10 ms.

    ./venv/bin/python resultados/07-MARY-BASE/figuras/figura_tons.py [--stem S] [--simbolo K] [--out PNG]

A janela tem o comprimento de um simbolo, que e o minimo para separar tons
distantes 162 Hz, e desliza de um oitavo dele. A FFT e preenchida com zeros
ate 2048 pontos: isso nao cria resolucao nenhuma, so faz a figura sair
continua em vez de um tabuleiro de raias de 100 Hz.

O sinal e desenhado em cinza e em nivel absoluto, relativo ao maximo do
trecho, entao o piso de ruido fica a vista como o cinza de fundo. A cor esta
reservada ao que o receptor fez: o marcador do tom detectado, verde-azul
quando saiu o tom transmitido e vermelho quando nao.
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator
from scipy.signal import spectrogram

import comum
from comum import CERTO, CONTORNO, ERRADO, GRADE, LARGURA, MARY_TONES, virgula

NOME = '16fsk-tons.png'
SIMBOLOS = 30            # 0,3 s
PRIMEIRO = 290
FAIXA = (min(MARY_TONES) - 120.0, max(MARY_TONES) + 120.0)
NFFT = 2048              # so preenchimento com zeros, para a figura sair contínua
ESCALA = 28.0            # dB de cinza abaixo do maximo do trecho


def espectrograma(a, t0, t1):
    """Espectrograma deslizante do trecho, em dB relativos ao maximo dele."""
    passo = a.demod.samples_per_symbol
    f, t, S = spectrogram(a.amostras, fs=a.fs, window='hann',
                          nperseg=passo, noverlap=7 * passo // 8, nfft=NFFT,
                          mode='magnitude')
    corte = (t >= t0 - 0.004) & (t <= t1 + 0.004)
    faixa = (f >= FAIXA[0]) & (f <= FAIXA[1])
    D = 20 * np.log10(np.maximum(S[np.ix_(faixa, corte)], 1e-12))
    return f[faixa], t[corte], D - D.max()


def desenha(fig, ax, a, k0, k1, marcadores=True):
    """O espectrograma, a grade nominal, o eixo dos tons e a barra de escala.

    Comum as duas figuras de espectrograma desta campanha, para que elas nao
    possam divergir em nada que nao seja o que cada uma tem a dizer.
    """
    t0, t1 = a.tempo(k0), a.tempo(k1)
    f, t, D = espectrograma(a, t0, t1)
    # Tempo em milissegundos contados do inicio do trecho: o instante
    # absoluto dentro da gravacao nao diz nada a quem le, e a duracao do
    # simbolo diz tudo.
    ms = (t - t0) * 1000.0

    malha = ax.pcolormesh(ms, f, D, cmap='gray_r', vmin=-ESCALA, vmax=0.0,
                          shading='gouraud', rasterized=True)
    barra = fig.colorbar(malha, ax=ax, pad=0.015, fraction=0.04)
    barra.set_label('Nível relativo ao máximo do trecho (dB)')
    barra.outline.set_linewidth(0.8)

    # Grade de passo constante, no periodo nominal do simbolo. As
    # horizontais vao no meio do caminho entre um tom e o seguinte,
    # delimitando a faixa de cada um em vez de passar por cima do valor.
    for x in (a.bordas_nominais(k0, k1) - t0) * 1000.0:
        ax.axvline(x, color=GRADE, linewidth=0.4, linestyle=(0, (1, 3)),
                   zorder=3)
    for y in comum.faixas_dos_tons():
        ax.axhline(y, color=GRADE, linewidth=0.4, linestyle=(0, (1, 3)),
                   zorder=3)

    if marcadores:
        # O tom que o receptor detectou, sobre o simbolo em que ele decidiu.
        # Forma para o significado, cor para o resultado, contorno claro para
        # sobreviver tanto ao fundo claro quanto ao escuro.
        for k in range(k0, k1):
            centro = (a.tempo(k) + a.tempo(k + 1)) / 2 - t0
            ax.plot([centro * 1000.0], [MARY_TONES[a.recebido(k)]],
                    linestyle='none', marker='o', markersize=6.5,
                    markerfacecolor=a.cor(k), markeredgecolor=CONTORNO,
                    markeredgewidth=1.0, zorder=6)

    ax.set_xlim(0.0, (t1 - t0) * 1000.0)
    ax.set_ylim(*FAIXA)
    ax.set_ylabel('Frequência dos dezesseis tons (Hz)')
    # O eixo e a lista de tons, lida de `modem.MARY_TONES`: uma escala de
    # 500 em 500 Hz obrigaria a medir com regua o que a camada define.
    ax.set_yticks(list(MARY_TONES))
    ax.set_yticklabels([virgula(v, 0) for v in MARY_TONES], fontsize=7)
    ax.xaxis.set_major_locator(MultipleLocator(50))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))
    ax.tick_params(axis='y', length=3.0, width=0.8)
    return f, t, D


def legenda(ax, a, k0, k1, extras=()):
    """Legenda curta, sem moldura, so com o que o eixo nao diz."""
    houve_erro = any(a.recebido(k) != a.tom[k] for k in range(k0, k1))
    itens = [Line2D([], [], linestyle='none', marker='o', markersize=6.5,
                    markerfacecolor=CERTO, markeredgecolor=CONTORNO,
                    label='Tom detectado, igual ao transmitido')]
    if houve_erro:
        itens.append(Line2D([], [], linestyle='none', marker='o',
                            markersize=6.5, markerfacecolor=ERRADO,
                            markeredgecolor=CONTORNO,
                            label='Tom detectado, diferente do transmitido'))
    itens.append(Line2D([], [], color=GRADE, linewidth=0.6,
                        linestyle=(0, (1, 3)),
                        label='Grade de passo nominal do símbolo'))
    itens += list(extras)
    ax.legend(handles=itens, loc='upper left', bbox_to_anchor=(0.0, -0.16),
              frameon=False, ncols=2, handletextpad=0.6, columnspacing=1.6,
              borderpad=0.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stem', default=comum.PADRAO)
    ap.add_argument('--simbolo', type=int, default=PRIMEIRO)
    ap.add_argument('--out', action='append', metavar='PNG')
    args = ap.parse_args()

    a = comum.alinha(args.stem)
    k0, k1 = args.simbolo, args.simbolo + SIMBOLOS

    fig, ax = plt.subplots(figsize=(LARGURA, 3.9), layout='constrained')
    f, t, D = desenha(fig, ax, a, k0, k1)
    ax.set_xlabel('Tempo dentro do trecho (ms)')
    legenda(ax, a, k0, k1)

    destinos = comum.grava(fig, NOME, args.out)

    contraste = D.max(axis=0) - np.median(D, axis=0)
    certos = sum(a.recebido(k) == a.tom[k] for k in range(k0, k1))

    print("[tons] " + ", ".join(destinos))
    for linha in comum.cabecalho(a):
        print(linha)
    print(f"    trecho: símbolos {k0} a {k1} do quadro, "
          f"{virgula(a.tempo(k0), 3)} a {virgula(a.tempo(k1), 3)} s da gravação, "
          f"{virgula(a.tempo(k0) - a.tempo(0), 2)} s depois do início do quadro")
    print(f"    {len(MARY_TONES)} tons de {virgula(min(MARY_TONES), 0)} a "
          f"{virgula(max(MARY_TONES), 0)} Hz, separação "
          f"{virgula(float(np.diff(MARY_TONES).min()), 0)}–"
          f"{virgula(float(np.diff(MARY_TONES).max()), 0)} Hz; símbolo de "
          f"{a.demod.samples_per_symbol} amostras, "
          f"{virgula(1000 / a.meta['baud'], 0)} ms")
    print(f"    janela {a.demod.samples_per_symbol} amostras, salto "
          f"{a.demod.samples_per_symbol // 8}, FFT preenchida até {NFFT}; "
          f"escala de {virgula(ESCALA, 0)} dB abaixo do máximo do trecho")
    print(f"    pico menos mediana da coluna: mediana "
          f"{virgula(float(np.median(contraste)))} dB, mínimo "
          f"{virgula(float(contraste.min()))} dB")
    print(f"    no trecho, {certos} dos {SIMBOLOS} símbolos decididos no tom "
          f"transmitido, e portanto todos os {4 * SIMBOLOS} bits")


if __name__ == '__main__':
    main()
