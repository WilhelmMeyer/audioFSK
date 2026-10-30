"""Figurinha da bandeira do Brasil para mandar pelo ar: BMP de 4 bits, como o
logo do IF, porque um BMP sem compressão se forma linha a linha na tela de quem
recebe. Sem dependências além do Python.

    python figurinhas/bandeira_br.py
"""
import math
import struct
from pathlib import Path

L, A = 48, 34
VERDE, AMARELO, AZUL, BRANCO = 0, 1, 2, 3
PALETA = [(0, 151, 57), (254, 221, 0), (0, 39, 118), (255, 255, 255)] + [(0, 0, 0)] * 12


def cor(x, y):
    cx, cy = (L - 1) / 2, (A - 1) / 2
    if abs(x - cx) / 20.5 + abs(y - cy) / 13.5 > 1:   # o losango
        return VERDE
    r = math.hypot(x - cx, y - cy)
    if r > 7.6:
        return AMARELO
    # A faixa branca: um arco de círculo grande que cruza a esfera.
    d = math.hypot(x - (cx - 3), y - (cy + 13))
    if 12.2 < d < 14.2:
        return BRANCO
    return AZUL


def bmp():
    linha = (L + 1) // 2
    linha_alinhada = (linha + 3) // 4 * 4
    corpo = bytearray()
    for y in range(A - 1, -1, -1):   # de baixo para cima, como o formato pede
        px = [cor(x, y) for x in range(L)]
        b = bytes((px[i] << 4) | px[i + 1] for i in range(0, L, 2))
        corpo += b + bytes(linha_alinhada - linha)
    pal = b''.join(bytes((b, g, r, 0)) for r, g, b in PALETA)
    inicio = 14 + 40 + len(pal)
    return (b'BM' + struct.pack('<IHHI', inicio + len(corpo), 0, 0, inicio)
            + struct.pack('<IiiHHIIiiII', 40, L, A, 1, 4, 0, len(corpo), 2835, 2835, 16, 0)
            + pal + bytes(corpo))


if __name__ == '__main__':
    saida = Path(__file__).with_name('bandeira-br-48.bmp')
    saida.write_bytes(bmp())
    print(saida, saida.stat().st_size, 'bytes')
