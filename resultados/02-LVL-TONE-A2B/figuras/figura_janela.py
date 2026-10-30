"""Figura do artigo: por que um tom limpo chega espalhado por outras frequências.

Duas partes. Em cima, um símbolo da gravação de 1700 Hz no tempo: as 480
amostras do símbolo, as 72 descartadas como guarda e as 408 que o detector
analisa. Embaixo, o espectro dessas 408 amostras, calculado com resolução
fina (preenchimento com zeros), comparado com o de um seno ideal de 1700 Hz
calculado no computador e cortado na mesma janela, sem alto-falante, ar ou
microfone. As marcas verticais são os dezesseis tons da 16-FSK.

    ./venv/bin/python resultados/02-LVL-TONE-A2B/figuras/figura_janela.py

O seno cortado em N amostras não é uma linha: o espectro é um lóbulo
principal de largura 2 fs/N e lóbulos laterais, |sen(pi x)/(pi x)| com
x = (f - f0) N / fs. A figura mostra que o tom gravado segue essa forma, e
que o tom vizinho, 162,5 Hz acima, cai no primeiro lóbulo lateral.
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, 'modem.py')):
            return d
        d = os.path.dirname(d)
    raise SystemExit("[janela] nao achei a raiz do repositorio")


RAIZ = raiz()
sys.path.insert(0, RAIZ)

import recording
from modem import MaryDemodulator, MARY_TONES

COM = os.path.join(RAIZ, 'resultados', '02-LVL-TONE-A2B', 'gravacao',
                   '20260903-175101-lvl-tone-A2B.wav')
TOM = 1700.0
JANELAS = 100
NFFT = 1 << 15
LARGURA = 6.3

TEAL = '#0F5257'
TEAL_MED = '#2E7D82'
GELO = '#BFDDE4'
CINZA = '#9AA5A8'

SAIDAS = (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espalhamento-janela.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'espalhamento-janela.png'))

plt.rcParams.update({
    'font.size': 9, 'axes.labelsize': 9.5, 'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5, 'legend.fontsize': 8, 'axes.linewidth': 0.8,
    'savefig.dpi': 300, 'figure.dpi': 300,
})


def virgula(v, casas=1):
    return f"{v:.{casas}f}".replace('.', ',')


def main():
    samples = recording.read(COM)
    fs = recording.FS
    demod = MaryDemodulator(fs=fs, baud=100)
    sps = demod.samples_per_symbol
    guarda = demod.guard
    n = demod.samples_per_tone - guarda
    inicio = len(samples) // 2 - JANELAS * sps // 2

    freqs = np.fft.rfftfreq(NFFT, 1 / fs)
    espectros = []
    for k in range(JANELAS):
        seg = samples[inicio + k * sps + guarda:inicio + k * sps + guarda + n]
        espectros.append(np.abs(np.fft.rfft(seg, NFFT)))
    rec = np.median(espectros, axis=0)
    rec_db = 20 * np.log10(np.maximum(rec, 1e-12) / rec.max())

    t = np.arange(n) / fs
    ideal = np.abs(np.fft.rfft(np.sin(2 * np.pi * TOM * t), NFFT))
    ideal_db = 20 * np.log10(np.maximum(ideal, 1e-12) / ideal.max())

    df = fs / n
    viz = TOM + (MARY_TONES[1] - MARY_TONES[0])
    iv = np.argmin(np.abs(freqs - viz))
    x = (viz - TOM) * n / fs
    teoria = 20 * np.log10(abs(np.sin(np.pi * x) / (np.pi * x)))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(LARGURA, 4.9),
                                 gridspec_kw=dict(height_ratios=[1, 2.2]))

    # (a) um símbolo no tempo
    k0 = JANELAS // 2
    sim = samples[inicio + k0 * sps:inicio + (k0 + 1) * sps]
    ms = np.arange(sps) / fs * 1e3
    pico = np.max(np.abs(sim)) * 1.9
    a1.axvspan(0, guarda / fs * 1e3, color=GELO, alpha=0.6, lw=0)
    a1.plot(ms, sim, color=TEAL, lw=0.7)
    a1.set_xlim(0, sps / fs * 1e3)
    a1.set_ylim(-pico, pico)
    a1.set_yticks([])
    a1.set_xlabel('Tempo dentro do símbolo (ms)')
    a1.text(0.06, pico * 0.95, f'descarte: {guarda} amostras',
            ha='left', va='top', fontsize=7.5, color=TEAL)
    a1.annotate('', xy=(guarda / fs * 1e3, -pico * 0.62), xytext=(sps / fs * 1e3, -pico * 0.62),
                arrowprops=dict(arrowstyle='<->', color=TEAL_MED, lw=0.8))
    a1.text((guarda + sps) / 2 / fs * 1e3, -pico * 0.70,
            f'janela analisada: {n} amostras, {virgula(n / fs * 1e3)} ms',
            ha='center', va='top', fontsize=7.5, color=TEAL)
    a1.set_title('(a) Um símbolo do tom de 1700 Hz recebido', fontsize=9, loc='left')

    # (b) espectro da janela
    for f in MARY_TONES:
        a2.axvline(f, color=CINZA, lw=0.5, ls=':', zorder=0)
    a2.plot(freqs, ideal_db, color=TEAL_MED, lw=1.0, ls='--',
            label='Seno ideal calculado, mesma janela')
    a2.plot(freqs, rec_db, color=TEAL, lw=1.2,
            label=f'Tom recebido (mediana de {JANELAS} janelas)')
    a2.set_xlim(800, 3400)
    a2.set_ylim(-60, 8)
    a2.set_xlabel('Frequência (Hz); linhas pontilhadas: os dezesseis tons da 16-FSK')
    a2.set_ylabel('Nível relativo ao pico (dB)')
    a2.annotate('', xy=(TOM - df, -44), xytext=(TOM + df, -44),
                arrowprops=dict(arrowstyle='<->', color=TEAL, lw=0.8))
    a2.text(TOM, -46, f'lóbulo principal\n±fs/N = ±{virgula(df, 0)} Hz', ha='center', va='top',
            fontsize=7.5, color=TEAL)
    a2.plot([viz], [rec_db[iv]], 'o', color=TEAL, ms=4)
    a2.annotate(f'tom vizinho, {virgula(viz, 1)} Hz:\n{virgula(rec_db[iv])} dB recebido, '
                f'{virgula(teoria)} dB previsto',
                xy=(viz, rec_db[iv]), xytext=(2150, -4), fontsize=7.5, color=TEAL,
                arrowprops=dict(arrowstyle='-', color=TEAL_MED, lw=0.7))
    a2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False, fontsize=7.5)
    a2.set_title('(b) Espectro da janela analisada', fontsize=9, loc='left')
    a2.grid(axis='y', color='#E5E5E5', lw=0.5)

    fig.tight_layout(h_pad=0.8)
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print(f"[janela] {', '.join(SAIDAS)}")
    print(f"    janela {n} amostras, {virgula(n / fs * 1e3)} ms, fs/N = {virgula(df)} Hz")
    print(f"    vizinho {virgula(viz)} Hz: recebido {virgula(rec_db[iv])} dB, "
          f"seno ideal {virgula(ideal_db[iv])} dB, sinc {virgula(teoria)} dB")


if __name__ == '__main__':
    main()
