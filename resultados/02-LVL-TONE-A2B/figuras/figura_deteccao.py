"""Figura do artigo: o que o detector vê num tom e no silêncio.

Uma pergunta só: quanto separa um tom presente de um tom ausente, medido com
a mesma janela e as mesmas sondas que o demodulador de 16-FSK usa para
decidir um símbolo. PNG 300 dpi, largura de coluna, seguro em escala de
cinza.

    ./venv/bin/python resultados/02-LVL-TONE-A2B/figuras/figura_deteccao.py

A janela nao e escolhida aqui: vem do proprio `MaryDemodulator`, instanciado
com os parametros de operacao. A 100 baud e 48 kHz o simbolo tem 480
amostras, das quais as primeiras 15% sao guarda descartada, entao a decisao
sai de 408 amostras, 8,5 ms, cerca de 118 Hz de resolucao. As sondas sao as
exponenciais complexas de `MaryDemodulator.probe`, uma por tom, e a figura
mostra exatamente o vetor de energias que o detector compara, um valor por
tom.

Duas condicoes, as duas gravadas nesta bancada, sentido A->B:

  com tom    `resultados/02-LVL-TONE-A2B/`, 1700 Hz continuo, que e o tom 6
             dos dezesseis (a 16-FSK usa 1700 Hz exato).
  sem tom    `resultados/01-LVL-BASE-A2B/`, o enlace inteiramente parado.

E uma terceira serie que nao e gravacao nenhuma: um seno de 1700 Hz
sintetizado aqui, na amplitude que a gravacao mediu no proprio tom, sondado
pela mesma janela. Sem sala, sem alto-falante e sem microfone, ele reproduz
as sondas vizinhas e distantes da gravacao. Isso responde por que as outras
frequencias sobem quando o tom entra: e o vazamento espectral da janela
retangular de 408 amostras, o mesmo sinc que qualquer seno fora do centro de
um bin produz, e nao sensibilidade do microfone nem ruido novo na sala.

A leitura e a distancia entre as duas curvas no tom transmitido, contra o
1,3 dB que a regra de decisao exige (contraste 0,15 entre o vencedor e o
segundo colocado, que e uma razao de energia de 1,35).
"""

import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np


def raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[detecção] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import recording
from modem import MaryDemodulator, MARY_TONES

COM = os.path.join(RAIZ, 'resultados', '02-LVL-TONE-A2B', 'gravacao',
                   '20260903-175101-lvl-tone-A2B.wav')
SEM = os.path.join(RAIZ, 'resultados', '01-LVL-BASE-A2B', 'gravacao')
TOM = 1700.0
JANELAS = 100            # simbolos consecutivos, tomados no meio da gravacao
LARGURA = 6.3

# Paleta: teal escuro para a serie principal, azul gelo para o que e fundo ou
# dispersao. Escolha do autor. A figura continua legivel em escala de cinza
# porque nada e codificado so por cor: cada serie tem marcador e traco
# proprios, e a cor apenas reforca.
TEAL = '#0F5257'
TEAL_MED = '#2E7D82'
GELO = '#BFDDE4'
GELO_CLARO = '#E8F2F5'


# Dois destinos e uma geracao so. O PNG do artigo e o mesmo arquivo que
# fica aqui ao lado dos dados: a pasta do artigo carrega apenas figuras, e
# o que as gera mora junto da campanha que elas medem.
SAIDAS = (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deteccao-tom.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'deteccao-tom.png'))

plt.rcParams.update({
    'font.size': 9,
    'axes.labelsize': 9.5,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8,
    'axes.linewidth': 0.8,
    'savefig.dpi': 300,
    'figure.dpi': 300,
})


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


