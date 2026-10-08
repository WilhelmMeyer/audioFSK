"""Mede um par alto-falante -> microfone tom a tom, nas 16 frequências do M-ary.

Toca uma sequência fixa (1 s de silêncio, depois os 16 tons de MARY_TONES, três
voltas, 0,30 s de tom e 0,10 s de pausa cada) e, do outro lado, grava com folga.
A pontuação acha o início da sequência por correlação com a referência e mede a
energia em cada frequência durante o próprio tom contra a mesma frequência no
silêncio inicial. Mediana das três voltas, como pede o CLAUDE.md: uma frequência
se mede mandando aquela frequência, não varrendo por ela.

Autocontido de propósito (não importa modem.py): roda copiado para a máquina
Windows, fora do repositório.

    python sonda.py play  --device "AL-1888" --gain 0.3
    python sonda.py rec   --device "Mic1" --seconds 28 --out x.wav
    python sonda.py score x.wav
"""
import argparse
import json
import sys

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import correlate

FS = 48000
TONES = (888, 1050, 1212, 1375, 1538, 1700, 1862, 2025,
         2188, 2350, 2512, 2675, 2838, 3000, 3162, 3325)
LEAD = 1.0
TONE = 0.30
PAUSE = 0.10
REPS = 3
TAIL = 0.5
FADE = 0.010


def sequence(gain=1.0):
    n_tone = int(TONE * FS)
    t = np.arange(n_tone) / FS
    ramp = np.ones(n_tone)
    k = int(FADE * FS)
    ramp[:k] = np.linspace(0, 1, k)
    ramp[-k:] = np.linspace(1, 0, k)
    parts = [np.zeros(int(LEAD * FS))]
    slots = []
    pos = int(LEAD * FS)
    for r in range(REPS):
        for f in TONES:
            parts.append(np.sin(2 * np.pi * f * t) * ramp)
            slots.append((r, f, pos))
            pos += n_tone
            parts.append(np.zeros(int(PAUSE * FS)))
            pos += int(PAUSE * FS)
    parts.append(np.zeros(int(TAIL * FS)))
    return (gain * np.concatenate(parts)).astype('float32'), slots


def find_device(name, kind):
    hits = [(i, d) for i, d in enumerate(sd.query_devices())
            if name in d['name'] and d['max_%s_channels' % kind] > 0
            and not d['name'].endswith('.monitor')]
    if not hits:
        sys.exit('nenhum dispositivo de %s com "%s"' % (kind, name))
    i, d = hits[0]
    print('%s: [%d] %s (%s)' % (kind, i, d['name'],
                                sd.query_hostapis(d['hostapi'])['name']), flush=True)
    return i


def band_power(x, f, half=25.0):
    w = np.hanning(len(x))
    X = np.abs(np.fft.rfft(x * w)) ** 2
    fr = np.fft.rfftfreq(len(x), 1 / FS)
    return X[(fr > f - half) & (fr < f + half)].sum()


def score(path):
    fs, y = wavfile.read(path)
    assert fs == FS, fs
    y = y.astype('float64')
    if y.ndim > 1:
        y = y[:, 0]
    if not np.any(y):
        sys.exit('gravação de zeros exatos: microfone ausente ou mudo, não silencioso')
    ref, slots = sequence()
    c = correlate(y, ref, mode='valid', method='fft')
    start = int(np.argmax(np.abs(c)))
    m = int(0.05 * FS)               # descarta 50 ms de cada borda do tom
    win = int(TONE * FS) - 2 * m
    floor_wins = [y[start + int(a * FS): start + int(a * FS) + win]
                  for a in (0.15, 0.40, 0.65)]
    out = {}
    for f in TONES:
        floor = np.median([band_power(w, f) for w in floor_wins])
        on = [band_power(y[start + p + m: start + p + m + win], f)
              for r, ff, p in slots if ff == f]
        out[f] = 10 * np.log10(np.median(on) / max(floor, 1e-30))
    seg = y[start: start + len(ref)]
    snr = np.array(list(out.values()))
    res = {
        'arquivo': path,
        'inicio_s': start / FS,
        'pico': float(np.abs(seg).max()),
        'rms_dbfs': float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)),
        'snr_db': {str(k): round(float(v), 1) for k, v in out.items()},
        'snr_min_db': round(float(snr.min()), 1),
        'snr_mediana_db': round(float(np.median(snr)), 1),
        'tons_abaixo_10db': int((snr < 10).sum()),
    }
    print(json.dumps(res, ensure_ascii=False))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('play', 'rec', 'score'))
    ap.add_argument('path', nargs='?')
    ap.add_argument('--device')
    ap.add_argument('--gain', type=float, default=0.3)
    ap.add_argument('--seconds', type=float, default=28.0)
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.cmd == 'play':
        dev = find_device(a.device, 'output')
        x, _ = sequence(a.gain)
        sd.play(x, FS, device=dev)
        sd.wait()
        print('tocou %.1f s' % (len(x) / FS), flush=True)
    elif a.cmd == 'rec':
        dev = find_device(a.device, 'input')
        y = sd.rec(int(a.seconds * FS), FS, channels=1, device=dev, dtype='float32')
        sd.wait()
        wavfile.write(a.out, FS, y[:, 0])
        print('gravou %s, pico %.3f' % (a.out, float(np.abs(y).max())), flush=True)
    else:
        score(a.path)


if __name__ == '__main__':
    main()
