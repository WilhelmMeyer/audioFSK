"""Figura do artigo: bits certos ao longo do quadro, malha contra varreduras.

Le as 24 gravacoes do estudo de ganho de 2026-09-03 (16-FSK, 48 bytes, rep 1,
varreduras nas duas pontas, uma maquina com caixa Bluetooth), cada uma de dois
jeitos, como `resultado.py` le: a malha de adiantamento e atraso e o relogio
medido pelas duas varreduras (`modem.sweep_soft`). Para cada leitura, o quadro
transmitido (palavra de referencia mais bloco codificado) e alinhado pelo
melhor deslizamento do quadro inteiro, uma regua so para as duas curvas, e o
acerto e contado em janelas de 5% do quadro. A curva e a media das 24.

O estudo fica em old/studies/, fora do git; o audio nao e versionado.

    ./venv/bin/python resultados/FIG-SINCRONISMO/figura_sincronismo_bloco.py
"""
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
import recording
import resultado

ESTUDO = os.path.join(RAIZ, 'old', 'studies', '20260903-111105-ganho-mary', 'recordings')
JANELAS = 20
SAIDAS = (os.path.join(AQUI, 'sincronismo-bloco.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'sincronismo-bloco.png'))
TEAL, CINZA = '#0F5257', '#9AA5A8'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})


def janelas(llr, want):
    off, _ = resultado.best_slide(llr, want)
    certo = np.sign(llr[off:off + len(want)]) == (2 * want - 1)
    return [100 * p.mean() for p in np.array_split(certo, JANELAS)]


def main():
    malha, varr, nbits = [], [], None
    blocos = [0, 0]
    for j in sorted(glob.glob(os.path.join(ESTUDO, '*.json'))):
        samples, payload, meta = recording.load(j)
        want = resultado.frame_bits(payload, meta)
        nbits = len(want)
        g = resultado.soft(resultado.demodulator(meta), samples)
        v, how, _, _ = resultado.sweep_llr(samples, payload, meta)
        malha.append(janelas(g, want))
        varr.append(janelas(v, want))
        blocos[0] += bool(resultado.decodes(g, payload, meta))
        blocos[1] += bool(resultado.decodes(v, payload, meta))
    m, v = np.mean(malha, axis=0), np.mean(varr, axis=0)
    x = (np.arange(JANELAS) + 0.5) * 100 / JANELAS

    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax.plot(x, v, color=TEAL, lw=1.5)
    ax.plot(x, m, color=CINZA, lw=1.5)
    ax.text(101, v[-1] + 0.8, f'varreduras\n{blocos[1]} de {len(malha)} blocos',
            color=TEAL, fontsize=7.5, va='bottom')
    ax.text(101, m[-1] - 0.8, f'malha\n{blocos[0]} de {len(malha)} blocos',
            color='0.45', fontsize=7.5, va='top')
    ax.set_xlim(0, 100)
    ax.set_ylim(75, 100)
    ax.set_xlabel('Posição no quadro (%)')
    ax.set_ylabel('Bits certos (%)')
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[sincronismo]', ', '.join(SAIDAS))
    print(f'    {len(malha)} gravacoes, quadro de {nbits} bits; blocos malha {blocos[0]}, '
          f'varreduras {blocos[1]}')
    q = JANELAS // 10  # primeiros 10% do quadro
    print(f'    primeiros 10%: malha {m[:q].mean():.1f}%, varreduras {v[:q].mean():.1f}%')
    print(f'    resto:         malha {m[q:].mean():.1f}%, varreduras {v[q:].mean():.1f}%')


if __name__ == '__main__':
    main()
