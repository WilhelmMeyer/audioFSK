"""Figuras do artigo, geradas a partir dos dados medidos na bancada.

Tres figuras, PNG 300 dpi, largura de uma coluna de A4 (~16 cm), seguras em
escala de cinza: nada e codificado so por cor, sempre por marcador e traco.
Sem titulo dentro da figura -- a legenda vai embaixo, no texto.

    ./venv/bin/python artigo/figuras.py

A) artigo/figuras/resposta-canal.png
   Resposta de frequencia medida por varredura (300-6000 Hz), sentido A->B,
   com os 16 tons do 16-FSK marcados. A grandeza do eixo vertical e o
   *nivel relativo ao melhor ponto da varredura*, em dB -- nao e dBFS e nao
   e SNR. E a coluna `nivel` de `channel.py`, 20*log10(sig/pico), que e a
   unica que o HEADER de 03-CH-CHIRP-A2B autoriza a ler como a forma do
   canal: "a forma relativa do pente e o que esta varredura mede bem".

B) artigo/figuras/nivel-alto-falante.png
   Acuracia de bits e blocos inteiros contra o volume do alto-falante da
   maquina transmissora (A->B, ganho digital fixo em 0,5, 3 gravacoes por
   ponto). Valores de `resultados/17-SPK-LEVEL-A2B/`, transcritos aqui.

C) artigo/figuras/bancada.png
   Esquema da bancada: as duas maquinas, o alto-falante de ensaio ligado a
   que transmite, o microfone interno da que recebe, o caminho acustico
   entre eles e o cabo serial. Nao ha dado medido nesta figura, so o
   arranjo. O cabo serial e tracejado de proposito: ele so sincroniza o
   ensaio, e os bytes pontuados viajam apenas pelo ar.
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import (Arc, Circle, FancyArrowPatch, Patch, Polygon,
                                Rectangle)
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# Os tons vem do codigo que os transmite, nunca transcritos a mao.
from modem import MARY_TONES

SAIDA = os.path.join(RAIZ, 'artigo', 'figuras')
MAPA = os.path.join(RAIZ, 'resultados', '03-CH-CHIRP-A2B', 'figuras',
                    'mapa-frequencia-bins76.txt')

BANDA = (550, 3500)          # faixa util medida
LARGURA = 6.3                # polegadas ~ 16 cm

plt.rcParams.update({
    'font.size': 9,
    'axes.titlesize': 9,
    'axes.labelsize': 9.5,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8,
    'axes.linewidth': 0.8,
    'savefig.dpi': 300,
    'figure.dpi': 300,
})


def virgula(v, casas=0):
    return f"{v:.{casas}f}".replace('.', ',')


def le_mapa(caminho, esperado=76):
    """As linhas de bin do mapa: `freq | nivel | snr | barra`.

    O arquivo tem cabecalho e, no fim, um bloco "melhores faixas" com linhas
    do tipo `4388 Hz  60.8 dB`. Um parser que so procure numeros engole esse
    rodape como se fossem bins, e em silencio. So valem linhas com tres
    campos numericos separados por barra vertical.
    """
    freqs, niveis, snrs = [], [], []
    with open(caminho, encoding='utf-8', errors='replace') as fh:
        for linha in fh:
            partes = [p.strip() for p in linha.split('|')]
            if len(partes) < 4:
                continue
            try:
                f, nivel, snr = (float(partes[0]), float(partes[1]),
                                 float(partes[2]))
            except ValueError:
                continue
            freqs.append(f)
            niveis.append(nivel)
            snrs.append(snr)
    if len(freqs) != esperado:
        raise SystemExit(f"[figuras] {caminho}: li {len(freqs)} bins, "
                         f"esperava {esperado}")
    return np.array(freqs), np.array(niveis), np.array(snrs)


def figura_a():
    f, nivel, _snr = le_mapa(MAPA)

    fig, ax = plt.subplots(figsize=(LARGURA, 3.4), layout='constrained')

    ax.axvspan(*BANDA, color='0.85', zorder=0)

    ax.plot(f, nivel, color='black', linewidth=1.0, marker='o',
            markersize=2.6, markerfacecolor='white', markeredgewidth=0.7,
            zorder=3)

    # Os 16 tons como tracos curtos no rodape: 16 linhas de altura inteira
    # tapariam a curva que a figura existe para mostrar.
    lo, hi = nivel.min() - 3.5, 2.0
    base = lo + 0.06 * (hi - lo)
    ax.vlines(MARY_TONES, lo, base, color='black', linewidth=1.1, zorder=4)

    ax.set_xlim(250, 6050)
    ax.set_ylim(lo, hi)
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel('Nível relativo ao melhor ponto (dB)')
    ax.grid(True, which='major', color='0.9', linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)

    ax.legend(handles=[
        Line2D([], [], color='black', linewidth=1.0, marker='o',
               markersize=2.6, markerfacecolor='white',
               label='Resposta medida (varredura 300–6000 Hz)'),
        Line2D([], [], color='black', linewidth=1.1, linestyle='-',
               label='16 tons do 16-FSK (888–3325 Hz)'),
        Patch(facecolor='0.85', edgecolor='none',
              label=f'Faixa útil {BANDA[0]}–{BANDA[1]} Hz'),
    ], loc='upper right', framealpha=0.95, borderpad=0.5)

    destino = os.path.join(SAIDA, 'resposta-canal.png')
    fig.savefig(destino)
    plt.close(fig)

    d = np.abs(np.diff(nivel))
    dentro = (f >= BANDA[0]) & (f <= BANDA[1])
    print(f"[A] {destino}")
    print(f"    {len(f)} bins de {f[0]:.0f} a {f[-1]:.0f} Hz "
          f"(largura {f[1] - f[0]:.0f} Hz)")
    print(f"    nivel: {nivel.min():.1f} a {nivel.max():.1f} dB; "
          f"maior salto entre vizinhos {d.max():.1f} dB")
    print(f"    na faixa util: {nivel[dentro].min():.1f} a "
          f"{nivel[dentro].max():.1f} dB, "
          f"maior salto {np.abs(np.diff(nivel[dentro])).max():.1f} dB")


# resultados/17-SPK-LEVEL-A2B: A->B, ganho digital 0,5, 3 gravacoes por ponto.
VOLUMES = (0.10, 0.20, 0.45, 1.00)
BITS = {
    0.10: (80.93, 72.52, 86.51),
    0.20: (87.26, 85.35, 85.76),
    0.45: (83.18, 85.68, 80.77),
    1.00: (81.85, 77.60, 80.35),
}
MEDIA = {0.10: 79.99, 0.20: 86.12, 0.45: 83.21, 1.00: 79.93}
BLOCOS = {0.10: 1, 0.20: 2, 0.45: 0, 1.00: 0}
TOTAL_BLOCOS = 3


def figura_b():
    x = np.arange(len(VOLUMES))          # posicoes categoricas: o eixo nao e
                                          # linear e nao finge ser
    fig, ax = plt.subplots(figsize=(LARGURA, 3.6), layout='constrained')
    ax2 = ax.twinx()

    ax2.bar(x, [BLOCOS[v] for v in VOLUMES], width=0.5, color='0.87',
            edgecolor='black', linewidth=0.7, zorder=1)

    for i, v in enumerate(VOLUMES):
        ax.plot([i] * 3, BITS[v], linestyle='none', marker='o',
                markersize=5, markerfacecolor='white', markeredgecolor='black',
                markeredgewidth=0.9, zorder=3)
    ax.plot(x, [MEDIA[v] for v in VOLUMES], color='black', linewidth=1.4,
            marker='s', markersize=6, markerfacecolor='black', zorder=4)

    # O twinx desenha as barras por cima da serie principal; sem esta troca
    # de zorder a curva some atras delas, sem erro nenhum.
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)

    ax.set_xticks(x)
    ax.set_xticklabels([virgula(v, 2) for v in VOLUMES])
    ax.set_xlim(-0.5, len(VOLUMES) - 0.5)
    ax.set_xlabel('Volume do alto-falante da máquina transmissora '
                  '(escala não linear)')
    ax.set_ylabel('Acurácia de bits (%)')
    ax.set_ylim(70, 90)
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v)))
    ax.grid(True, axis='y', color='0.9', linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

    ax2.set_ylabel(f'Blocos inteiros (de {TOTAL_BLOCOS})')
    ax2.set_ylim(0, 3.2)
    ax2.set_yticks([0, 1, 2, 3])

    ax.legend(handles=[
        Line2D([], [], color='black', linewidth=1.4, marker='s',
               markersize=6, label='Acurácia de bits, média de 3 gravações'),
        Line2D([], [], linestyle='none', marker='o', markersize=5,
               markerfacecolor='white', markeredgecolor='black',
               label='Gravações individuais'),
        Patch(facecolor='0.87', edgecolor='black', linewidth=0.7,
              label=f'Blocos inteiros (eixo à direita)'),
    ], loc='lower right', framealpha=0.95, borderpad=0.5)

    destino = os.path.join(SAIDA, 'nivel-alto-falante.png')
    fig.savefig(destino)
    plt.close(fig)
    print(f"[B] {destino}")
    for v in VOLUMES:
        print(f"    volume {virgula(v, 2)}: media {virgula(MEDIA[v], 2)}%, "
              f"dispersao {max(BITS[v]) - min(BITS[v]):.2f} pontos, "
              f"{BLOCOS[v]} de {TOTAL_BLOCOS} blocos")


# Bancada: A transmite, B recebe. O sentido segue a figura B e as campanhas
# *-A2B, e trocar o sentido aqui poria as duas figuras em contradicao.
BANCADA = {
    'altura': 3.1,               # polegadas; aspecto igual, 1 unidade = 1 pol
    'tela': (1.30, 1.20),        # largura e altura da tela de cada notebook
    'base': (1.54, 0.16),        # a parte de baixo, mais larga que a tela
    'x_a': 1.05,                 # centro do notebook esquerdo
    'x_b': 5.25,                 # centro do notebook direito
    'y_base': 0.75,              # onde a base apoia
    'y_ar': 1.45,                # altura do caminho acustico
}


def notebook(ax, xc, y_base, rotulo):
    """Um notebook de bloco: base larga, tela em cima, area util dentro dela.

    Devolve os limites da tela, porque o marcador do microfone e o rotulo
    da maquina se posicionam a partir dela, nunca por numero solto.
    """
    lt, ht = BANCADA['tela']
    lb, hb = BANCADA['base']
    ax.add_patch(Rectangle((xc - lb / 2, y_base), lb, hb,
                           facecolor='0.90', edgecolor='black', linewidth=1.0))
    x0, y0 = xc - lt / 2, y_base + hb
    ax.add_patch(Rectangle((x0, y0), lt, ht,
                           facecolor='white', edgecolor='black',
                           linewidth=1.0))
    ax.add_patch(Rectangle((x0 + 0.10, y0 + 0.10), lt - 0.20, ht - 0.20,
                           facecolor='0.94', edgecolor='0.55', linewidth=0.6))
    ax.text(xc, y0 + ht + 0.30, rotulo, ha='center', va='center',
            fontsize=10, fontweight='bold')
    return x0, y0, lt, ht


def alto_falante(ax, x0, yc):
    """Caixa mais cone, apontando para a direita. Devolve a boca do cone."""
    corpo_l, corpo_h, cone_l = 0.22, 0.40, 0.26
    ax.add_patch(Rectangle((x0, yc - corpo_h / 2), corpo_l, corpo_h,
                           facecolor='0.90', edgecolor='black', linewidth=1.0))
    boca = x0 + corpo_l + cone_l
    ax.add_patch(Polygon([(x0 + corpo_l, yc - corpo_h / 2),
                          (x0 + corpo_l, yc + corpo_h / 2),
                          (boca, yc + 0.37),
                          (boca, yc - 0.37)],
                         closed=True, facecolor='0.96', edgecolor='black',
                         linewidth=1.0))
    return boca


def figura_c():
    h = BANCADA['altura']
    y_base, y_ar = BANCADA['y_base'], BANCADA['y_ar']

    fig, ax = plt.subplots(figsize=(LARGURA, h))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, LARGURA)
    ax.set_ylim(0, h)
    ax.set_aspect('equal')
    ax.set_axis_off()

    xa, xb = BANCADA['x_a'], BANCADA['x_b']
    _, _, lt, ht = notebook(ax, xa, y_base, 'Máquina A')
    xb0, yb0, _, _ = notebook(ax, xb, y_base, 'Máquina B')

    # Alto-falante de ensaio, ligado a maquina que transmite por um cabo curto.
    boca = alto_falante(ax, 2.10, y_ar)
    ax.add_patch(FancyArrowPatch((xa + BANCADA['base'][0] / 2, y_base + 0.08),
                                 (2.10, y_ar - 0.10), arrowstyle='-',
                                 connectionstyle='arc3,rad=-0.35',
                                 linewidth=1.0, color='black'))
    ax.text(2.48, y_ar + 0.62, 'alto-falante de ensaio', ha='center',
            va='center', fontsize=8.5)

    # O ar: frentes de onda saindo da boca do cone e uma seta ate o microfone.
    for r in (0.40, 0.60, 0.80):
        ax.add_patch(Arc((boca, y_ar), 2 * r, 2 * r, theta1=-32, theta2=32,
                         linewidth=0.9, color='black'))
    x_mic, y_mic = xb0 + 0.16, yb0 + ht - 0.05
    ax.annotate('', xy=(x_mic - 0.02, y_mic - 0.11), xytext=(3.45, y_ar),
                arrowprops=dict(arrowstyle='-|>', linewidth=1.0, color='black',
                                shrinkA=0, shrinkB=2, mutation_scale=11))
    ax.text(3.40, y_ar - 0.50, 'caminho acústico (ar)', ha='center',
            va='center', fontsize=8.5)
    ax.text(3.40, y_ar - 0.67, '(bytes pontuados)', ha='center', va='center',
            fontsize=8.5)

    # Microfone interno: um marcador pequeno na moldura da tela receptora.
    ax.add_patch(Circle((x_mic, y_mic), 0.045, facecolor='black',
                        edgecolor='black', linewidth=0.8))
    ax.annotate('microfone interno', xy=(x_mic + 0.02, y_mic + 0.06),
                xytext=(4.45, y_mic + 0.26), ha='right', va='center',
                fontsize=8.5,
                arrowprops=dict(arrowstyle='-', linewidth=0.7, color='black',
                                shrinkA=2, shrinkB=1))

    # Cabo serial: tracejado, e a legenda diz que nao carrega dados.
    y_cabo = 0.42
    ax.plot([xa, xa, xb, xb], [y_base, y_cabo, y_cabo, y_base],
            linestyle=(0, (4, 3)), linewidth=1.1, color='black',
            solid_capstyle='butt')
    ax.text((xa + xb) / 2, y_cabo - 0.22, 'cabo serial (só controle)',
            ha='center', va='center', fontsize=8.5)

    ax.text(LARGURA / 2, h - 0.25, 'Ambas as máquinas amostram a 48 kHz',
            ha='center', va='center', fontsize=9)

    destino = os.path.join(SAIDA, 'bancada.png')
    fig.savefig(destino)
    plt.close(fig)
    print(f"[C] {destino}")
    print(f"    esquema {LARGURA * 2.54:.1f} x {h * 2.54:.1f} cm, "
          f"A transmite pelo alto-falante e B recebe pelo microfone interno")
    print(f"    caminho pontuado: so o ar; cabo serial tracejado, so controle")


def main():
    os.makedirs(SAIDA, exist_ok=True)
    figura_a()
    figura_b()
    figura_c()


if __name__ == '__main__':
    main()
