"""Figura do artigo: o logo enviado pelo computador e o recebido pelo celular, pelo ar.

O celular grava tudo o que recebeu na sessao num .bin: os 1270 bytes do BMP e,
depois, 23 bytes de texto digitados na mesma sessao. A figura usa os primeiros
1270 e confere que sao identicos ao enviado.

    ./venv/bin/python resultados/H08-ARQUIVO-CELULAR/figuras/figura_arquivo.py
"""
import io
import os
import zlib

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

enviado = open(os.path.join(ARQ, 'if-logo-enviado.bmp'), 'rb').read()
recebido = open(os.path.join(ARQ, '20261030-131754-enlace-ouvinte-recebido.bin'), 'rb').read()
recebido = recebido[:len(enviado)]
assert recebido == enviado, 'o recebido difere do enviado'
print(f'{len(enviado)} bytes, CRC-32 {zlib.crc32(enviado):08x} nos dois')

fig, eixos = plt.subplots(1, 2, figsize=(3.4, 1.9))
for ax, (dados, titulo) in zip(eixos, ((enviado, '(a) enviada pelo computador'),
                                       (recebido, '(b) recebida pelo celular'))):
    ax.imshow(Image.open(io.BytesIO(dados)).convert('RGB'), interpolation='nearest')
    ax.set_title(titulo, fontsize=8)
    ax.set_xticks([]); ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_color('0.75')
fig.tight_layout()
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[arquivo]', ', '.join(SAIDAS))
