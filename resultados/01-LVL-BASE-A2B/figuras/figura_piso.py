"""Figura do artigo: piso de ruido do microfone receptor, nada tocando.

Espectro medio das gravacoes de `resultados/01-LVL-BASE-A2B/gravacao/`, que
sao 8 s cada do microfone de B com o enlace inteiramente parado. PNG 300 dpi,
largura de uma coluna, seguro em escala de cinza: nada codificado so por cor,
sempre por marcador ou traco. Sem titulo dentro da figura, a legenda e do
texto.

    ./venv/bin/python resultados/01-LVL-BASE-A2B/figuras/figura_piso.py [--dir <campanha>] [--out <png>]

O eixo vertical e dBFS, o mesmo do HEADER daquela campanha, e a curva e lida
com o `band_rms` do `ruido.py` -- a mesma funcao que produziu os numeros do
HEADER -- em janelas de 50 Hz. A janela de 50 Hz nao e cosmetica: o piso no
tom de 1700 Hz, que e a referencia do teste 02, e medido em +-25 Hz, entao a
janela e exatamente essa e o ponto marcado cai sobre a curva em vez de ser
uma segunda medida ao lado dela.

Nenhum numero e transcrito: tudo e lido das gravacoes.
"""

import argparse
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np

def raiz():
    """A raiz do repositorio, achada subindo ate encontrar `modem.py`.

    Nao e `dirname(dirname(__file__))`: isso fixaria a profundidade em que
    este arquivo mora, e quem o mover uma pasta para o lado o quebra sem
    aviso, com um ImportError que parece falta de dependencia.
    """
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[piso] nao achei a raiz do repositorio a partir deste arquivo")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import recording
# Os tons e a janela de decisao vem do codigo que transmite e decide, nunca
# transcritos a mao.
from modem import MARY_TONES, MaryDemodulator
from ruido import band_rms, dbfs

# 550-3500 Hz, a faixa util do CLAUDE.md da raiz e da figura da resposta do
# canal. O HEADER de 01-LVL-BASE-A2B rotula a dele 550-3600 Hz; as duas
# medianas coincidem em 0,1 dB porque entre 3500 e 3600 Hz nao ha nada acima
# de -90 dBFS, entao a escolha e de coerencia entre figuras, nao de numero.
BANDA = (550, 3500)
TOM = 1700.0            # tom de referencia do teste 02
LARGURA_BIN = 50.0      # = 2 x os +-25 Hz com que o piso no tom e medido
FMAX = 6000.0
LARGURA = 6.3           # polegadas ~ 16 cm, uma coluna

