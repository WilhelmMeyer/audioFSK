from PIL import Image, ImageDraw
W = 48; c = 10; g = 2; x0 = (W - (3*c + 2*g)) // 2; y0 = (W - (4*c + 3*g)) // 2
im = Image.new('P', (W, W), 0)
im.putpalette([255,255,255, 47,158,65, 205,25,30] + [0]*3*13)
d = ImageDraw.Draw(im)
for r in range(4):
    for k in range(3):
        x, y = x0 + k*(c+g), y0 + r*(c+g)
        if (r, k) == (0, 0):
            d.ellipse([x, y, x+c-1, y+c-1], fill=2)
        elif k < 2 or r in (0, 2):
            d.rectangle([x, y, x+c-1, y+c-1], fill=1)
im.save('if-logo-48.bmp', bits=4)
im.resize((480, 480), Image.NEAREST).convert('RGB').save('if-logo-previa.png')

import struct
def bmp4(im, path):
    w, h = im.size; px = im.load()
    linha = ((w * 4 + 31) // 32) * 4
    corpo = b''
    for y in range(h - 1, -1, -1):
        b = bytearray(linha)
        for x in range(w):
            b[x // 2] |= px[x, y] << (4 if x % 2 == 0 else 0)
        corpo += bytes(b)
    pal = im.getpalette()[:48]
    tab = b''.join(bytes([pal[3*i+2], pal[3*i+1], pal[3*i], 0]) for i in range(16))
    off = 14 + 40 + 64
    cab = b'BM' + struct.pack('<IHHI', off + len(corpo), 0, 0, off)
    info = struct.pack('<IiiHHIIiiII', 40, w, h, 1, 4, 0, len(corpo), 2835, 2835, 16, 0)
    open(path, 'wb').write(cab + info + tab + corpo)
bmp4(im, 'if-logo-48.bmp')
