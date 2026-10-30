"""Figuras do capítulo de resultados: formas de transmissão e sincronismo.

Formas: lê acerto_bits e bloco_ok de cada gravação nos resultado.csv das
campanhas a 10 cm de 2026-10-08. Sincronismo: contagens de blocos íntegros
das campanhas 12-13-SYNC, H03-2FSK-FEC e do estudo de ganho com uma máquina,
escritas abaixo com a origem de cada uma.

    ./venv/bin/python resultados/FIG-RESULTADOS/figuras_resultados.py
"""
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(AQUI)
ART = os.path.join(os.path.dirname(RES), 'artigo', 'figuras')
TEAL, TEAL_MED, CINZA = '#0F5257', '#2E7D82', '#9AA5A8'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})

# (rótulo, campanha, modo no csv, taxa útil calculada em B/s ou None)
FORMAS = [
    ('2-FSK Bell 202\nsem correção', 'F01-2FSK-10CM', 'fsk', None),
    ('2-FSK 1700/2350 Hz\ncom correção', 'H03-2FSK-FEC', 'fsk2', 3.6),
    ('5×2-FSK votada', 'F02-5X2-VOTADA-10CM', 'mfsk', 3.7),
    ('5×2-FSK multicanal', 'F03-5X2-MULTICANAL-10CM', 'mfsk', 13.8),
    ('16-FSK', 'F00-NIVEL-10CM', 'mary', 11.2),
    ('16-FSK com\nvarreduras', 'F04-16FSK-10CM', 'mary', 10.7),
]

# (rótulo, gravações, blocos malha, blocos varreduras)
SINC = [
    ('16-FSK,\nduas máquinas', 4, 4, 4),        # 12-13-SYNC
    ('2-FSK,\nduas máquinas', 8, 6, 7),                  # H03-2FSK-FEC, as 8 com varreduras
    ('16-FSK,\numa máquina', 24, 15, 23),       # studies/20260903-111105-ganho-mary
]


def salva(fig, nome):
    for d in (AQUI, ART):
        fig.savefig(os.path.join(d, nome), bbox_inches='tight')
    print('[resultados]', nome)


def formas():
    fig, ax = plt.subplots(figsize=(3.5, 3.0))
    for i, (rot, camp, modo, taxa) in enumerate(FORMAS):
        y = len(FORMAS) - 1 - i
        linhas = [r for r in csv.DictReader(open(os.path.join(RES, camp, 'resultado.csv')))
                  if r['modo'] == modo]
        ok = sum(int(r['bloco_ok']) for r in linhas)
        for r in linhas:
            b = float(r['acerto_bits'])
            cheio = int(r['bloco_ok']) == 1
            ax.plot(b, y, 'o', ms=5, color=TEAL, markerfacecolor=TEAL if cheio else 'white',
                    markeredgewidth=1.0, alpha=0.9)
        txt = f'{ok}/{len(linhas)}' + (f'  {str(taxa).replace(".", ",")} B/s' if taxa else '')
        ax.text(101.5, y, txt, va='center', fontsize=7.5, color=TEAL)
        print(f'    {rot!r}: {ok}/{len(linhas)} blocos')
    ax.set_yticks(range(len(FORMAS)))
    ax.set_yticklabels([f[0] for f in reversed(FORMAS)])
    ax.set_xlim(50, 101)
    ax.set_xlabel('Bits certos por gravação (%)')
    ax.text(101.5, len(FORMAS) - 0.35, 'blocos  taxa', fontsize=7, color=CINZA)
    ax.grid(axis='x', color='0.9', lw=0.5)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    salva(fig, 'resultado-formas.png')


def sinc():
    fig, ax = plt.subplots(figsize=(3.5, 2.1))
    larg = 0.36
    for i, (rot, n, m, v) in enumerate(SINC):
        for dx, val, cor, nome in ((-larg / 2, m, CINZA, 'Malha'), (larg / 2, v, TEAL, 'Varreduras')):
            ax.bar(i + dx, 100 * val / n, larg, color=cor, label=nome if i == 0 else None)
            ax.text(i + dx, 100 * val / n + 2, f'{val}/{n}', ha='center', fontsize=7.5)
    ax.set_xticks(range(len(SINC)))
    ax.set_xticklabels([s[0] for s in SINC])
    ax.set_ylim(0, 115)
    ax.set_yticks([0, 50, 100])
    ax.set_ylabel('Blocos íntegros (%)')
    ax.legend(frameon=False, fontsize=7.5, loc='lower right', ncol=2, bbox_to_anchor=(1, 1))
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    salva(fig, 'resultado-sincronismo.png')


if __name__ == '__main__':
    formas()
    sinc()
