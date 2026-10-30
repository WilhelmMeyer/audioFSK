"""Figura do capítulo 5: a tela do computador e a do celular, lado a lado, da
mesma altura. Junta as duas capturas desta pasta; não mede nada."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

aqui = Path(__file__).parent
a = Image.open(aqui / 'tela-computador.png').convert('RGB')
b = Image.open(aqui / 'tela-celular.png').convert('RGB')
b = b.crop((0, 0, b.width, int(b.height * .90)))     # sem a barra de gestos
H, G, T = 1300, 40, 70
a = a.resize((a.width * H // a.height, H), Image.LANCZOS)
b = b.resize((b.width * H // b.height, H), Image.LANCZOS)
f = Image.new('RGB', (a.width + G + b.width, H + T), 'white')
f.paste(a, (0, T))
f.paste(b, (a.width + G, T))
d = ImageDraw.Draw(f)
fonte = ImageFont.truetype('DejaVuSans.ttf', 44)
d.text((a.width // 2, T // 2), '(a)', fill='black', font=fonte, anchor='mm')
d.text((a.width + G + b.width // 2, T // 2), '(b)', fill='black', font=fonte, anchor='mm')
f.save(aqui / 'telas-visor-celular.png')
