"""Draw a capture as an image: time across, frequency up, energy as colour.

Numbers said the channel is a comb with deep nulls, and that per-tone error
rates run from 9% to 50%. A picture says *when*: whether a tone is weak all
the way through or dies in patches, whether the damage moves with time, and
whether the symbol grid is where the receiver thinks it is.

Two panels, and the second is the point:

  cru          each pixel is absolute energy in dB. Shows which tones are
               loud, which is what the detector currently rewards.
  contraste    each frequency row divided by its own median over the whole
               recording. Shows which tones *change* when they are
               transmitted -- which is what actually carries information. A
               row that is bright in the first panel and flat in the second
               is a tone arriving loud and saying nothing.

That difference is the hypothesis this tool exists to check: energy and
usefulness are not the same ranking, and the detector only sees the first.

No matplotlib here, for the same reason recording.py writes its own WAV: this
project has no plotting dependency and does not need one for a heat map.

    ./venv/bin/python spectro.py captures/<stem>.json -o /tmp/vista.png
"""

import argparse
import struct
import sys
import zlib

import numpy as np

import recording
from modem import MARY_TONES


def write_png(path, rgb):
    """Minimal 8-bit RGB PNG. `rgb` is (height, width, 3), row 0 at the top."""
    h, w, _ = rgb.shape
    raw = b''.join(b'\x00' + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        body = tag + data
        return (struct.pack('>I', len(data)) + body
                + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF))

    header = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    return open(path, 'wb').write(
        b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
        + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def colourise(v):
    """0..1 to a perceptually rising blue-green-yellow ramp.

    Monotone in lightness on purpose: a heat map whose colours brighten and
    dim in a cycle invents structure that is not in the data.
    """
    v = np.clip(v, 0.0, 1.0)
    r = np.clip(1.6 * v - 0.55, 0, 1)
    g = np.clip(1.45 * v - 0.13, 0, 1)
    b = np.clip(0.9 - 1.4 * np.abs(v - 0.28), 0, 1) + 0.25 * np.clip(v - 0.85, 0, 1)
    return (np.stack([r, g, np.clip(b, 0, 1)], axis=-1) * 255).astype(np.uint8)


def spectrogram(samples, fs, f_lo, f_hi, cols, rows, win=None):
    """Energy per (time, frequency) cell, as a rows-by-cols array in dB.

    `win` is the analysis length in samples and it is the whole trade: short
    enough and the symbols separate in time but the tones blur together in
    frequency, long enough and the reverse. One symbol's worth is the natural
    choice, since that is what the detector itself measures.
    """
    win = int(win) if win else max(256, int(len(samples) / cols))
    hop = max(1, (len(samples) - win) // max(cols - 1, 1))
    taper = np.hanning(win)
    freqs = np.linspace(f_lo, f_hi, rows)
    # Goertzel-style probe per row rather than a full FFT: the rows wanted are
    # a handful of frequencies, not the whole spectrum, and this keeps the
    # frequency axis exactly linear in what is asked for.
    n = np.arange(win)
    probe = np.exp(-2j * np.pi * np.outer(freqs, n) / fs) * taper

    out = np.zeros((rows, cols))
    for c in range(cols):
        a = c * hop
        seg = samples[a:a + win]
        if len(seg) < win:
            break
        out[:, c] = np.abs(probe @ seg) ** 2
    return 10 * np.log10(np.maximum(out, 1e-20))


def panel(db, mode, floor_db=45.0):
    """Map dB to 0..1, either absolutely or against each row's own median."""
    if mode == 'contraste':
        db = db - np.median(db, axis=1, keepdims=True)
        lo, hi = 0.0, max(np.percentile(db, 99.5), 6.0)
    else:
        hi = np.percentile(db, 99.5)
        lo = hi - floor_db
    return (db - lo) / max(hi - lo, 1e-9)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('capture', help="the .json of a capture")
    ap.add_argument('-o', '--out', default='espectro.png')
    ap.add_argument('--lo', type=float, default=600.0)
    ap.add_argument('--hi', type=float, default=3600.0)
    ap.add_argument('--cols', type=int, default=900)
    ap.add_argument('--rows', type=int, default=300)
    ap.add_argument('--from', dest='t0', type=float, default=0.0, help="segundos")
    ap.add_argument('--secs', type=float, default=None)
    ap.add_argument('--win', type=int, default=None,
                    help="janela de analise em amostras (408 = um simbolo mary)")
    args = ap.parse_args()

    samples, payload, meta = recording.load(args.capture)
    fs = meta['fs']
    a = int(args.t0 * fs)
    b = int((args.t0 + args.secs) * fs) if args.secs else len(samples)
    samples = samples[a:b]
    if len(samples) < 4096:
        sys.exit("[spectro] trecho curto demais")

    db = spectrogram(samples, fs, args.lo, args.hi, args.cols, args.rows, args.win)

    panels = [panel(db, 'cru'), panel(db, 'contraste')]
    sep = 6
    h = args.rows * len(panels) + sep * (len(panels) - 1)
    img = np.zeros((h, args.cols, 3), dtype=np.uint8)
    for i, p in enumerate(panels):
        top = i * (args.rows + sep)
        # Row 0 of the array is the lowest frequency, but row 0 of a PNG is the
        # top of the picture, so flip: frequency should rise upward.
        img[top:top + args.rows] = colourise(p)[::-1]

    # Mark the sixteen M-ary tones down the left edge, so a null is readable
    # as "that tone" rather than "somewhere around there".
    for f in MARY_TONES:
        if not args.lo <= f <= args.hi:
            continue
        r = int((f - args.lo) / (args.hi - args.lo) * (args.rows - 1))
        for i in range(len(panels)):
            y = i * (args.rows + sep) + (args.rows - 1 - r)
            img[y, :10] = (255, 255, 255)

    write_png(args.out, img)
    dur = len(samples) / fs
    print(f"[spectro] {args.out}  {args.cols}x{h}  "
          f"{dur:.1f}s, {args.lo:.0f}-{args.hi:.0f} Hz")
    print(f"[spectro] painel de cima: energia absoluta (o que o detector premia)")
    print(f"[spectro] painel de baixo: cada frequencia contra a propria mediana "
          f"(o que de fato carrega informacao)")


if __name__ == '__main__':
    main()
