"""Figura 1 do artigo: a resposta em frequencia medida, com os 16 tons da
16-FSK marcados sobre o pente.

Offline, como `channel.py` e `bench.py`: nao abre dispositivo e nao toca na
porta serial. Desenha com o escritor de PNG do `spectro.py`, numpy puro, porque
nao ha matplotlib na venv, e usa so ASCII nos rotulos, porque a fonte embutida
do `spectro.py` nao tem acentuada e um glifo faltando some em silencio.

**Os dois arquivos de entrada nao moram juntos, e e proposital dizer por que.**
O JSON autoritativo esta versionado em `resultados/03-CH-CHIRP-A2B/gravacao/`:
e ele que carrega `chirp`, `kind` e o resto do que a varredura precisa. O WAV
nao esta versionado em lugar nenhum (`.gitignore` ignora `*.wav`) e so existe
na maquina que gravou, em `captures/`. A gravacao local e float32; a copia que
foi pontuada em 2026-09-03 viajou pela serial em int16, entao a local e a
melhor das duas. O sidecar que veio junto dela nao serve: foi escrito por esta
maquina como ouvinte (`side: local`, `kind: room`) e nao sabe que aquilo era
uma varredura.

    ./venv/bin/python figura_canal.py \
        resultados/03-CH-CHIRP-A2B/gravacao/20260903-175426-ch-chirp-A2B.json \
        captures/20260903-175426-ch-chirp-A2B.wav \
        artigo/figuras/resposta-canal.png
"""
import argparse
import json

import numpy as np

import channel
import modem
import recording
from spectro import write_png, draw_text

BINS = 114                      # 300-6000 Hz => 50 Hz por bin, como diz o texto

W, H = 1100, 620
ESQ, DIR, TOPO, BASE = 92, 26, 52, 74
PX0, PX1 = ESQ, W - DIR
PY0, PY1 = TOPO, H - BASE

FUNDO = (255, 255, 255)
EIXO = (60, 60, 60)
GRADE = (222, 222, 222)
CURVA = (26, 74, 158)
BANDA = (238, 244, 252)
TOM = (200, 40, 40)
TEXTO = (35, 35, 35)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('meta', help="o .json da varredura (versionado em resultados/)")
    ap.add_argument('wav', help="o .wav da mesma gravacao (so local, em captures/)")
    ap.add_argument('saida')
    args = ap.parse_args()

    meta = json.loads(open(args.meta).read())
    if meta.get('kind') != 'chirp':
        raise SystemExit(f"[figura] {args.meta} nao e uma varredura")
    samples = recording.read_wav(args.wav)

    f0, f1, secs = meta['chirp']
    fs = meta['fs']
    start = channel.find_onset(samples, fs)
    rows = channel.response(samples[start:], fs, f0, f1, secs, BINS)
    pico = max(r[1] for r in rows)

    freq = np.array([r[0] for r in rows])
    niv = np.array([20 * np.log10(max(r[1], 1e-30) / pico) for r in rows])
    ymin, ymax = 5 * np.floor(niv.min() / 5.0), 0.0

    img = np.full((H, W, 3), FUNDO, dtype=np.uint8)
    px = lambda f: int(PX0 + (f - f0) / (f1 - f0) * (PX1 - PX0))
    py = lambda v: int(PY1 - (v - ymin) / (ymax - ymin) * (PY1 - PY0))

    # a faixa onde os tons foram colocados, atras de tudo
    img[PY0:PY1, px(550):px(3500)] = BANDA

    for f in range(1000, int(f1) + 1, 1000):
        img[PY0:PY1, px(f):px(f) + 1] = GRADE
        draw_text(img, px(f) - 14, PY1 + 10, str(f), TEXTO, 1)
    draw_text(img, (PX0 + PX1) // 2 - 24, PY1 + 30, 'f (Hz)', TEXTO, 2)

    for v in np.arange(ymin, ymax + 1, 10):
        img[py(v):py(v) + 1, PX0:PX1] = GRADE
        draw_text(img, PX0 - 46, py(v) - 3, '%d' % v, TEXTO, 1)
    draw_text(img, PX0 - 46, PY0 - 26, 'nivel relativo (dB)', TEXTO, 2)

    # os dezesseis tons, cada um sobre o ponto do pente em que caiu
    for t in modem.MARY_TONES:
        if not f0 <= t <= f1:
            continue
        x, y = px(t), py(float(np.interp(t, freq, niv)))
        img[y:PY1, x:x + 1] = TOM
        img[max(PY0, y - 3):y + 4, max(PX0, x - 3):x + 4] = TOM

    for i in range(len(freq) - 1):
        x0, y0, x1, y1 = px(freq[i]), py(niv[i]), px(freq[i + 1]), py(niv[i + 1])
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
            img[max(PY0, y - 1):min(PY1, y + 2), x:x + 1] = CURVA

    img[PY0:PY1, PX0:PX0 + 1] = EIXO
    img[PY0:PY1, PX1 - 1:PX1] = EIXO
    img[PY1:PY1 + 1, PX0:PX1] = EIXO
    img[PY0:PY0 + 1, PX0:PX1] = EIXO

    lx, ly = PX0 + 14, PY0 + 12
    img[ly + 3:ly + 5, lx:lx + 18] = CURVA
    draw_text(img, lx + 26, ly, 'resposta medida, bins de 50 Hz', TEXTO, 1)
    img[ly + 17:ly + 23, lx + 6:lx + 12] = TOM
    draw_text(img, lx + 26, ly + 16, 'os 16 tons da 16-FSK', TEXTO, 1)
    img[ly + 32:ly + 38, lx + 6:lx + 12] = BANDA
    draw_text(img, lx + 26, ly + 32, 'faixa 550-3500 Hz, onde os tons moram', TEXTO, 1)

    write_png(args.saida, img)

    viz = [float(np.interp(t, freq, niv)) for t in modem.MARY_TONES]
    print('%s  %dx%d' % (args.saida, W, H))
    print('nivel nos 16 tons: %.1f a %.1f dB (excursao %.1f dB)'
          % (min(viz), max(viz), max(viz) - min(viz)))


if __name__ == '__main__':
    main()
