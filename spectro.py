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

Two windows, not the whole recording: at 100 baud a ten-second capture is a
thousand symbols, and a thousand symbols in nine hundred pixels is a texture,
not a reading. `--auto` writes one figure at the head of the burst, where
acquisition happens, and one in the middle of the coded body, where the link
is carrying something. Both are `--simbolos` wide, because what has to be
countable is symbols, not seconds.

Two clocks, and the choice is stated on the figure. `--relogio grade` freezes
the receiver's symbol clock on the transmitted grid, so the picture answers
"what did the air deliver". `--relogio livre` lets the early/late gate steer
as it does live, and answers "what did the receiver do". Drawing the ideal on
one and the decisions on the other -- which is what this did -- is two
references and disagrees even where the receiver is right.

No matplotlib here, for the same reason recording.py writes its own WAV: this
project has no plotting dependency and does not need one for a heat map.

    ./venv/bin/python spectro.py captures/<stem>.json --fundido --auto \
        --win 480 -o /tmp/vista.png
"""

import argparse
import struct
import sys
import zlib

import numpy as np

import fec
import recording
from modem import (MARY_TONES, MARY_BITS, MFSK_PAIRS, _GRAY, _UNGRAY,
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


def align_mary(samples, meta, want, coarse, sps):
    """Start of symbol 0 of `want`, in samples, plus how well it then agrees.

    `find_start` alone is not enough and the reason is specific: the frame
    opens with 120 symbols of two tones alternating, so its score saturates.
    A candidate offset 44 symbols late matches the preamble exactly as well as
    the true one -- measured on a capture that decodes every byte, the brute
    force landed 44 symbols late, and the ideal panel was then drawn against
    the wrong part of the payload. Symbols 0-60 agreed 100%, 120 onward agreed
    6%, which is chance for sixteen tones, and the picture showed red and
    green scattered independently on a recording where the receiver was right.

    So take the phase from the brute force and the *index* from the body,
    which is the half of the frame that is not periodic: demodulate on a
    frozen clock, slide the decision sequence against `want`, and keep the
    shift that agrees most. Then refine the phase once more at that index.
    """
    def score(start, period=None):
        d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                            gap=meta.get('gap', 0.0), steer=False,
                            skip=max(0, int(start)), period=period)
        dec = np.array([i for i, _c, _n in d._symbols(samples)], dtype=int)
        return dec

    w = np.asarray(want, dtype=int)
    dec = score(coarse)
    best = (-1, 0)
    # The decision stream may begin before or after symbol 0 of the frame,
    # so both directions of slide have to be tried.
    for shift in range(-len(w) + 8, len(dec) - 8):
        if shift >= 0:
            n = min(len(dec) - shift, len(w))
            hits = int(np.sum(dec[shift:shift + n] == w[:n]))
        else:
            n = min(len(dec), len(w) + shift)
            hits = int(np.sum(dec[:n] == w[-shift:-shift + n]))
        if n >= 40 and hits > best[0]:
            best = (hits, shift)
    # In both branches above the decision at index i sits at
    # `coarse + i*sps` and carries `want[i - shift]`, so symbol 0 of the frame
    # is `shift` symbols away from where the brute force stopped. Getting this
    # sign backwards moves the ideal panel twice as far wrong as leaving it
    # alone, and it still looks like a plausible picture.
    start = coarse + best[1] * sps

    # One more pass on the phase, now that the index is right. A quarter of a
    # symbol either way is enough: the coarse search already found the phase
    # to within its own 24-sample step, and anything larger would be a
    # different symbol.
    fine = (-1, start)
    for off in range(int(start - sps // 4), int(start + sps // 4) + 1, 24):
        if off < 0:
            continue
        dec = score(off)
        n = min(len(dec), len(w))
        hits = int(np.sum(dec[:n] == w[:n]))
        if hits > fine[0]:
            fine = (hits, off)
    hits, start = fine
    dec = score(start)
    n = min(len(dec), len(w))
    return int(start), hits, n


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


def mary_decisions(samples, meta, start, sps, clock='grade'):
    """Every decision as (sample position, tone index, symbol index).

    `clock='grade'` freezes the receiver's symbol clock on the transmitted
    grid found by `align_mary`, so decision k *is* symbol k and the picture
    answers "what did the air deliver". `clock='livre'` lets the early/late
    gate steer as it does live, and the symbol index is then read off where
    the window actually landed -- which answers the different question "what
    did the receiver do", and is where a timing collapse becomes visible.

    Two clocks because two questions, and conflating them is what the drawing
    did before: the ideal marks came from the rigid grid and the decisions
    from the free-running gate, so the two panels were two references and
    disagreed even where the receiver was right.
    """
    if clock == 'livre':
        d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                            gap=meta.get('gap', 0.0))
        out = []
        for idx, _c, _n in d._symbols(samples):
            k = int(round((d.last_window - start) / sps))
            out.append((d.last_window, idx, k))
        return out

    k0 = max(0, int(np.ceil(-start / sps)))
    skip = int(start + k0 * sps)
    d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                        gap=meta.get('gap', 0.0), steer=False, skip=skip)
    return [(skip + j * sps, idx, k0 + j)
            for j, (idx, _c, _n) in enumerate(d._symbols(samples))]


def agreement(decisions, want):
    """(matching, comparable) over the decisions that fall inside the frame."""
    ok = n = 0
    for _pos, idx, k in decisions:
        if 0 <= k < len(want):
            n += 1
            ok += int(want[k] == idx)
    return ok, n


def decided_panel(decisions, want, f_lo, f_hi, cols, rows, win, nsamp, sps,
                  want_mask=False):
    """What the demodulator concluded, marked at the position it concluded it.

    Correctness is judged by symbol *index*, which `mary_decisions` supplies,
    not by re-aligning the decision sequence here. The sequence alignment this
    used to do could only paper over a disagreement it had no way to explain:
    with the ideal panel on one clock and the decisions on another, a receiver
    that was right drew as a receiver that was wrong.

    Green where the decision matches what was sent, red where it does not,
    grey where the symbol falls outside the transmitted frame and there is
    nothing to compare it with -- said rather than guessed.
    """
    hop = max(1, (nsamp - win) // max(cols - 1, 1))
    img = np.zeros((rows, cols, 3))
    mask = np.zeros((rows, cols))
    half = max(1, int(rows * 26.0 / (f_hi - f_lo)))
    for pos, idx, k in decisions:
        f = MARY_TONES[idx]
        if not f_lo <= f <= f_hi:
            continue
        inside = 0 <= k < len(want)
        right = inside and want[k] == idx
        c0 = int((pos - win // 2) / hop)
        c1 = int((pos + sps - win // 2) / hop)
        r = int((f - f_lo) / (f_hi - f_lo) * (rows - 1))
        lo_r, hi_r = max(0, r - half), min(rows, r + half + 1)
        colour = ((0.15, 1.0, 0.35) if right
                  else (1.0, 0.15, 0.15) if inside else (0.5, 0.5, 0.5))
        for c in range(max(0, c0), min(cols, max(c1, c0 + 1))):
            img[lo_r:hi_r, c] = colour
            mask[lo_r:hi_r, c] = 1.0
    if want_mask:
        return mask
    return (img * 255).astype(np.uint8)


def nibble_label(v):
    """A symbol's four bits as one character: 0-9 then A-F."""
    return "0123456789ABCDEF"[v & 0xF]


