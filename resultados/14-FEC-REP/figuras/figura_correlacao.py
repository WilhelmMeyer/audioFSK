"""Figura do artigo: a palavra de referência localizada por correlação.

Uma gravação real desta campanha (16-FSK, correção de erros, repetição 1,
bloco entregue íntegro) é demodulada como resultado.py a demodula: em blocos
de 2048 amostras, decisão suave, código Gray da gravação por
modem.gray_gravado. A correlação é a de fec.find_sync, sinal de cada valor
suave contra a palavra de 31 bits em ±1, dividida por 31. A linha marca o
início que o decodificador usou; o bloco decodificado confere com a carga.

    ./venv/bin/python resultados/14-FEC-REP/figuras/figura_correlacao.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
sys.path.insert(0, RAIZ)
import fec                                            # noqa: E402
import modem                                          # noqa: E402
import recording                                      # noqa: E402

STEM = '20260903-172504-rep1-B2A'
BLOCO = 2048
TEAL, TEAL_MED, CINZA = '#0F5257', '#2E7D82', '#9AA5A8'
SAIDAS = (os.path.join(AQUI, 'correlacao-palavra.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'correlacao-palavra.png'))
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})


def virgula(v, casas=2):
    return f'{v:.{casas}f}'.replace('.', ',')


def main():
    base = os.path.join(os.path.dirname(AQUI), 'gravacao', STEM)
    meta = json.load(open(base + '.json'))
    x = recording.read(recording.audio_path(base))
    d = modem.MaryDemodulator(fs=meta['fs'], baud=meta['baud'], gray=modem.gray_gravado(meta))
    llr = np.concatenate([d.demodulate_soft(x[i:i + BLOCO]) for i in range(0, len(x), BLOCO)])

    inicio = fec.find_sync(llr)
    carga = bytes.fromhex(meta['payload_hex'])
    if inicio is None or fec.decode(llr[inicio:], meta['payload_len'],
                                    repeat=meta['fec_repeat']) != carga:
        raise SystemExit(f'[correlacao] {STEM}: bloco não decodifica')

    # o mesmo cálculo de fec.find_sync
    want = 2.0 * fec.SYNC - 1.0
    c = np.correlate(np.sign(llr), want, mode='valid') / len(fec.SYNC)
    pico = int(np.argmax(c))
    assert pico + len(fec.SYNC) == inicio
    fora = np.abs(c[pico + len(fec.SYNC):])          # depois da palavra: o bloco de dados
    lobo = float(np.max(np.delete(np.abs(c), range(pico - 30, pico + 31))))

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    k = np.arange(len(c))
    nbloco = len(fec.encode(carga, repeat=meta['fec_repeat']))
    # preâmbulo: o trecho mais longo de correlação constante antes do pico
    igual = np.r_[False, np.abs(np.diff(c[:pico])) < 1e-9, False].astype(int)
    bordas = np.flatnonzero(np.diff(igual))
    corridas = list(zip(bordas[::2], bordas[1::2]))
    pre0 = int(max(corridas, key=lambda r: r[1] - r[0])[0]) - 1 if corridas else pico
    for a, b, nome in ((pre0, pico, 'preâmbulo'), (inicio, inicio + nbloco, 'bloco codificado')):
        ax.axvspan(a, b, color='#E3EEF0', lw=0, zorder=0)
        ax.text((a + b) / 2, -0.56, nome, ha='center', va='bottom', fontsize=7, color='0.3')
    ax.axhline(0, color=CINZA, lw=0.5)
    ax.plot(k, c, color=TEAL_MED, lw=0.45)
    ax.axhline(0.55, color=CINZA, lw=0.7, ls='--')
    ax.text(len(c) * 0.99, 0.58, 'limiar 0,55', ha='right', va='bottom', fontsize=7, color='0.35')
    ax.plot([pico], [c[pico]], 'o', color=TEAL, ms=3.5)
    ax.annotate(f'palavra de referência\npico {virgula(c[pico])}', xy=(pico, c[pico]),
                xytext=(pico + 0.12 * len(c), 0.88), fontsize=7.5, color=TEAL, va='top',
                arrowprops=dict(arrowstyle='-', color=TEAL, lw=0.6))
    ax.set_xlim(0, len(c))
    ax.set_ylim(-0.6, 1.05)
    ax.set_xlabel('Posição no fluxo recebido (bits)')
    ax.set_ylabel('Correlação normalizada')
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[correlacao]', ', '.join(SAIDAS))
    print(f'    {len(llr)} bits, pico {c[pico]:.3f} em {pico}, inicio {inicio}, '
          f'maior fora do pico ±30: {lobo:.3f} ({lobo * 31:.0f}/31), '
          f'maior no bloco de dados {fora.max():.3f}, acerto do bloco {meta.get("payload_len")} B')


if __name__ == '__main__':
    main()