# Dois destinos e uma geracao so. O PNG do artigo e o mesmo arquivo que
# fica aqui ao lado dos dados: a pasta do artigo carrega apenas figuras, e
# o que as gera mora junto da campanha que elas medem.
SAIDAS = (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'piso-ruido.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'piso-ruido.png'))

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


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


def gravacoes(pasta):
    """Os pares WAV+JSON da campanha, em ordem de nome, com o audio todo.

    Prefere o `.wav` e cai no `.flac` pelo `recording.audio_path`, porque um
    clone do repositorio carrega o FLAC e nao o WAV.
    """
    import json
    from pathlib import Path
    saida = []
    for js in sorted(Path(pasta).glob('*.json')):
        meta = json.loads(js.read_text())
        # Uma gravacao com carga nao e piso de sala. Ler uma como se fosse
        # poria um sinal transmitido dentro da media do ruido, e a figura
        # nao teria como avisar.
        if meta.get('payload_len'):
            raise SystemExit(f"[piso] {js.name} tem carga ({meta['payload_len']} B), "
                             f"nao e gravacao de sala")
        saida.append((js.stem, recording.read(recording.audio_path(js.with_suffix('')))))
    if not saida:
        raise SystemExit(f"[piso] nenhuma gravacao em {pasta}")
    return saida


def espectro(samples, bordas):
    """Rms em cada janela de frequencia, pelo mesmo `band_rms` do HEADER."""
    return np.array([band_rms(samples, lo, hi)
                     for lo, hi in zip(bordas[:-1], bordas[1:])])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default=os.path.join(
        RAIZ, 'resultados', '01-LVL-BASE-A2B', 'gravacao'))
    ap.add_argument('--out', action='append', metavar='PNG',
                    help="onde gravar; repetivel. Sem ele, grava nos dois "
                         "destinos padrao (esta pasta e artigo/figuras)")
    args = ap.parse_args()

    gravs = gravacoes(args.dir)
    n = len(gravs)
    segundos = {round(len(s) / recording.FS, 1) for _, s in gravs}

    # As bordas comecam em meia janela para que os centros caiam em multiplos
    # de 50 Hz, e portanto o tom de 1700 Hz caia no centro de uma delas.
    bordas = np.arange(LARGURA_BIN / 2, FMAX + LARGURA_BIN, LARGURA_BIN)
    centros = (bordas[:-1] + bordas[1:]) / 2
    # Media em potencia, nao em decibel: a media dos logaritmos e a media
    # geometrica, que aqui pesaria a gravacao mais silenciosa demais.
    pot = np.mean([espectro(s, bordas) ** 2 for _, s in gravs], axis=0)
    curva = np.array([dbfs(v) for v in np.sqrt(pot)])
    envelope = np.array([[dbfs(v) for v in espectro(s, bordas)] for _, s in gravs])

    # O ponto do tom cai no centro de uma janela, entao e um valor da propria
    # curva, nao uma segunda medida ao lado dela.
    i_tom = int(np.argmin(np.abs(centros - TOM)))
    if abs(centros[i_tom] - TOM) > 1e-6:
        raise SystemExit(f"[piso] {TOM:.0f} Hz nao e centro de janela "
                         f"(mais proximo {centros[i_tom]:.1f} Hz)")

    largas = [dbfs(float(np.sqrt(np.mean(s ** 2)))) for _, s in gravs]
    uteis = [dbfs(band_rms(s, *BANDA)) for _, s in gravs]
    tons = [dbfs(band_rms(s, TOM - 25, TOM + 25)) for _, s in gravs]

    fig, ax = plt.subplots(figsize=(LARGURA, 3.4), layout='constrained')
    # A faixa util e o envelope sao os dois unicos preenchimentos, entao um
    # deles precisa de contorno: em cinza impresso duas manchas de tom
    # parecido lem como uma so.
    ax.axvspan(*BANDA, facecolor='0.93', edgecolor='none', zorder=0)
    for x in BANDA:
        ax.axvline(x, color='0.35', linewidth=0.8, linestyle=(0, (4, 3)),
                   zorder=2)
    # Com uma gravacao so o envelope colapsa sobre a curva: `fill_between`
    # nao desenha nada e a legenda anunciaria uma mancha invisivel.
    if n > 1:
        ax.fill_between(centros, envelope.min(axis=0), envelope.max(axis=0),
                        color='0.62', linewidth=0, alpha=0.55, zorder=2)
    ax.plot(centros, curva, color='black', linewidth=1.0, zorder=3)
    ax.plot([centros[i_tom]], [curva[i_tom]], linestyle='none', marker='o',
            markersize=6, markerfacecolor='white', markeredgecolor='black',
            markeredgewidth=1.1, zorder=5)
    ax.annotate(f"{virgula(TOM, 0)} Hz\n{virgula(curva[i_tom])} dBFS",
                xy=(centros[i_tom], curva[i_tom]),
                xytext=(centros[i_tom] + 430, curva[i_tom] + 7.0),
                ha='left', va='center', fontsize=8.5,
                arrowprops=dict(arrowstyle='-', linewidth=0.7, color='black',
                                shrinkA=1, shrinkB=4))

    ax.set_xlim(0, FMAX)
    lo = np.floor(curva.min() / 5) * 5 - 2
    hi = np.ceil(curva.max() / 5) * 5 + 6
    ax.set_ylim(lo, hi)

    # Os 16 tons como tracos curtos no rodape, como na figura da resposta do
    # canal: dezesseis linhas de altura inteira tapariam a curva. Aqui eles
    # dizem onde o modem tem de ser ouvido, que e a metade da leitura de
    # margem que a figura sozinha nao daria.
    #
    # E cada traco ganha a largura que o detector realmente escuta: a decisao
    # sai de uma janela de `samples_per_tone - guard` amostras, e uma janela
    # dessas resolve fs/N Hz. Fora dessas fatias o ruido da sala nao entra na
    # decisao, que e o "o que o sistema filtra" da leitura de margem.
    demod = MaryDemodulator(fs=recording.FS, baud=100)
    nwin = demod.samples_per_tone - demod.guard
    resolucao = recording.FS / nwin
    base = lo + 0.06 * (hi - lo)
    ax.vlines(MARY_TONES, lo, base, color='black', linewidth=1.1, zorder=4)
    ax.hlines([base] * len(MARY_TONES),
              np.array(MARY_TONES) - resolucao / 2,
              np.array(MARY_TONES) + resolucao / 2,
              color='black', linewidth=1.4, zorder=4)
    ax.xaxis.set_major_locator(MultipleLocator(1000))
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))
    ax.set_xlabel('Frequência (Hz)')
    ax.set_ylabel(f'Nível em janelas de {virgula(LARGURA_BIN, 0)} Hz (dBFS)')
    ax.grid(True, color='0.9', linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)

    duracao = ' e '.join(virgula(s) for s in sorted(segundos))
    handles = [
        Line2D([], [], color='black', linewidth=1.0,
               label=(f'Média de {n} gravações de {duracao} s' if n > 1
                      else f'Uma gravação de {duracao} s')),
    ]
    if n > 1:
        handles.append(Patch(facecolor='0.62', alpha=0.55, edgecolor='none',
                             label='Extremos das gravações'))
    handles += [
        Line2D([], [], linestyle='none', marker='o', markersize=6,
               markerfacecolor='white', markeredgecolor='black',
               label=f'Tom de referência de {virgula(TOM, 0)} Hz'),
        Patch(facecolor='0.93', edgecolor='0.35', linewidth=0.8,
              linestyle=(0, (4, 3)),
              label=f'Faixa útil {BANDA[0]}–{BANDA[1]} Hz'),
        Line2D([], [], color='black', linewidth=1.4,
               label=(f'16 sondas do detector, {virgula(resolucao, 0)} Hz '
                      f'cada ({virgula(1000 * nwin / recording.FS)} ms)')),
    ]
    ax.legend(handles=handles, loc='upper right', framealpha=0.95,
              borderpad=0.5)

    for destino in (args.out or SAIDAS):
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        fig.savefig(destino)
    plt.close(fig)

    print("[piso] " + ", ".join(args.out or SAIDAS))
    print(f"    {n} gravações de {', '.join(virgula(s) for s in sorted(segundos))} s, "
          f"pasta {args.dir}")
    print(f"    banda inteira: mediana {virgula(float(np.median(largas)))} dBFS "
          f"({virgula(min(largas))} a {virgula(max(largas))})")
    print(f"    faixa útil {BANDA[0]}–{BANDA[1]} Hz: mediana "
          f"{virgula(float(np.median(uteis)))} dBFS "
          f"({virgula(min(uteis))} a {virgula(max(uteis))})")
    print(f"    tom {virgula(TOM, 0)} Hz ±25 Hz: mediana "
          f"{virgula(float(np.median(tons)))} dBFS "
          f"({virgula(min(tons))} a {virgula(max(tons))}); "
          f"na curva média {virgula(curva[i_tom])} dBFS")
    dentro = (centros >= BANDA[0]) & (centros <= BANDA[1])
    dentro_tons = [f for f in MARY_TONES if BANDA[0] <= f <= BANDA[1]]
    pisos = [curva[int(np.argmin(np.abs(centros - f)))] for f in MARY_TONES]
    print(f"    janela de decisão {nwin} amostras, "
          f"{virgula(resolucao)} Hz por sonda")
    print(f"    {len(dentro_tons)} de {len(MARY_TONES)} tons do 16-FSK dentro da "
          f"faixa útil; piso sob eles de {virgula(min(pisos))} a "
          f"{virgula(max(pisos))} dBFS")
    print(f"    curva média: {virgula(curva.min())} a {virgula(curva.max())} dBFS; "
          f"na faixa útil {virgula(curva[dentro].min())} a "
          f"{virgula(curva[dentro].max())} dBFS")


if __name__ == '__main__':
    main()
