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

import fec
import recording
from modem import MARY_TONES, MARY_BITS, _GRAY


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


def tx_tone_indices(payload, repeat):
    """The tone the transmitter sounded in each symbol slot, from the payload.

    Reconstructed rather than guessed: the preamble is a fixed alternation and
    the body is `fec.frame` of a payload the capture stored, so the intended
    picture is fully known. That is what makes an "ideal" panel meaningful
    instead of decorative -- it is the actual transmitted sequence, not an
    illustration of one.
    """
    pre = []
    for i in range(120):
        v = 0 if i % 2 else (1 << MARY_BITS) - 1
        pre += [(v >> j) & 1 for j in range(MARY_BITS)]
    bits = list(pre) + list(fec.frame(payload, repeat=repeat))
    return [_GRAY[sum(int(b) << j for j, b in enumerate(bits[i:i + MARY_BITS]))]
            for i in range(0, len(bits) - (MARY_BITS - 1), MARY_BITS)]


def find_start(samples, fs, sps, tones, want, guard=0.15, search=2.5):
    """Sample offset of the first symbol, by trying them all.

    Brute force on purpose. The receiver's own estimate is what is under
    examination here, so borrowing it would beg the question.
    """
    g = int(guard * sps)
    n = np.arange(g, sps)
    probe = np.exp(-2j * np.pi * np.outer(tones, n) / fs)
    best = (-1, 0)
    for off in range(0, int(search * fs), 24):
        ok = 0
        for k in range(min(60, len(want))):
            seg = samples[off + k * sps + g:off + k * sps + sps]
            if len(seg) != len(n):
                break
            ok += int(np.argmax(np.abs(probe @ seg) ** 2)) == want[k]
        if ok > best[0]:
            best = (ok, off)
    return best[1], best[0]


