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
from modem import (MARY_TONES, MARY_BITS, MFSK_PAIRS, _GRAY,
                   MFSKDemodulator, MaryDemodulator)


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


def mfsk_plan(payload, meta):
    """The tones sounding in each MFSK symbol, and the tone list to draw.

    Both readings of the chord layer are covered. Voting sends one bit per
    symbol and every pair sounds the member matching it, so five tones light
    together. Parallel sends one bit per pair, so the five tones are chosen
    independently and the pattern is arbitrary.
    """
    npairs = len(MFSK_PAIRS)
    par = bool(meta.get('parallel'))
    rep = meta.get('fec_repeat', 1)
    if par:
        pre = [0, 1] * 40 * npairs
        body = list(fec.frame_parallel(payload, npairs, repeat=rep))
    else:
        pre = [0, 1] * 40
        body = list(fec.frame(payload, repeat=rep))
    bits = [int(b) for b in pre + body]

    per_symbol = npairs if par else 1
    tones = sorted(t for pair in MFSK_PAIRS for t in pair)
    plan = []
    for i in range(0, len(bits) - per_symbol + 1, per_symbol):
        chunk = bits[i:i + per_symbol]
        if par:
            plan.append([MFSK_PAIRS[k][chunk[k]] for k in range(npairs)])
        else:
            plan.append([MFSK_PAIRS[k][chunk[0]] for k in range(npairs)])
    return plan, tones


def mfsk_decided(samples, meta):
    """What the MFSK receiver concluded, as (window position, tones)."""
    npairs = len(MFSK_PAIRS)
    par = bool(meta.get('parallel'))
    d = MFSKDemodulator(fs=meta['fs'], baud=meta['baud'], parallel=par)
    out = []
    for bit, _c, llr in d._symbols(samples):
        if par:
            # In parallel the soft value is one number per pair; its sign is
            # that pair's bit, which is the only place the per-pair decision
            # survives.
            bits = [1 if v > 0 else 0 for v in np.atleast_1d(llr)]
        else:
            bits = [bit] * npairs
        out.append((d.last_window,
                    [MFSK_PAIRS[k][bits[k]] for k in range(npairs)]))
    return out


def tx_tone_indices(payload, repeat):
    """The tone the transmitter sounded in each symbol slot, from the payload.

    Reconstructed rather than guessed: the preamble is a fixed alternation and
    the body is `fec.frame` of a payload the capture stored, so the intended
    picture is fully known. That is what makes an "ideal" panel meaningful
    instead of decorative -- it is the actual transmitted sequence, not an
    illustration of one.
    """
    pre = fec.preamble_bits('mary', symbol_bits=MARY_BITS)
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


def decided_panel(samples, meta, want, start, f_lo, f_hi, cols, rows, win, nsamp,
                  want_mask=False):
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

    marks = []                       # (sample position, tone index)
    for idx, _c, _n in d._symbols(samples):
        # Ask the demodulator where it measured, rather than inferring it from
        # how much buffer is left. The gate measures at an offset inside the
        # buffer and then consumes a different amount, so the inference is off
        # by up to a quarter of a symbol -- enough to draw an aligned receiver
        # as a misaligned one.
        marks.append((d.last_window, idx))

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
    mask = np.zeros((rows, cols))
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
        lo_r, hi_r = max(0, r - half), min(rows, r + half + 1)
        for c in range(max(0, c0), min(cols, max(c1, c0 + 1))):
            img[lo_r:hi_r, c] = (0.15, 1.0, 0.35) if right else (1.0, 0.15, 0.15)
            mask[lo_r:hi_r, c] = 1.0
    if want_mask:
        return mask
    return (img * 255).astype(np.uint8)


# A five-by-seven bitmap font, only the letters the legends need. A picture
# whose colours have to be explained in prose elsewhere stops being a picture,
# and pulling in a font library to write eight words would cost more than
# drawing them.
_FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_text(img, x, y, text, colour, scale=2):
    """Stamp uppercase text into an RGB array. Unknown characters are skipped."""
    for ch in text.upper():
        glyph = _FONT.get(ch)
        if glyph is None:
            x += 6 * scale
            continue
        for ry, row in enumerate(glyph):
            for rx, on in enumerate(row):
                if on != '1':
                    continue
                y0, x0 = y + ry * scale, x + rx * scale
                img[y0:y0 + scale, x0:x0 + scale] = colour
        x += 6 * scale
    return x


