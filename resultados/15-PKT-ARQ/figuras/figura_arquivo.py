"""Figura do artigo: a imagem enviada e a recebida pelo ar, lado a lado.

    ./venv/bin/python resultados/15-PKT-ARQ/figuras/figura_arquivo.py
"""
import hashlib
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
ARQ = os.path.join(os.path.dirname(AQUI), 'arquivo')
SAIDAS = (os.path.join(AQUI, 'arquivo-enviado-recebido.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'arquivo-enviado-recebido.png'))

plt.rcParams.update({'font.size': 8.5, 'savefig.dpi': 300, 'figure.dpi': 300})

fig, eixos = plt.subplots(1, 2, figsize=(3.4, 1.9))
for ax, (nome, titulo) in zip(eixos, (('testcard-original.bmp', '(a) enviada'),
                                      ('got-B2A.bmp', '(b) recebida pelo ar'))):
    p = os.path.join(ARQ, nome)
    ax.imshow(Image.open(p).convert('RGB'), interpolation='nearest')
    ax.set_title(titulo, fontsize=8.5)
    ax.set_xticks([]); ax.set_yticks([])
    print(nome, hashlib.md5(open(p, 'rb').read()).hexdigest())
fig.tight_layout()
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[arquivo]', ', '.join(SAIDAS))
