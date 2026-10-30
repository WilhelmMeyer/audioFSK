"""Figura do artigo: as duas imagens recebidas pelo celular, pelo ar, cada uma conferida contra a enviada.

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
from PIL import Image, ImageChops

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(AQUI)))
ARQ = os.path.join(os.path.dirname(AQUI), 'arquivo')
SAIDAS = (os.path.join(AQUI, 'arquivo-enviado-recebido.png'),
          os.path.join(RAIZ, 'artigo', 'figuras', 'arquivo-enviado-recebido.png'))

plt.rcParams.update({'font.size': 8.5, 'savefig.dpi': 300, 'figure.dpi': 300})

PARES = (('if-logo-enviado.bmp', '../logo-rep1/20261030-160037-enlace-ouvinte-recebido.bin',
          '(a) logotipo do IF, 1270 B'),
         ('../../../figurinhas/bandeira-br-48.bmp',
          '../bandeira-embaralhada/20261030-154344-enlace-ouvinte-recebido.bin',
          '(b) bandeira, 934 B'))

imagens = []
for env, rec, titulo in PARES:
    enviado = open(os.path.join(ARQ, env), 'rb').read()
    recebido = open(os.path.join(ARQ, rec), 'rb').read()[:len(enviado)]
    assert recebido == enviado, f'{rec} difere do enviado'
    print(f'{titulo}: {len(enviado)} bytes, CRC-32 {zlib.crc32(enviado):08x} nos dois')
    img = Image.open(io.BytesIO(recebido)).convert('RGB')
    # so para exibir: tira a margem branca, que sem contorno faria o desenho parecer menor
    fundo = Image.new('RGB', img.size, (255, 255, 255))
    imagens.append((img.crop(ImageChops.difference(img, fundo).getbbox()), titulo))

# larguras proporcionais ao formato, para as duas ficarem com a mesma altura
fig, eixos = plt.subplots(1, 2, figsize=(3.4, 1.6), width_ratios=[i.width / i.height for i, _ in imagens])
for ax, (img, titulo) in zip(eixos, imagens):
    ax.imshow(img, interpolation='nearest')
    ax.set_title(titulo, fontsize=8)
    ax.axis('off')
fig.tight_layout()
for s in SAIDAS:
    fig.savefig(s, bbox_inches='tight')
print('[arquivo]', ', '.join(SAIDAS))