def ideal_panel(want, start, fs, sps, tone_frac, f_lo, f_hi, cols, rows, win, nsamp):
    """Where a perfect channel would put energy, on the same time axis.

    Built against the *same* column-to-sample mapping the measured panel uses,
    so a symbol that has slid in time shows up as a shift between the panels
    rather than being quietly re-aligned away.
    """
    hop = max(1, (nsamp - win) // max(cols - 1, 1))
    img = np.zeros((rows, cols))
    half = max(1, int(rows * 26.0 / (f_hi - f_lo)))     # ~26 Hz of thickness
    for c in range(cols):
        centre = c * hop + win // 2
        k = (centre - start) // sps
        if k < 0 or k >= len(want):
            continue
        if (centre - start) % sps > tone_frac * sps:    # the transmitted gap
            continue
        f = MARY_TONES[want[k]]
        if not f_lo <= f <= f_hi:
            continue
        r = int((f - f_lo) / (f_hi - f_lo) * (rows - 1))
        img[max(0, r - half):min(rows, r + half + 1), c] = 1.0
    return img


def decided_panel(samples, meta, want, start, f_lo, f_hi, cols, rows, win, nsamp):
    """What the demodulator concluded, symbol by symbol, and whether it was right.

    Drawn from the receiver's *own* timing rather than the rigid grid the ideal
    panel uses, because that timing is part of what is being shown: if the
    decisions drift away from the ideal marks along the picture, the drift is
    the finding.

    Green where the decision matches what was sent, red where it does not.
    """
    from modem import MaryDemodulator
    d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'], gap=meta.get('gap', 0.0))
    sps = d.samples_per_symbol

    gen = d._symbols(samples)
    marks = []                       # (sample position, tone index)
    total = len(samples)
    for idx, _c, _n in gen:
        # The generator has already advanced its buffer, so what it consumed up
        # to now places the window that produced this decision.
        pos = total - len(d.buf) - sps
        marks.append((pos, idx))

    # Judge correctness by aligning the decision *sequence* to the transmitted
    # one, not by sample position. The receiver's clock steers, so its symbol k
    # drifts away from the rigid grid; scoring by position marks correct
    # decisions wrong as soon as that drift exceeds half a symbol, which paints
    # a working stretch red.
    decided = [idx for _p, idx in marks]
    # The slice being drawn is usually a zoom into the middle of the burst, so
    # there are fewer decisions than transmitted symbols and the offset runs
    # the other way. Getting this backwards compares a mid-burst stretch
    # against the preamble and paints a 67%-correct passage almost entirely
    # red -- which is how this was found.
    if len(decided) <= len(want):
        off = max(range(0, len(want) - len(decided) + 1),
                  key=lambda o: sum(decided[k] == want[o + k]
                                    for k in range(len(decided))))
        shift = -off
    else:
        shift = max(range(0, len(decided) - len(want) + 1),
                    key=lambda sh: sum(decided[sh + k] == want[k]
                                       for k in range(len(want))))

    hop = max(1, (nsamp - win) // max(cols - 1, 1))
    img = np.zeros((rows, cols, 3))
    half = max(1, int(rows * 26.0 / (f_hi - f_lo)))
    for k, (pos, idx) in enumerate(marks):
        f = MARY_TONES[idx]
        if not f_lo <= f <= f_hi:
            continue
        slot = k - shift
        right = 0 <= slot < len(want) and want[slot] == idx
        c0 = int((pos - win // 2) / hop)
        c1 = int((pos + sps - win // 2) / hop)
        r = int((f - f_lo) / (f_hi - f_lo) * (rows - 1))
        for c in range(max(0, c0), min(cols, max(c1, c0 + 1))):
            img[max(0, r - half):min(rows, r + half + 1), c] = (
                (0.15, 1.0, 0.35) if right else (1.0, 0.15, 0.15))
    return (img * 255).astype(np.uint8)


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
    ap.add_argument('--ideal', action='store_true',
                    help="acrescenta o que um canal perfeito teria entregue, "
                         "e os dois sobrepostos, no mesmo eixo de tempo")
    args = ap.parse_args()

    samples, payload, meta = recording.load(args.capture)
    fs = meta['fs']
    full = samples
    a = int(args.t0 * fs)
    b = int((args.t0 + args.secs) * fs) if args.secs else len(samples)
    samples = samples[a:b]
    if len(samples) < 4096:
        sys.exit("[spectro] trecho curto demais")

    db = spectrogram(samples, fs, args.lo, args.hi, args.cols, args.rows, args.win)
    win = int(args.win) if args.win else max(256, int(len(samples) / args.cols))

    measured = panel(db, 'contraste')
    tiles = [(colourise(panel(db, 'cru')), 'cru'),
             (colourise(measured), 'contraste')]

    if args.ideal:
        if meta.get('mode') != 'mary' or meta.get('kind') != 'fec':
            sys.exit("[spectro] --ideal so vale para uma captura mary com --fec")
        want = tx_tone_indices(payload, meta.get('fec_repeat', 1))
        sps = int(fs / meta['baud'])
        tone_frac = 1.0 - meta.get('gap', 0.0)
        # Search the whole recording, not the slice being drawn: the burst
        # begins wherever it begins, and a zoom into the middle of it contains
        # no start to find.
        start, hits = find_start(full, fs, sps, np.array(MARY_TONES, float), want)
        print(f"[spectro] inicio da rajada em {start / fs:.3f}s "
              f"({hits}/60 simbolos batem no alinhamento)")
        start -= a
        ideal = ideal_panel(want, start, fs, sps, tone_frac, args.lo, args.hi,
                            args.cols, args.rows, win, len(samples))

        # Overlay: what arrived in green, what should have arrived in red.
        # Agreement turns yellow, so the eye reads the mismatch rather than
        # having to compare two pictures held apart.
        over = np.zeros((args.rows, args.cols, 3))
        over[..., 1] = np.clip(measured, 0, 1)
        over[..., 0] = ideal
        tiles.append(((over * 255).astype(np.uint8), 'sobreposto'))
        tiles.append((decided_panel(samples, meta, want, start, args.lo, args.hi,
                                    args.cols, args.rows, win, len(samples)),
                      'decidido (verde=certo, vermelho=errado)'))
        tiles.append((colourise(ideal), 'ideal'))

    sep = 6
    h = args.rows * len(tiles) + sep * (len(tiles) - 1)
    img = np.zeros((h, args.cols, 3), dtype=np.uint8)
    for i, (tile, _name) in enumerate(tiles):
        top = i * (args.rows + sep)
        # Row 0 of the array is the lowest frequency, but row 0 of a PNG is the
        # top of the picture, so flip: frequency should rise upward.
        img[top:top + args.rows] = tile[::-1]
    panels = tiles

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
    print("[spectro] paineis, de cima para baixo: " +
          ", ".join(name for _t, name in panels))
    if args.ideal:
        print("[spectro] no sobreposto: verde = o que chegou, vermelho = o que "
              "deveria ter chegado, amarelo = os dois")


if __name__ == '__main__':
    main()
