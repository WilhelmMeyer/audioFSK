"""Figura do artigo: as quatro formas, notebook para celular a 10 cm, modo manual.

100 baud, repeticao 3, 10 pacotes de 32 bytes (texto-320.txt), uma sessao por
forma. Numeros de RESUMO.md desta campanha (pacotes, tempo do primeiro envio a
ultima confirmacao, bits errados antes da correcao).

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
TEAL, BARRA, ERRO = '#0F5257', '#B9D7DA', '#C0392B'
plt.rcParams.update({'font.size': 8.5, 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
                     'ytick.labelsize': 8, 'axes.linewidth': 0.7, 'savefig.dpi': 300,
                     'figure.dpi': 300})

# (rotulo, pacotes entregues, tempo s, bits errados, bits lidos)
FORMAS = [
    ('2-FSK', 10, 350.9, 8, 29340),
    ('5×2-FSK\nvotada', 10, 355.2, 0, 29340),
    ('16-FSK', 10, 128.4, 0, 29340),
    ('5×2-FSK\nmulticanal', 10, 129.7, 4, 29400),
]
BYTES = 320

fig, ax = plt.subplots(figsize=(3.4, 2.4))
for x, (rot, pac, t, err, lidos) in enumerate(FORMAS):
    taxa = BYTES / t
    ax.bar(x, taxa, width=0.6, color=BARRA)
    ax.text(x, taxa + 0.06, f'{taxa:.2f}'.replace('.', ','), ha='center', fontsize=8, color=TEAL)
    ax.text(x, 0.12, f'{err}\nerrados', ha='center', fontsize=7.5, color=ERRO, linespacing=1.1)
    print(f'    {rot!r}: {pac}/10, {taxa:.2f} B/s, {err} de {lidos} bits errados')
ax.set_xticks(range(len(FORMAS)))
ax.set_xticklabels([f[0] for f in FORMAS])
ax.tick_params(axis='x', length=0)
ax.set_ylim(0, 3.0)
ax.set_yticks([0, 1, 2, 3])
ax.set_ylabel('Taxa efetiva (B/s)')
for lado in ('top', 'right'):
    ax.spines[lado].set_visible(False)
fig.tight_layout()
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[formas]', ', '.join(SAIDAS))