def label_strip(width, decisions, want, sps, hop, win, scale=2):
    """Two rows of characters under the picture: what was sent, what was read.

    One glyph per symbol, because a symbol is four bits and four bits is what
    a symbol decides -- the same quantity `resultado.py` writes into
    `bits/<stem>.txt`, put under the drawing instead of beside it. On a coded
    capture that is a hex nibble and not a letter, and it has to be: the
    payload is convolutionally coded, interleaved and repeated, so no symbol
    corresponds to any character of the text. Labelling the text over the
    coded stream would be a picture asserting something that is not there.

    Characters would be the nicer label and are not available here: a coded
    capture is the only kind this drawing can compare against an ideal, and in
    one there is no byte to name under a symbol. What the text was, and what
    came out of the decoder, go in the caption strip instead, where they are
    statements about the whole block -- which is the level at which they are
    true.
    """
    rowh = 7 * scale + 4
    strip = np.zeros((2 * rowh + 10, width, 3), dtype=np.uint8)
    strip[:] = (14, 14, 18)
    draw_text(strip, 2, 3, "tx", (150, 150, 160), 1)
    draw_text(strip, 2, 3 + rowh, "rx", (150, 150, 160), 1)
    step = 6 * scale
    for pos, idx, k in decisions:
        c = int((pos + sps / 2 - win // 2) / hop) - 2 * scale
        if not 0 <= c < width - step:
            continue
        inside = 0 <= k < len(want)
        if inside:
            draw_text(strip, c, 3, nibble_label(_UNGRAY[want[k]]),
                      (230, 120, 120), scale)
        right = inside and want[k] == idx
        draw_text(strip, c, 3 + rowh, nibble_label(_UNGRAY[idx]),
                  (120, 230, 140) if right else (245, 120, 120), scale)
    return strip


# A five-by-seven bitmap font, drawn here rather than loaded, for the same
# reason recording.py writes its own WAV: this project has no font
# dependency and a heat map does not justify acquiring one. It covers the
# printable ASCII the labels need, upper and lower case *distinctly* --
# the payload alphabet is A-Za-z0-9, so folding case would make a wrong
# byte and a right one draw the same glyph, which is the one thing a
# label under a symbol must never do.
_FONT = {
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '\'': ("01000", "01000", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ',': ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    '@': ("01110", "10001", "10111", "10101", "10111", "10000", "01111"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    '\\': ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '^': ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    '~': ("00000", "00000", "01001", "10101", "10010", "00000", "00000"),
    '0': ("01110", "10011", "10101", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10101", "10011", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01111", "10000", "10000", "10000", "01111"),
    'd': ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01111"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "00000", "01111", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01101", "10011", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11110", "01000", "01000", "01001", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
}


def draw_text(img, x, y, text, colour, scale=2):
    """Stamp text into an RGB array. Unknown characters are skipped.

    Case is preserved. It used to be folded to upper, which was harmless while
    the only text was legends and fatal once bytes are labelled: `a` and `A`
    are different bytes and would have drawn identically.
    """
    for ch in text:
        glyph = _FONT.get(ch) or _FONT.get(ch.upper())
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


def caption_strip(width, lines, scale=1, pad=4):
    """A few lines of small text under the picture."""
    rowh = 7 * scale + 3
    strip = np.zeros((rowh * len(lines) + 2 * pad, width, 3), dtype=np.uint8)
    strip[:] = (14, 14, 18)
    for i, (text, colour) in enumerate(lines):
        draw_text(strip, pad, pad + i * rowh, text[:width // (6 * scale)],
                  colour, scale)
    return strip


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


def panel(db, mode, floor_db=None):
    """Map dB to 0..1, either absolutely or against each row's own median.

    The absolute panel takes its floor from the data, not from a fixed number
    of decibels below the peak, and that is a fix rather than a preference. A
    one-symbol window on this link spans about 36 dB from the 5th percentile
    to the 99.5th and only 19 dB from the median up; a 45 dB floor therefore
    sat *below* everything, mapped 64% of the cells above mid-scale, and drew
    a recording whose tone line is 15 dB clear of its own background as an
    even wash of noise. Measured on the capture that decodes every byte:
    64% of cells above mid-scale with the fixed floor, 3% with the floor at
    the 70th percentile -- and at 3% the line is visible.

    `floor_db`, when given, restores the old fixed-range behaviour, which the
    fused panel wants: there the background exists only to say whether a mark
    sits on a tone.
    """
    if mode == 'contraste':
        db = db - np.median(db, axis=1, keepdims=True)
        lo, hi = 0.0, max(np.percentile(db, 99.5), 6.0)
    elif floor_db is not None:
        hi = np.percentile(db, 99.5)
        lo = hi - floor_db
    else:
        hi = np.percentile(db, 99.9)
        lo = np.percentile(db, 70.0)
    return (db - lo) / max(hi - lo, 1e-9)


def render(args, samples_all, payload, meta, t0, secs, out_path, tag):
    """One figure over one window of the recording. Returns a report line."""
    fs = meta['fs']
    a = int(t0 * fs)
    b = int((t0 + secs) * fs) if secs else len(samples_all)
    a = max(0, min(a, max(0, len(samples_all) - 4096)))
    b = min(len(samples_all), max(b, a + 4096))
    samples = samples_all[a:b]

    db = spectrogram(samples, fs, args.lo, args.hi, args.cols, args.rows, args.win)
    win = int(args.win) if args.win else max(256, int(len(samples) / args.cols))
    hop = max(1, (len(samples) - win) // max(args.cols - 1, 1))

    measured = panel(db, 'contraste')
    absolute = panel(db, 'cru')
    tiles = [(colourise(absolute), 'cru'), (colourise(measured), 'contraste')]
    strips_top, strips_bottom = [], []
    report = ''

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
            start = args.start - a
        else:
            plan, tone_list = mfsk_plan(payload, meta)
            want = [tone_list.index(p[0]) for p in plan]
            start = args.start - a

        if is_mary:
            ideal = ideal_panel(want, start, fs, sps, tone_frac, args.lo,
                                args.hi, args.cols, args.rows, win, len(samples))
            decisions = mary_decisions(samples, meta, start, sps, args.relogio)
            ok, n = agreement(decisions, want)
            report = (f"{tag}: {ok}/{n} simbolos coincidem "
                      f"({100 * ok / max(n, 1):.1f}%) no relogio '{args.relogio}'")
        else:
            ideal = chord_panel([(start + k * sps, t) for k, t in enumerate(plan)],
                                fs, sps, tone_frac, args.lo, args.hi, args.cols,
                                args.rows, win, len(samples), 0)
            decisions = None
            report = f"{tag}: camada de acorde, sem contagem por simbolo"

        over = np.zeros((args.rows, args.cols, 3))
        over[..., 1] = np.clip(measured, 0, 1)
        over[..., 0] = ideal
        if is_mary:
            dec_mask = decided_panel(decisions, want, args.lo, args.hi, args.cols,
                                     args.rows, win, len(samples), sps,
                                     want_mask=True)
        else:
            dec_mask = chord_panel(mfsk_decided(samples, meta), fs, sps,
                                   tone_frac, args.lo, args.hi, args.cols,
                                   args.rows, win, len(samples), 0)
        if args.fundido:
            fused = blended(panel(db, 'cru', floor_db=28.0), ideal, dec_mask)
            fused = draw_grid(fused[::-1], start, sps, tone_frac, hop, win,
                              args.cols, args.rows, args.lo, args.hi,
                              tone_list)[::-1]
            tiles = [(colourise(absolute), 'espectro'), (fused, 'leitura')]
            strips_top = [legend(args.cols, [
                ((235, 40, 40), "IDEAL"),
                ((40, 235, 40), "LIDO"),
                ((235, 235, 40), "AMBOS"),
                ((120, 120, 120), "ESPECTRO"),
                ((110, 110, 135), "LIMITES"),
            ])]
            if is_mary:
                strips_bottom.append(
                    label_strip(args.cols, decisions, want, sps, hop, win))
            strips_bottom.append(caption_strip(args.cols, args.caption + [
                (report, (200, 200, 210))]))
        else:
            tiles.append(((over * 255).astype(np.uint8), 'sobreposto'))
            if is_mary:
                tiles.append((decided_panel(decisions, want, args.lo, args.hi,
                                            args.cols, args.rows, win,
                                            len(samples), sps),
                              'decidido (verde=certo, vermelho=errado)'))
            tiles.append((colourise(ideal), 'ideal'))

    sep = 6
    top = sum(len(x) for x in strips_top)
    bottom = sum(len(x) for x in strips_bottom)
    h = top + args.rows * len(tiles) + sep * (len(tiles) - 1) + bottom
    img = np.zeros((h, args.cols, 3), dtype=np.uint8)
    y = 0
    for strip in strips_top:
        img[y:y + len(strip)] = strip
        y += len(strip)
    for i, (tile, _name) in enumerate(tiles):
        t = top + i * (args.rows + sep)
        # Row 0 of the array is the lowest frequency, row 0 of a PNG is the top
        # of the picture: flip, so frequency rises upward.
        img[t:t + args.rows] = tile[::-1]
    y = top + args.rows * len(tiles) + sep * (len(tiles) - 1)
    for strip in strips_bottom:
        img[y:y + len(strip)] = strip
        y += len(strip)

    marks = (MARY_TONES if meta.get('mode') == 'mary'
             else sorted(t for pair in MFSK_PAIRS for t in pair))
    for f in marks:
        if not args.lo <= f <= args.hi:
            continue
        r = int((f - args.lo) / (args.hi - args.lo) * (args.rows - 1))
        for i in range(len(tiles)):
            yy = top + i * (args.rows + sep) + (args.rows - 1 - r)
            img[yy, :10] = (255, 255, 255)

    write_png(out_path, img)
    print(f"[spectro] {out_path}  {args.cols}x{h}  "
          f"{t0:.2f}-{t0 + len(samples) / fs:.2f}s  {report}")
    return report


def windows(meta, start, nsamp, symbols):
    """The two windows to draw, chosen from the frame rather than the clock.

    One at the head of the burst, opening a few symbols before the first
    symbol, because that is where acquisition happens and where a receiver
    that never locks shows it. One in the middle of the *coded body*, past the
    preamble, because that is where the link is carrying something. Both are
    `symbols` wide, so the width is a number of symbols the eye can count
    rather than a number of seconds that means something different at every
    baud rate.
    """
    fs = meta['fs']
    sps = int(fs / meta['baud'])
    pre = len(fec.preamble_bits('mary', symbol_bits=MARY_BITS)) // MARY_BITS
    secs = symbols * sps / fs
    total = nsamp / fs
    head = max(0.0, (start - 3 * sps) / fs)
    body_syms = max(0, int((nsamp - start) / sps) - pre)
    mid_sym = pre + max(0, body_syms // 2 - symbols // 2)
    mid = max(0.0, (start + mid_sym * sps) / fs)
    return [('inicio', min(head, max(0.0, total - secs)), secs),
            ('meio', min(mid, max(0.0, total - secs)), secs)]


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
    ap.add_argument('--auto', action='store_true',
                    help="duas janelas escolhidas pelo conteudo: o inicio da "
                         "rajada e o meio dos dados (escreve dois arquivos)")
    ap.add_argument('--simbolos', type=int, default=80,
                    help="largura de cada janela de --auto, em simbolos")
    ap.add_argument('--relogio', choices=['grade', 'livre'], default='grade',
                    help="'grade': decisoes no relogio transmitido, diz o que o "
                         "ar entregou. 'livre': o gate do receptor como ele roda "
                         "ao vivo, diz o que o receptor fez")
    args = ap.parse_args()

    samples, payload, meta = recording.load(args.capture)
    fs = meta['fs']
    args.caption = []
    args.start = 0

    if args.fundido or args.ideal:
        if meta.get('kind') != 'fec':
            sys.exit("[spectro] --ideal precisa de uma captura com --fec")
        sps = int(fs / meta['baud'])
        if meta.get('mode') == 'mary':
            want = tx_tone_indices(payload, meta.get('fec_repeat', 1))
            coarse, hits = find_start(samples, fs, sps,
                                      np.array(MARY_TONES, float), want)
            start, agree, ncomp = align_mary(samples, meta, want, coarse, sps)
            moved = (start - coarse) // sps
            print(f"[spectro] rajada em {start / fs:.3f}s "
                  f"(bruta {coarse / fs:.3f}s, corrigida em {moved:+d} simbolos); "
                  f"{agree}/{ncomp} simbolos batem = {100 * agree / max(ncomp, 1):.1f}%")
            args.start = start
            # An alignment this weak is not a picture, it is a guess. Say so on
            # the figure rather than drawing marks that look authoritative: a
            # figure is an assertion about a recording, and the one thing it
            # must not do is assert confidently what it could not establish.
            frac = agree / max(ncomp, 1)
            args.caption = [
                (f"tx: {payload[:40].decode('ascii', 'replace')}",
                 (230, 160, 160)),
                (f"alinhamento: {agree}/{ncomp} simbolos = {frac * 100:.1f}%"
                 + ("" if frac >= 0.35 else "  ALINHAMENTO DUVIDOSO"),
                 (220, 220, 120) if frac >= 0.35 else (255, 120, 120)),
            ]
        else:
            plan, _tones = mfsk_plan(payload, meta)
            start, hits = find_start_mfsk(samples, meta, plan, sps)
            args.start = start
            print(f"[spectro] rajada em {start / fs:.3f}s ({hits} acertos)")

    if args.auto:
        base = args.out[:-4] if args.out.endswith('.png') else args.out
        for tag, t0, secs in windows(meta, args.start, len(samples),
                                     args.simbolos):
            render(args, samples, payload, meta, t0, secs,
                   f"{base}-{tag}.png", tag)
        return

    render(args, samples, payload, meta, args.t0,
           args.secs, args.out, 'janela')


if __name__ == '__main__':
    main()
