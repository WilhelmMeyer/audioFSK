"""Figura do artigo: espectrograma da varredura, sentido A->B.

Refaz o espectrograma de `resultados/03-CH-CHIRP-A2B/` com resolucao de
frequencia utilizavel. PNG 300 dpi, largura de uma coluna, escala de cinza.
Sem titulo dentro da figura, a legenda e do texto.

    ./venv/bin/python resultados/03-CH-CHIRP-A2B/figuras/figura_varredura.py [--gravacao <wav|json>]

A janela e o assunto desta figura. A PNG que a campanha ja tem veio do
`spectro.py` com 900 colunas sobre 8 s, ou seja janelas de ~427 amostras e
cerca de 112 Hz por bin -- e os tons da 16-FSK estao 162 Hz apart, entao
naquela resolucao dois tons vizinhos quase se encostam e a varredura sai como
uma faixa grossa. A espessura era do instrumento. Aqui a janela e de 4096
amostras (11,7 Hz por bin, 85,3 ms), que numa varredura de 6 s sobra tempo de
sobra, e a largura que se ve passa a ser a do sinal.

Um painel so, nao os dois do `spectro.py`: numa varredura cada linha de
frequencia so tem energia enquanto a rampa passa por ela, entao a mediana da
linha ja e o piso e o painel de contraste sai quase igual ao cru.

O script mede e imprime o que decide se a figura entra no artigo: a largura
real da rampa contra os 162 Hz que separam os tons, o nivel dos harmonicos
que a cadeia gera, e o que acontece depois que a varredura termina.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np


def raiz():
    """A raiz do repositorio, achada subindo ate encontrar `modem.py`."""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[varredura] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import recording
from modem import MARY_TONES

GRAVACAO = os.path.join(RAIZ, 'resultados', '03-CH-CHIRP-A2B', 'gravacao',
                        '20260903-175426-ch-chirp-A2B.json')
JANELA = 4096            # amostras: 11,7 Hz por bin a 48 kHz, 85,3 ms
SALTO = 512              # 10,7 ms entre colunas
FAIXA_DB = 75.0          # profundidade da escala abaixo do maximo
FMAX = 12500.0           # cabe a rampa, o 2o harmonico inteiro e o 3o em parte
LARGURA = 6.3            # polegadas ~ 16 cm, uma coluna

# Paleta: teal escuro para a serie principal, azul gelo para o que e fundo ou
# dispersao. Escolha do autor. A figura continua legivel em escala de cinza
# porque nada e codificado so por cor: cada serie tem marcador e traco
# proprios, e a cor apenas reforca.
TEAL = '#0F5257'
TEAL_MED = '#2E7D82'
GELO = '#BFDDE4'
GELO_CLARO = '#E8F2F5'

# A imagem fica em cinza, e a cor entra so nas marcacoes. Um mapa tingido de
# teal foi tentado e piorou a leitura: os tons claros de gelo comem o meio da
# escala, que e exatamente onde vivem os harmonicos, 30 e 42 dB abaixo da
# fundamental. Num espectrograma a cor tem de gastar toda a luminosidade
# disponivel com o dado.
MAPA = 'gray_r'

# Dois destinos e uma geracao so. O PNG do artigo e o mesmo arquivo que
# fica aqui ao lado dos dados: a pasta do artigo carrega apenas figuras, e
# o que as gera mora junto da campanha que elas medem.
SAIDAS = (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'varredura.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'varredura.png'))

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


def sep_tons():
    """A separacao entre tons vizinhos da 16-FSK, lida do codigo."""
    return float(np.min(np.diff(sorted(MARY_TONES))))


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


def carrega(caminho):
    """A gravacao e o que o JSON diz que ela carrega."""
    stem = Path(caminho).with_suffix('')
    meta = json.loads(stem.with_suffix('.json').read_text())
    if meta.get('kind') != 'chirp' or 'chirp' not in meta:
        raise SystemExit(f"[varredura] {stem.name} nao e uma varredura "
                         f"(kind={meta.get('kind')!r})")
    return recording.read(recording.audio_path(stem)), meta


def stft(samples, fs, janela=JANELA, salto=SALTO):
    """Espectrograma em dB relativo a fundo de escala.

    Hann com o ganho da janela dividido de volta, para que uma senoide de
    amplitude 1 leia 0 dB e o eixo signifique dBFS como no resto do projeto.
    """
    w = np.hanning(janela)
    n = 1 + (len(samples) - janela) // salto
    quadros = np.lib.stride_tricks.as_strided(
        samples, shape=(n, janela),
        strides=(samples.strides[0] * salto, samples.strides[0]))
    espectro = np.fft.rfft(quadros * w, axis=1)
    mag = 2 * np.abs(espectro) / w.sum()
    freqs = np.fft.rfftfreq(janela, 1.0 / fs)
    tempos = (np.arange(n) * salto + janela / 2) / fs
    return tempos, freqs, 20 * np.log10(np.maximum(mag, 1e-12))


def inicio(samples, fs, meta):
    """Quando a rampa comeca, medido, nao suposto.

    O JSON diz a duracao e as frequencias, e nao diz o silencio que veio
    antes: o agente comeca a gravar antes de a maquina de la tocar, e quanto
    antes depende da ida e volta pelo cabo serial. Um instante suposto
    deslocaria as diagonais previstas em relacao ao que a figura mostra.
    """
    n = int(0.01 * fs)
    env = np.sqrt(np.mean(samples[:len(samples) // n * n]
                          .reshape(-1, n) ** 2, axis=1))
    piso = np.median(env[:50])                 # meio segundo de sala
    alto = np.max(env)
    limiar = np.sqrt(piso * alto)              # meio caminho, em dB
    acima = np.flatnonzero(env > limiar)
    if len(acima) == 0:
        raise SystemExit("[varredura] nao achei o comeco da rampa")
    return acima[0] * n / fs


def largura(freqs, coluna, pico_db, queda=6.0):
    """Largura da crista em Hz, a `queda` dB abaixo do maximo da coluna."""
    i = int(np.argmax(coluna))
    lo = i
    while lo > 0 and coluna[lo] > pico_db - queda:
        lo -= 1
    hi = i
    while hi < len(coluna) - 1 and coluna[hi] > pico_db - queda:
        hi += 1
    return freqs[hi] - freqs[lo], freqs[i]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--gravacao', default=GRAVACAO)
    ap.add_argument('--out', action='append', metavar='PNG',
                    help="onde gravar; repetivel. Sem ele, grava nos dois "
                         "destinos padrao (esta pasta e artigo/figuras)")
    args = ap.parse_args()

    samples, meta = carrega(args.gravacao)
    fs = meta.get('fs', recording.FS)
    f0, f1, dur = meta['chirp']
    t0 = inicio(samples, fs, meta)
    tempos, freqs, db = stft(samples, fs)

    sel = freqs <= FMAX
    imagem = db[:, sel].T
    topo = float(imagem.max())

    fig, ax = plt.subplots(figsize=(LARGURA, 3.8), layout='constrained')
    im = ax.imshow(imagem, origin='lower', aspect='auto', cmap=MAPA,
                   vmin=topo - FAIXA_DB, vmax=topo,
                   extent=(tempos[0], tempos[-1], 0.0, freqs[sel][-1]),
                   interpolation='nearest')

    # As diagonais previstas: a fundamental e os harmonicos que a cadeia
    # fabrica. Tracejadas e rotuladas, e desenhadas a partir do instante
    # medido do inicio, nao de um instante suposto.
    # So os harmonicos levam tracejado, e os dois com o mesmo traco: a
    # fundamental e a propria rampa, que ja se ve, e uma linha sobre ela lia
    # como uma quarta diagonal paralela as outras.
    # Os harmonicos sao apontados de fora, nunca cobertos. Uma linha sobre a
    # diagonal esconde justamente a energia fraca que a figura existe para
    # mostrar: a seta para a poucos pixels da faixa e o rotulo fica no vazio
    # ao lado.
    # A fundamental entra com a mesma marcacao dos harmonicos: e ela a
    # frequencia emitida, e sem faixa a figura marcava so o que a cadeia
    # inventou e deixava sem nome o que foi transmitido.
    for ordem, texto_xy in ((1, (3.05, 620.0)), (2, (7.3, 8600.0)),
                            (3, (3.35, 11500.0))):
        fa, fb = ordem * f0, ordem * f1
        if fa > FMAX:
            continue
        fim = dur if fb <= FMAX else dur * (FMAX - fa) / (fb - fa)
        # A area, e nao a linha: uma faixa clara acompanhando a diagonal, larga
        # o bastante para conter a energia do harmonico e clara o bastante para
        # nao apaga-la. A linha tracejada de antes passava exatamente por cima
        # do que a figura existe para mostrar.
        tt = np.linspace(t0, t0 + fim, 64)
        ff = fa + (fb - fa) * (tt - t0) / dur
        meia = 420.0
        ax.fill_between(tt, ff - meia, ff + meia, facecolor=TEAL, alpha=0.13,
                        edgecolor='none', zorder=2)
        ax.plot(tt, ff - meia, color=TEAL, linewidth=0.6, alpha=0.55, zorder=2)
        ax.plot(tt, ff + meia, color=TEAL, linewidth=0.6, alpha=0.55, zorder=2)
        # O rotulo aponta para a borda da faixa, nunca para dentro dela.
        frac = 0.35 if ordem == 1 else 0.72
        # Para a fundamental o rotulo vem por baixo: acima dela estao as duas
        # faixas dos harmonicos.
        lado = -meia if ordem == 1 else meia
        alvo = (t0 + frac * fim, fa + (fb - fa) * frac * fim / dur + lado)
        nome = ('varredura emitida' if ordem == 1 else f'{ordem}º harmônico')
        ax.annotate(nome, xy=alvo, xytext=texto_xy,
                    ha='center', va='center', fontsize=8.5, color='black',
                    arrowprops=dict(arrowstyle='->', linewidth=0.9,
                                    color=TEAL, shrinkA=2, shrinkB=6,
                                    mutation_scale=9),
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor='none', alpha=0.85))

    # O recorte existe porque a figura inteira nao consegue mostrar a
    # largura da rampa: 12 kHz de eixo em 16 cm sao ~90 Hz por milimetro, e o
    # que esta em julgamento sao os 162 Hz que separam dois tons vizinhos.
    # O recorte e centrado entre dois tons vizinhos, para que os dois
    # tracejados aparecam e a comparacao com a largura seja direta.
    alvo = np.mean(sorted(MARY_TONES)[9:11])
    tz = t0 + dur * (alvo - f0) / (f1 - f0)
    fz = alvo
    # A janela de tempo e curta de proposito: em 0,10 s a rampa sobe 95 Hz,
    # menos que os 162 Hz em julgamento, entao o que se ve na vertical e a
    # largura da crista e nao a inclinacao dela.
    jan_t, jan_f = 0.05, 200.0
    vizinhos = [f for f in MARY_TONES if abs(f - fz) < jan_f]
    # A escala do recorte e local. Referida ao maximo global, que e o pico da
    # rampa perto de 6 kHz, uma janela curta deixaria o recorte inteiro
    # branco: a crista ali chega uns 30 dB abaixo daquele pico.
    fatia_t = (tempos >= tz - jan_t) & (tempos <= tz + jan_t)
    fatia_f = (freqs[sel] >= fz - jan_f) & (freqs[sel] <= fz + jan_f)
    local = float(imagem[np.ix_(fatia_f, fatia_t)].max())

    zi = ax.inset_axes([0.64, 0.05, 0.26, 0.25])
    zi.imshow(imagem, origin='lower', aspect='auto', cmap=MAPA,
              vmin=local - 26.0, vmax=local,
              extent=(tempos[0], tempos[-1], 0.0, freqs[sel][-1]),
              interpolation='nearest')
    zi.set_xlim(tz - jan_t, tz + jan_t)
    zi.set_ylim(fz - jan_f, fz + jan_f)
    for f in vizinhos:
        zi.axhline(f, color=TEAL, linewidth=0.9, linestyle=(0, (3, 2)))
    zi.set_xticks([])
    zi.set_yticks(vizinhos)
    zi.set_yticklabels([f"{f:.0f}" for f in vizinhos], fontsize=7)
    zi.tick_params(length=2, pad=1)
    zi.set_title(f'recorte de {virgula(2 * jan_t, 2)} s, tracejados '
                 f'{virgula(sep_tons(), 0)} Hz', fontsize=7.0, pad=2)
    for lado in zi.spines.values():
        lado.set_linewidth(0.8)
    ax.indicate_inset_zoom(zi, edgecolor=TEAL, linewidth=0.8, alpha=1.0)

    ax.set_xlim(0, len(samples) / fs)
    ax.set_ylim(0, FMAX)
    ax.set_xlabel('Tempo (s)')
    ax.set_ylabel('Frequência (Hz)')
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_major_locator(MultipleLocator(2000))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))

    barra = fig.colorbar(im, ax=ax, pad=0.02)
    barra.set_label('Nível (dBFS)')
    barra.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: virgula(v, 0)))

    for destino in (args.out or SAIDAS):
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        fig.savefig(destino)
    plt.close(fig)

    # ---- o que a figura tem de sustentar, medido da mesma STFT ----
    print("[varredura] " + ", ".join(args.out or SAIDAS))
    print(f"    {virgula(f0, 0)}-{virgula(f1, 0)} Hz em {virgula(dur)} s, "
          f"começando em {virgula(t0, 2)} s; gravação de "
          f"{virgula(len(samples) / fs)} s")
    print(f"    janela {JANELA} amostras: {virgula(fs / JANELA)} Hz por bin, "
          f"{virgula(1000 * JANELA / fs)} ms; salto {SALTO} "
          f"({virgula(1000 * SALTO / fs)} ms)")

    sep = sep_tons()
    dentro = (tempos > t0 + 0.3) & (tempos < t0 + dur - 0.3)
    larguras, alvos = [], []
    for i in np.flatnonzero(dentro):
        col = db[i]
        w, fp = largura(freqs, col, col.max())
        larguras.append(w)
        alvos.append(fp)
    larguras = np.array(larguras)
    print(f"    largura da crista a -6 dB: mediana {virgula(np.median(larguras))} Hz "
          f"({virgula(larguras.min())} a {virgula(larguras.max())}), contra "
          f"{virgula(sep, 0)} Hz entre tons vizinhos da 16-FSK")
    print(f"    invade a separação em {int((larguras > sep).sum())} de "
          f"{len(larguras)} colunas")

    # Harmonicos: o nivel em 2f e 3f contra a fundamental, na mesma coluna.
    for ordem in (2, 3):
        rel = []
        for i in np.flatnonzero(dentro):
            f = f0 + (f1 - f0) * (tempos[i] - t0) / dur
            if ordem * f > freqs[-1]:
                continue
            def nivel(fc):
                j = (freqs > fc - 60) & (freqs < fc + 60)
                return db[i][j].max()
            rel.append(nivel(ordem * f) - nivel(f))
        if rel:
            print(f"    {ordem}º harmônico: mediana {virgula(float(np.median(rel)))} dB "
                  f"abaixo da fundamental ({virgula(min(rel))} a {virgula(max(rel))})")

    # Depois do fim: cauda ou queda direta ao piso. Medido na banda em que a
    # rampa terminou, que e onde uma cauda apareceria.
    # Aqui a janela longa da figura atrapalha: 85 ms de janela espalham o
    # fim da rampa por 85 ms de tempo, e isso sozinho pareceria cauda. A
    # cauda e medida com janela curta, 512 amostras (10,7 ms), que resolve
    # mal a frequencia e bem o tempo, que e o que esta em julgamento.
    fim = t0 + dur
    tempos, freqs, db = stft(samples, fs, janela=512, salto=128)
    j = (freqs > f1 - 400) & (freqs < f1 + 400)
    piso = float(np.median(db[tempos < t0 - 0.2][:, j]))
    print(f"    depois do fim ({virgula(fim, 2)} s), janela de 512 amostras, banda "
          f"{virgula(f1 - 400, 0)}-{virgula(f1 + 400, 0)} Hz, "
          f"piso da sala {virgula(piso)} dBFS:")
    for dt in (-0.05, 0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8):
        i = int(np.argmin(np.abs(tempos - (fim + dt))))
        if tempos[i] > tempos[-1]:
            continue
        sinal = '+' if dt >= 0 else ''
        print(f"      {sinal}{virgula(dt, 2)} s  "
              f"{virgula(float(db[i][j].max()))} dBFS")


if __name__ == '__main__':
    main()