def legend(width, entries, scale=2, pad=8):
    """A strip of colour swatches with their meanings, to sit above a panel."""
    h = 7 * scale + 2 * pad
    strip = np.zeros((h, width, 3), dtype=np.uint8)
    strip[:] = (18, 18, 22)
    x = pad
    for colour, text in entries:
        sw = 7 * scale
        strip[pad:pad + sw, x:x + sw] = colour
        x += sw + 5 * scale
        x = draw_text(strip, x, pad, text, (235, 235, 235), scale)
        x += 7 * scale
    return strip


def draw_grid(img, start, sps, tone_frac, hop, win, cols, rows,
              f_lo=None, f_hi=None, tone_list=None):
    """Faint dashed verticals where each symbol is expected to begin and end.

    Without them the eye has no ruler: a mark drawn slightly left of where it
    belongs looks like a mark, not like a mark that is late. With the grid the
    timing error reads directly off the picture -- which is the whole reason
    this measurement was worth taking.

    Dashed rather than solid, and dim rather than bright, because the grid is
    the reference and not the finding. A solid line across a heat map competes
    with the data for attention and wins.
    """
    # One line per symbol only while the symbols are far enough apart to read
    # as lines. Below about twelve pixels the dashes merge into a wall that
    # hides the data they exist to place, so thin them out and say by how much
    # in the caption. Observed at 7.5 px per symbol: the grid was the picture.
    px = sps / hop
    every = max(1, int(np.ceil(16.0 / max(px, 1e-9))))
    k = 0
    while True:
        p = start + k * sps
        c = int((p - win // 2) / hop)
        if c >= cols:
            break
        draw = (k % every == 0)
        k += 1
        if c < 0 or not draw:
            continue
        for y in range(0, rows, 6):          # o tracejado
            img[y:y + 3, c] = np.maximum(img[y:y + 3, c], (78, 78, 96))
        if tone_frac >= 1.0:
            continue
        # Where the tone is meant to stop and the transmitted gap begins.
        ce = int((p + tone_frac * sps - win // 2) / hop)
        if 0 <= ce < cols:
            for y in range(3, rows, 6):
                img[y:y + 2, ce] = np.maximum(img[y:y + 2, ce], (58, 58, 72))

    # Horizontal dashes halfway between neighbouring tones: the frequency
    # boundary the detector is implicitly drawing when it takes an argmax.
    # Energy that crosses one of these lines is energy being counted for the
    # wrong tone, which is the failure the error histogram measures and this
    # makes visible.
    if f_lo is not None and f_hi is not None:
        tones = sorted(tone_list if tone_list is not None else MARY_TONES)
        for a, b in zip(tones[:-1], tones[1:]):
            fm = 0.5 * (a + b)
            if not f_lo <= fm <= f_hi:
                continue
            y = int((fm - f_lo) / (f_hi - f_lo) * (rows - 1))
            for x in range(0, cols, 7):
                img[y, x:x + 3] = np.maximum(img[y, x:x + 3], (72, 72, 88))
    return img


def blended(background, ideal, decided):
    """Everything on one picture, the overlays added rather than blended.

    The two marks go in separate channels -- what should have been heard in
    red, what the receiver concluded in green -- so where they coincide the
    channels literally sum to yellow. Nothing is invented for the overlap: the
    colour of agreement is the sum of the colours of its parts, which is the
    only mapping that stays honest when one mark is present and the other is
    not.

    The spectrogram sits underneath in grey and deliberately dim. It is
    context, not a third claim, and at full strength it drowns the marks it
    exists to place.

    `background` must be the *absolute* panel, never the contrast one. Contrast
    divides each frequency row by its own median over the recording, so a tone
    that is on for a long stretch -- the preamble is 120 symbols of two tones
    alternating -- raises its own median and disappears. Observed: the whole
    preamble drew as empty black while the data half drew normally, which reads
    as a dead channel and is an artefact of the normalisation.
    """
    bg = 0.42 * np.clip(background, 0, 1)
    img = np.stack([bg, bg, bg], axis=-1)
    img[..., 0] += ideal
    img[..., 1] += decided
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def chord_panel(events, fs, sps, tone_frac, f_lo, f_hi, cols, rows, win,
                nsamp, shift=0):
    """Mark several tones per symbol, for the layers that sound chords.

    `events` is (sample position, list of frequencies). The M-ary panels take a
    single tone index because that layer sounds one tone; here five sound at
    once and the picture has to say so, or the ideal would look like a fifth of
    what was transmitted.
    """
    hop = max(1, (nsamp - win) // max(cols - 1, 1))
    img = np.zeros((rows, cols))
    half = max(1, int(rows * 22.0 / (f_hi - f_lo)))
    for pos, freqs in events:
        p = pos - shift
        c0 = int((p - win // 2) / hop)
        c1 = int((p + tone_frac * sps - win // 2) / hop)
        for f in freqs:
            if not f_lo <= f <= f_hi:
                continue
            r = int((f - f_lo) / (f_hi - f_lo) * (rows - 1))
            for c in range(max(0, c0), min(cols, max(c1, c0 + 1))):
                img[max(0, r - half):min(rows, r + half + 1), c] = 1.0
    return img


def find_start_mfsk(samples, meta, plan, sps, search=2.5):
    """Where the chord burst begins, by trying offsets against known symbols."""
    npairs = len(MFSK_PAIRS)
    tones = np.array(sorted(t for pair in MFSK_PAIRS for t in pair), float)
    guard = int(0.15 * sps)
    n = np.arange(guard, sps)
    probe = np.exp(-2j * np.pi * np.outer(tones, n) / meta['fs'])
    best = (-1, 0)
    for off in range(0, int(search * meta['fs']), 24):
        ok = 0
        for k in range(min(60, len(plan))):
            seg = samples[off + k * sps + guard:off + k * sps + sps]
            if len(seg) != len(n):
                break
            e = np.abs(probe @ seg) ** 2
            top = set(tones[np.argsort(e)[-npairs:]])
            ok += len(top & set(plan[k]))
        if ok > best[0]:
            best = (ok, off)
    return best[1], best[0]


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
    ap.add_argument('--fundido', action='store_true',
                    help="uma imagem so: espectro ao fundo, ideal e interpretado "
                         "somados por canal (implica --ideal)")
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
    absolute = panel(db, 'cru')
    tiles = [(colourise(absolute), 'cru'),
             (colourise(measured), 'contraste')]

    legend_strip = None
    if args.fundido:
        args.ideal = True
    is_mary = meta.get('mode') == 'mary'
    if args.ideal:
        if meta.get('kind') != 'fec':
            sys.exit("[spectro] --ideal precisa de uma captura com --fec")
        sps = int(fs / meta['baud'])
        tone_frac = 1.0 - meta.get('gap', 0.0)
        if is_mary:
            want = tx_tone_indices(payload, meta.get('fec_repeat', 1))
            tone_list = list(MARY_TONES)
        else:
            plan, tone_list = mfsk_plan(payload, meta)
            # The chord layers decide a bit, not a tone, so alignment is
            # scored on bits: which pair sounded is a consequence, not the
            # thing being recovered.
            want = [tone_list.index(p[0]) for p in plan]
        # Search the whole recording, not the slice being drawn: the burst
        # begins wherever it begins, and a zoom into the middle of it contains
        # no start to find.
        if is_mary:
            start, hits = find_start(full, fs, sps, np.array(MARY_TONES, float),
                                     want)
        else:
            start, hits = find_start_mfsk(full, meta, plan, sps)
        print(f"[spectro] inicio da rajada em {start / fs:.3f}s "
              f"({hits} acertos de tom no alinhamento)")
        start -= a
        if is_mary:
            ideal = ideal_panel(want, start, fs, sps, tone_frac, args.lo,
                                args.hi, args.cols, args.rows, win, len(samples))
        else:
            # Positions are absolute in the whole recording; the drawing is of
            # a slice starting at sample `a`, so that is the only shift.
            ideal = chord_panel([(start + k * sps, t)
                                 for k, t in enumerate(plan)],
                                fs, sps, tone_frac, args.lo, args.hi, args.cols,
                                args.rows, win, len(samples), a)

        # Overlay: what arrived in green, what should have arrived in red.
        # Agreement turns yellow, so the eye reads the mismatch rather than
        # having to compare two pictures held apart.
        over = np.zeros((args.rows, args.cols, 3))
        over[..., 1] = np.clip(measured, 0, 1)
        over[..., 0] = ideal
        if is_mary:
            dec_mask = decided_panel(samples, meta, want, start, args.lo,
                                     args.hi, args.cols, args.rows, win,
                                     len(samples), want_mask=True)
        else:
            dec_mask = chord_panel(mfsk_decided(samples, meta), fs, sps,
                                   tone_frac, args.lo, args.hi, args.cols,
                                   args.rows, win, len(samples), 0)
        if args.fundido:
            hop = max(1, (len(samples) - win) // max(args.cols - 1, 1))
            # A tighter dynamic range under the marks than in the panel
            # above it: the top panel is there to show the noise floor, the
            # bottom one to show whether a mark sits on a tone, and 45 dB of
            # floor renders as grey fog that the marks have to fight.
            fused = blended(panel(db, 'cru', floor_db=28.0), ideal, dec_mask)
            fused = draw_grid(fused[::-1], start, sps, tone_frac, hop, win,
                              args.cols, args.rows, args.lo, args.hi,
                              tone_list)[::-1]
            # Two panels, and the top one carries no annotation on purpose.
            # Every mark on the lower panel is an assertion this code is
            # making about the recording; the upper one is the recording. Kept
            # side by side, a mark that does not sit on any energy is visibly
            # a claim about nothing, which is exactly the failure a single
            # annotated picture hides.
            tiles = [(colourise(absolute), 'espectro'),
                     (fused,
                      'leitura: vermelho=ideal, verde=interpretado, '
                      'amarelo=os dois, cinza=espectro real, '
                      'tracejado=grade de simbolo esperada')]
            legend_strip = legend(args.cols, [
                ((235, 40, 40), "IDEAL"),
                ((40, 235, 40), "LIDO"),
                ((235, 235, 40), "AMBOS"),
                ((120, 120, 120), "ESPECTRO"),
                ((110, 110, 135), "LIMITES"),
            ])
        else:
            tiles.append(((over * 255).astype(np.uint8), 'sobreposto'))
            tiles.append((decided_panel(samples, meta, want, start, args.lo,
                                        args.hi, args.cols, args.rows, win,
                                        len(samples)),
                          'decidido (verde=certo, vermelho=errado)'))
            tiles.append((colourise(ideal), 'ideal'))

    strip = legend_strip if args.ideal and args.fundido else None
    sep = 6
    top0 = len(strip) if strip is not None else 0
    h = top0 + args.rows * len(tiles) + sep * (len(tiles) - 1)
    img = np.zeros((h, args.cols, 3), dtype=np.uint8)
    if strip is not None:
        img[:top0] = strip
    for i, (tile, _name) in enumerate(tiles):
        top = top0 + i * (args.rows + sep)
        # Row 0 of the array is the lowest frequency, but row 0 of a PNG is the
        # top of the picture, so flip: frequency should rise upward.
        img[top:top + args.rows] = tile[::-1]
    panels = tiles

    # Mark the layer's own tones down the left edge, so a null is readable as
    # "that tone" rather than "somewhere around there". Which tones those are
    # depends on the capture: the chord layers and the M-ary one do not share a
    # single frequency, and marking the wrong set would put the ticks where
    # nothing was ever transmitted.
    marks = (MARY_TONES if meta.get('mode') == 'mary'
             else sorted(t for pair in MFSK_PAIRS for t in pair))
    for f in marks:
        if not args.lo <= f <= args.hi:
            continue
        r = int((f - args.lo) / (args.hi - args.lo) * (args.rows - 1))
        for i in range(len(panels)):
            y = top0 + i * (args.rows + sep) + (args.rows - 1 - r)
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