def sondagem(demod, samples, janelas=JANELAS):
    """O vetor de energias do detector, em dBFS, mediana de N símbolos.

    Mediana e nao media: uma batida na mesa dentro de uma janela levaria a
    media junto, e o que a figura afirma e o que o detector ve tipicamente.
    """
    nwin = demod.samples_per_tone - demod.guard
    passo = demod.samples_per_symbol
    inicio = max(0, len(samples) // 2 - janelas * passo // 2)
    linhas = []
    for k in range(janelas):
        seg = samples[inicio + k * passo:inicio + k * passo + nwin]
        if len(seg) < nwin:
            break
        # 2|X|/N devolve a amplitude da senoide, entao o eixo e o mesmo dBFS
        # do resto do projeto e um tom de amplitude 1 leria 0 dB.
        linhas.append(np.abs(demod.probe @ seg) * 2 / nwin)
    if not linhas:
        raise SystemExit("[detecção] gravacao curta demais para uma janela")
    return 20 * np.log10(np.maximum(np.median(np.array(linhas), axis=0), 1e-12)), len(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--com', default=COM, help="gravacao com o tom")
    ap.add_argument('--sem', default=SEM, help="pasta das gravacoes de sala")
    ap.add_argument('--out', action='append', metavar='PNG',
                    help="onde gravar; repetivel. Sem ele, grava nos dois "
                         "destinos padrao (esta pasta e artigo/figuras)")
    args = ap.parse_args()

    demod = MaryDemodulator(fs=recording.FS, baud=100)
    nwin = demod.samples_per_tone - demod.guard
    res = recording.FS / nwin

    com, n_com = sondagem(demod, recording.read(args.com))
    silencios = sorted(glob.glob(os.path.join(args.sem, '*.wav')))
    if not silencios:
        raise SystemExit(f"[detecção] nenhuma gravacao de sala em {args.sem}")
    sem_cada = [sondagem(demod, recording.read(p))[0] for p in silencios]
    sem = np.median(np.array(sem_cada), axis=0)

    tons = np.array(MARY_TONES, dtype=float)
    i_tom = int(np.argmin(np.abs(tons - TOM)))

    # O seno puro, na amplitude que a propria gravacao mediu no tom, para que
    # as duas series se encostem em 1700 Hz e a comparacao seja das *saias*.
    n = np.arange(int(2.0 * recording.FS))
    puro = (10 ** (com[i_tom] / 20)) * np.sin(2 * np.pi * TOM * n / recording.FS)
    sim, _ = sondagem(demod, puro)
    margem = com[i_tom] - sem[i_tom]
    ordem = np.argsort(com)
    i_seg = int(ordem[-2])
    vantagem = com[i_tom] - com[i_seg]
    # A regra de decisao, tirada do proprio detector: contraste minimo entre o
    # vencedor e o segundo, que e uma razao de energia e portanto um numero de
    # decibeis.
    c = demod.contrast_min
    limiar_db = 10 * np.log10((1 + c) / (1 - c))

    fig, ax = plt.subplots(figsize=(LARGURA, 3.6), layout='constrained')

    ax.plot(tons, com, color=TEAL, linewidth=1.2, marker='o', markersize=5,
            markerfacecolor=TEAL, zorder=4)
    ax.plot(tons, sim, color=TEAL_MED, linewidth=1.0, linestyle=(0, (1, 2)),
            marker='^', markersize=5, markerfacecolor='white',
            markeredgecolor=TEAL_MED, zorder=5)
    ax.plot(tons, sem, color='#4C6B77', linewidth=1.0, linestyle=(0, (4, 3)),
            marker='s', markersize=5, markerfacecolor=GELO,
            markeredgecolor='#4C6B77', zorder=3)

    # A margem no tom transmitido, desenhada como a distancia que e.
    ax.annotate('', xy=(tons[i_tom], com[i_tom]), xytext=(tons[i_tom], sem[i_tom]),
                arrowprops=dict(arrowstyle='<->', linewidth=1.0, color=TEAL,
                                shrinkA=3, shrinkB=3))
    ax.annotate(f"{virgula(margem)} dB entre\ntom e não tom",
                xy=(tons[i_tom], (com[i_tom] + sem[i_tom]) / 2),
                xytext=(tons[1], (com[i_tom] + sem[i_tom]) / 2 + 9),
                ha='center', va='center', fontsize=8.5,
                arrowprops=dict(arrowstyle='-', linewidth=0.7, color=TEAL,
                                shrinkA=2, shrinkB=6),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='none', alpha=0.9))

    # E a distancia que a decisao de fato usa: vencedor contra segundo. As
    # duas guias horizontais existem porque a flecha, sozinha, media contra
    # nada visivel: ela liga dois niveis que estao em tons diferentes.
    for nivel in (com[i_tom], com[i_seg]):
        ax.hlines(nivel, tons[i_tom], tons[i_seg] + 60, color=TEAL_MED,
                  linewidth=0.7, linestyle=(0, (2, 2)), zorder=2)
    ax.annotate('', xy=(tons[i_seg], com[i_tom]), xytext=(tons[i_seg], com[i_seg]),
                arrowprops=dict(arrowstyle='<->', linewidth=1.0, color=TEAL_MED,
                                shrinkA=2, shrinkB=2))
    ax.annotate(f"{virgula(vantagem)} dB sobre o segundo tom mais alto,\n"
                f"contra {virgula(limiar_db)} dB exigidos pela decisão",
                xy=(tons[i_seg], (com[i_tom] + com[i_seg]) / 2),
                xytext=(tons[-4], com[i_tom] - 1.5),
                ha='center', va='center', fontsize=8.5,
                arrowprops=dict(arrowstyle='-', linewidth=0.7, color=TEAL_MED,
                                shrinkA=2, shrinkB=6),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='none', alpha=0.9))

    ax.set_xlim(tons[0] - 120, tons[-1] + 120)
    ax.set_xlabel('Frequência dos 16 tons da 16-FSK (Hz)')
    ax.set_ylabel('Nível na janela de decisão (dBFS)')
    ax.xaxis.set_major_locator(MultipleLocator(500))
    ax.yaxis.set_major_locator(MultipleLocator(10))
    for eixo in (ax.xaxis, ax.yaxis):
        eixo.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))
    ax.grid(True, color='0.9', linewidth=0.5)
    ax.set_axisbelow(True)

    ax.legend(handles=[
        Line2D([], [], color=TEAL, linewidth=1.2, marker='o', markersize=5,
               markerfacecolor=TEAL, label=f'Com tom de {virgula(TOM, 0)} Hz'),
        Line2D([], [], color=TEAL_MED, linewidth=1.0, linestyle=(0, (1, 2)),
               marker='^', markersize=5, markerfacecolor='white',
               markeredgecolor=TEAL_MED,
               label='Seno puro simulado, mesma janela'),
        Line2D([], [], color='#4C6B77', linewidth=1.0, linestyle=(0, (4, 3)),
               marker='s', markersize=5, markerfacecolor=GELO,
               markeredgecolor='#4C6B77',
               label=f'Sala parada, mediana de {len(sem_cada)} gravações'),
    ], loc='lower left', framealpha=0.95, borderpad=0.5)

    for destino in (args.out or SAIDAS):
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        fig.savefig(destino)
    plt.close(fig)

    print("[detecção] " + ", ".join(args.out or SAIDAS))
    print(f"    janela do detector: {nwin} amostras "
          f"({virgula(1000 * nwin / recording.FS)} ms, {virgula(res)} Hz por bin), "
          f"guarda de {demod.guard} amostras descartada de {demod.samples_per_symbol}")
    print(f"    {n_com} janelas no meio de {os.path.basename(args.com)}; "
          f"sala: mediana de {len(sem_cada)} gravações")
    print(f"    tom de {virgula(tons[i_tom], 0)} Hz: com {virgula(com[i_tom])} dBFS, "
          f"sem {virgula(sem[i_tom])} dBFS, margem {virgula(margem)} dB")
    print(f"    segundo tom mais alto com o tom no ar: "
          f"{virgula(tons[i_seg], 0)} Hz a {virgula(com[i_seg])} dBFS "
          f"({virgula(vantagem)} dB abaixo do vencedor)")
    print(f"    (o segundo tom mais alto recebe a saia do próprio tom vencedor na "
          f"janela retangular de {nwin} amostras, e não outro tom transmitido)")
    print(f"    decisão: contraste mínimo {virgula(c, 2)} = "
          f"{virgula(limiar_db)} dB entre vencedor e segundo")
    dif = np.abs(com - sim)
    fora = [i for i in range(len(tons)) if i != i_tom]
    print(f"    seno puro simulado na mesma janela: reproduz a gravação dentro "
          f"de {virgula(float(dif[fora].max()))} dB em todos os tons "
          f"(mediana {virgula(float(np.median(dif[fora])))} dB)")
    pior = int(np.argmax(dif))
    print(f"      maior desvio em {virgula(tons[pior], 0)} Hz: gravação "
          f"{virgula(com[pior])} dBFS contra {virgula(sim[pior])} simulado")
    print("    por tom: com tom, seno simulado, sala, margem (com - sala), dB:")
    for f, a, s, b in zip(tons, com, sim, sem):
        print(f"      {virgula(f, 0):>6} Hz  {virgula(a):>7}  {virgula(s):>7}  "
              f"{virgula(b):>7}  {virgula(a - b):>6}")


if __name__ == '__main__':
    main()
