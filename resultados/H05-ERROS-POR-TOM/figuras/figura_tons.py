"""Figura do artigo: erros de símbolo por tom em três sessões do mesmo sentido.

Lê ../simbolos.json (escrito por erros_por_tom.py, mapeamento Gray antigo, o
das gravações) e conta, em cada sessão, a fração dos erros de símbolo que
caiu em cada tom transmitido. Sessões B->A de 2026-09-03: 14-FEC-REP,
12-13-SYNC e 08-MARY-GAIN, nomeadas na figura como sessão 1, 2 e 3. Os três
piores tons de cada sessão vão em marcador cheio.

    ./venv/bin/python resultados/H05-ERROS-POR-TOM/figuras/figura_tons.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
H05 = os.path.dirname(AQUI)
RAIZ = os.path.dirname(os.path.dirname(H05))
sys.path.insert(0, RAIZ)
from modem import MARY_TONES  # noqa: E402

SAIDAS = (os.path.join(AQUI, 'erros-por-tom.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'erros-por-tom.png'))
TEAL, TEAL_MED, CINZA, OCRE = '#0F5257', '#2E7D82', '#9AA5A8', '#B2683E'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})

# (rótulo, campanha, cor, marcador)
SESSOES = [('Sessão 1', '14-FEC-REP', TEAL, 'o'),
           ('Sessão 2', '12-13-SYNC', OCRE, 's'),
           ('Sessão 3', '08-MARY-GAIN', CINZA, '^')]


def fracoes(dados, campanha):
    e = np.zeros(16)
    for r in dados:
        if r['direcao'] != 'B->A' or r['campanha'] != campanha:
            continue
        s, t = np.array(r['enviado']), np.array(r['detectado'])
        m = min(len(s), len(t))
        s, t = s[:m], t[:m]
        np.add.at(e, s[s != t], 1)
    return e / e.sum(), int(e.sum())


def main():
    dados = json.load(open(os.path.join(H05, 'simbolos.json')))
    x = np.arange(16)
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    ax.axhline(100 / 16, color=CINZA, lw=0.7, ls=':', zorder=0)
    ax.text(-0.3, 100 / 16 + 1.2, 'uniforme, 1/16', fontsize=6.5, color=CINZA, ha='left')
    for rot, camp, cor, mk in SESSOES:
        f, n = fracoes(dados, camp)
        piores = np.argsort(-f)[:3]
        ax.plot(x, 100 * f, color=cor, lw=0.8, alpha=0.7)
        ax.plot(x, 100 * f, mk, color=cor, ms=3, markerfacecolor='white', markeredgewidth=0.8)
        ax.plot(piores, 100 * f[piores], mk, color=cor, ms=5, label=f'{rot}: {100 * f[piores].sum():.0f}%'.replace('.', ','))
        print(f'    {rot} ({camp}): {n} erros; piores '
              + ', '.join(f'{MARY_TONES[i]:.0f} Hz {100 * f[i]:.1f}%' for i in piores)
              + f'; soma {100 * f[piores].sum():.1f}%')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{t:.0f}' for t in MARY_TONES], rotation=90)
    ax.set_xlabel('Tom transmitido (Hz)')
    ax.set_ylabel('Fração dos erros de símbolo (%)')
    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(0, 42)
    ax.legend(frameon=False, fontsize=7, loc='upper right',
              title='erros nos três piores tons', title_fontsize=7)
    ax.grid(axis='y', color='0.9', lw=0.5)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    for s in SAIDAS:
        fig.savefig(s, bbox_inches='tight')
    print('[tons]', ', '.join(SAIDAS))


if __name__ == '__main__':
    main()
