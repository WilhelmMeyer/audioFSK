"""Figura do artigo: as quatro formas, notebook para celular a 10 e a 30 cm, modo manual.

100 baud, repeticao 3, 10 pacotes de 32 bytes (texto-320.txt), uma sessao por
forma e distancia. Numeros de RESUMO.md desta campanha e de
H09-QUATRO-FORMAS-30CM/RESUMO.md (pacotes, tempo do primeiro envio a ultima
confirmacao, bits errados antes da correcao). Em 2-FSK a 30 cm entra a sessao refeita
(repeticao/2fsk/), escolha do autor; a primeira (4 retransmissoes) fica fora.

    ./venv/bin/python resultados/H09-QUATRO-FORMAS-10CM/figuras/figura_formas.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
SAIDAS = (os.path.join(AQUI, 'resultado-formas.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'resultado-formas.png'))
TEAL, BARRA = '#0F5257', '#B9D7DA'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})

# (rotulo, (tempo s, bits errados, bits lidos) a 10 cm, idem a 30 cm)
FORMAS = [
    ('2-FSK', (350.9, 8, 29340), (379.9, 150, 29340)),
    ('5×2-FSK\nvotada', (355.2, 0, 29340), (354.2, 11, 29340)),
    ('16-FSK', (128.4, 0, 29340), (148.9, 1071, 29340)),
    ('5×2-FSK\nmulticanal', (129.7, 4, 29400), (118.4, 3063, 29400)),
]
BYTES = 320
DIST = (('10 cm', BARRA, -0.19), ('30 cm', TEAL, 0.19))


def pct(err, lidos):
    p = 100 * err / lidos
    txt = '0' if err == 0 else (f'{p:.2f}' if p < 0.1 else f'{p:.1f}')
    return txt.replace('.', ',') + '%'


fig, (ax, ax2) = plt.subplots(2, 1, figsize=(3.7, 3.1), sharex=True)
for x, (rot, *medidas) in enumerate(FORMAS):
    for (nome, cor, dx), (t, err, lidos) in zip(DIST, medidas):
        taxa = BYTES / t
        ax.bar(x + dx, taxa, width=0.36, color=cor, label=nome if x == 0 else None)
        ax.text(x + dx, taxa + 0.05, f'{taxa:.1f}'.replace('.', ','), ha='center', fontsize=6.3)
        p = 100 * err / lidos
        ax2.bar(x + dx, p, width=0.36, color=cor)
        ax2.text(x + dx, p + 0.3, pct(err, lidos), ha='center', fontsize=5.8)
        print(f'    {rot!r} {nome}: {taxa:.2f} B/s, {err} de {lidos} bits errados')
ax.legend(frameon=False, fontsize=7.5, loc='upper left')
ax.set_ylim(0, 3.2)
ax.set_yticks([0, 1, 2, 3])
ax.set_ylabel('Taxa efetiva (B/s)')
ax2.set_xticks(range(len(FORMAS)))
ax2.set_xticklabels([f[0] for f in FORMAS])
ax2.set_ylim(0, 12.5)
ax2.set_yticks([0, 5, 10])
ax2.set_ylabel('Bits errados antes\nda correção (%)')
for eixo in (ax, ax2):
    eixo.tick_params(axis='x', length=0)
    for lado in ('top', 'right'):
        eixo.spines[lado].set_visible(False)
fig.tight_layout()
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[formas]', ', '.join(SAIDAS))
