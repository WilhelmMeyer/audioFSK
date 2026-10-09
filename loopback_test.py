"""End-to-end DSP test for both physical layers. No audio hardware needed.

The Bell 202 section is the original round trip. The MFSK section is judged
against the impairments actually measured on the two-machine acoustic link,
not against generic AWGN: a high-frequency tilt that pushed the 2300 Hz
content to 9.5% of nominal, the slow envelope an output limiter imposed, and
room reverberation. Those are the conditions the second physical layer exists
to survive, so those are the conditions it has to pass.
"""

import numpy as np

import distortion
import fec
import recording
import xfer
from modem import (FSKModulator, FSKDemodulator,
                   MFSKModulator, MFSKDemodulator, MFSK_PAIRS,
                   MaryModulator, MaryDemodulator, MARY_TONES, MARY_BITS,
                   _GRAY, ifk_tones, FSK2_TONES, FSK2_BITS, tone_layer,
                   chirp, find_chirp, find_chirp_pair, SYNC_CHIRP,
                   read_coded_frame)

FS = 48000

failures = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    if not ok:
        failures.append(name)


# --- channel impairments, measured on the real link ----------------------

def tilt(sig, db_at_2300=-16.0):
    """Progressive high-frequency loss, the dominant fault we measured."""
    spec = np.fft.rfft(sig)
    freq = np.fft.rfftfreq(len(sig), 1 / FS)
    gain_db = db_at_2300 * np.clip((freq - 1100.0) / 1200.0, 0.0, 2.0)
    return np.fft.irfft(spec * 10 ** (gain_db / 20.0), n=len(sig))


def reverb(sig, rt60_ms=80, seed=3):
    n = int(rt60_ms / 1000 * FS)
    rng = np.random.default_rng(seed)
    h = rng.normal(0, 1, n) * np.exp(-6.9 * np.arange(n) / n)
    h[0] += 3.0                      # direct path against the reverberant tail
    h /= np.abs(h).sum()
    return np.convolve(sig, h)[:len(sig)]


def limiter(sig, depth=0.6, period_s=2.0):
    t = np.arange(len(sig)) / FS
    return sig * (1.0 - depth * (0.5 + 0.5 * np.sin(2 * np.pi * t / period_s)))


def run(demod, audio, block=2048):
    out = bytearray()
    for i in range(0, len(audio), block):
        out += demod.demodulate(audio[i:i + block])
    return bytes(out)


# --- Bell 202 -------------------------------------------------------------

def test_bell202():
    print("\nBell 202 (1200 baud, delay-and-multiply):")
    mod = FSKModulator(fs=FS, baud=1200)
    preamble = bytes([0x55] * 10 + [0xFF])
    msg = preamble + b"Hello, FSK World! Testing 1 2 3."

    silence = np.zeros(int(FS * 0.1))
    tx = np.concatenate((silence, mod.modulate(msg), silence))
    rx = tx + np.random.default_rng(0).normal(0, 0.05, len(tx))

    got = run(FSKDemodulator(fs=FS, baud=1200, squelch=0.005), rx)
    check("round trip with noise", msg in got, f"{len(got)} bytes")


# --- MFSK -----------------------------------------------------------------

def mfsk_frame(mod, payload):
    """Alternating preamble, payload, trailing idle.

    The preamble alternates rather than idling because timing recovery needs
    transitions to lock onto. The trailing idle matters too: the demodulator
    keeps just over a symbol buffered, so without a tail the final byte stays
    stranded in it.
    """
    return np.concatenate([mod.modulate_bits([0, 1] * 40),
                           mod.modulate(payload),
                           mod.idle(4)])


def test_mfsk():
    print("\nMFSK (100 baud, energy ratio):")
    payload = b"Hello, FSK World! Testing 1 2 3."

    for name, impair in [
        ("clean", lambda s: s),
        ("noise 0.05", lambda s: s + np.random.default_rng(1).normal(0, 0.05, len(s))),
        ("tilt -16 dB (measured)", tilt),
        ("tilt + limiter", lambda s: limiter(tilt(s))),
        ("tilt + limiter + noise", lambda s: limiter(tilt(s)) + np.random.default_rng(2).normal(0, 0.05, len(s))),
    ]:
        mod = MFSKModulator(fs=FS, baud=100)
        got = run(MFSKDemodulator(fs=FS, baud=100), impair(mfsk_frame(mod, payload)))
        check(name, payload in got, f"{len(got)} bytes")

    # The guard interval trades reverberation tolerance against measurement
    # window: a longer guard skips more of the previous symbol's tail but
    # leaves fewer samples to measure, coarsening frequency resolution. The
    # default is 0.15 because that is what the real link measured best --
    # 99.5% of bytes and 4 packets of 4, against 82.7% and 1 of 4 at 0.35.
    # A room with a longer tail than ours wants the opposite, so both ends of
    # the trade are pinned here.
    print("\nMFSK guard/contrast trade-off under heavy reverberation:")
    mod = MFSKModulator(fs=FS, baud=100)
    audio = reverb(tilt(mfsk_frame(mod, payload)), 80)
    for guard, cmin, expect in ((0.35, 0.15, True),      # tuned for reverb
                                (0.15, 0.30, False)):    # the shipped default
        got = run(MFSKDemodulator(fs=FS, baud=100, guard=guard,
                                  contrast_min=cmin), audio)
        check(f"guard {guard} / contrast {cmin} "
              f"{'recovers' if expect else 'does not'}", (payload in got) == expect)

    # The whole point of the scheme: the decision is a ratio, so a change of
    # gain must not change a single bit. A sign test on an absolute threshold
    # cannot make this claim, which is why the Bell 202 path decodes nothing
    # once the level drops.
    print("\nMFSK amplitude independence:")
    mod = MFSKModulator(fs=FS, baud=100)
    frame = tilt(mfsk_frame(mod, payload))
    for scale in (2.0, 1.0, 0.1, 0.01, 0.001):
        got = run(MFSKDemodulator(fs=FS, baud=100), frame * scale)
        check(f"gain x{scale}", payload in got)

    # Same signal, same scaling, through the Bell 202 detector: this is the
    # failure the new layer was built to remove, so it is worth asserting that
    # it really is a property of the scheme and not of this particular capture.
    print("\nBell 202 under the same tilt, for contrast:")
    b_mod = FSKModulator(fs=FS, baud=1200)
    b_audio = tilt(b_mod.modulate(bytes([0x55]) * 20 + payload))
    b_got = run(FSKDemodulator(fs=FS, baud=1200, squelch=0.0005), b_audio)
    check("payload lost, as expected", payload not in b_got,
          f"{len(b_got)} bytes, payload absent")


def test_xfer():
    """Packets over MFSK, on the file that actually broke the link.

    testcard.bmp is the hard case on purpose: a BMP header and a 256-entry
    palette are mostly 0x00, and framed 8N1 that is nine identical bits per
    byte with no transition for timing recovery to hold onto.
    """
    print("\nxfer packets over MFSK:")
    try:
        with open("testcard.bmp", "rb") as fh:
            raw = fh.read()
    except OSError:
        print("  SKIP  testcard.bmp ausente")
        return

    parts = xfer.split(raw)

    def long_runs(data, limit=6):
        bits = []
        for byte in data:
            bits.append(0)
            bits += [(byte >> i) & 1 for i in range(8)]
            bits.append(1)
        n = run = 0
        for i in range(1, len(bits)):
            run = run + 1 if bits[i] == bits[i - 1] else 1
            if run == limit:
                n += 1
        return n

    def max_run(data):
        bits = []
        for byte in data:
            bits.append(0)
            bits += [(byte >> i) & 1 for i in range(8)]
            bits.append(1)
        best = run = 1
        for i in range(1, len(bits)):
            run = run + 1 if bits[i] == bits[i - 1] else 1
            best = max(best, run)
        return best

    # The sync byte is the one byte that cannot be scrambled -- the receiver
    # must recognise it to find anything -- so it has to be the most robust in
    # the packet. 0xFF was the least: nine identical bits, and the wire dropped
    # it outright, leaving the parser with no candidate at all.
    check("sync byte is transition-rich", max_run(bytes([xfer.SYNC])) <= 3,
          f"0x{xfer.SYNC:02x} -> max run {max_run(bytes([xfer.SYNC]))} "
          f"(0xff would be {max_run(b'\xff')})")

    plain = long_runs(raw)
    scrambled = long_runs(b"".join(xfer._scramble(p) for p in parts))
    check("scrambling breaks up long runs", scrambled < plain // 2,
          f"{plain} -> {scrambled} runs of 6+ identical bits")

    for name, impair in [("clean", lambda s: s),
                         ("tilt -16 dB", tilt),
                         ("tilt + reverb 40 ms", lambda s: reverb(tilt(s), 40))]:
        ok = 0
        sample = parts[:8]
        for seq, chunk in enumerate(sample):
            mod = MFSKModulator(fs=FS, baud=100)
            audio = impair(np.concatenate([mod.modulate(xfer.build(seq, chunk)),
                                           mod.idle(6)]))
            got = xfer.parse(run(MFSKDemodulator(fs=FS, baud=100), audio), want_seq=seq)
            if got and got[1] == chunk:
                ok += 1
        check(f"packets over {name}", ok == len(sample), f"{ok}/{len(sample)}")

    # The CRC has to reject damage, or a corrupt file passes as a good one.
    pkt = bytearray(xfer.build(3, parts[3]))
    pkt[len(xfer.LEAD) + 6] ^= 0x01
    check("CRC rejects a flipped bit", xfer.parse(bytes(pkt)) is None)
    check("CRC32 covers the whole file", xfer.crc32(raw) == xfer.crc32(b"".join(parts)))


def test_mary():
    """The M-ary layer, fed the way the live path feeds it: in blocks.

    Block size is the whole point of this test. A symbol is 480 samples and
    audio arrives in blocks of 2048, so a block holds 4.27 symbols and most
    blocks end in the middle of a byte. Decoding each block independently
    discards that half byte and shifts every byte after it by a nibble --
    which reads as a channel problem and is not one. Feeding the whole array
    in one call hides it completely, so the test must not do that.
    """
    print()
    print("M-ary (100 baud, 16 tons, 4 bits por simbolo):")
    msg = b"ola mary, como vai voce"
    mod = MaryModulator(fs=FS, baud=100)
    audio = np.concatenate([mod.modulate(msg), mod.idle(6)])

    # Several block sizes, none of them a whole number of symbols: the bug
    # this guards against only appears when a boundary falls mid-byte.
    for block in (2048, 1024, 777):
        demod = MaryDemodulator(fs=FS, baud=100)
        out = run(demod, audio, block=block)
        check(f"bloco {block} preserva o byte partido", msg in out,
              f"{out[:len(msg) + 4]!r}")

    # Amplitude must not change the answer: every decision in this layer is a
    # ratio, and the running floor is divided out before any comparison.
    for gain in (1.0, 0.05):
        demod = MaryDemodulator(fs=FS, baud=100)
        out = run(demod, audio * gain, block=2048)
        check(f"ganho x{gain}", msg in out)


def mary_fec_air(msg, repeat=2):
    """Exactly what console.py's fecsend puts on the air, in M-ary.

    Kept here rather than imported because console.py pulls in sounddevice,
    and this suite has to run on a machine with no PortAudio at all.
    """
    mod = MaryModulator(fs=FS, baud=100)
    pre = []
    for i in range(120):
        v = 0 if i % 2 else (1 << 4) - 1
        pre += [(v >> j) & 1 for j in range(4)]
    bits = fec.frame(msg, repeat=repeat)
    return np.concatenate([mod.modulate_bits(pre),
                           mod.modulate_bits(list(bits)),
                           mod.idle(6)])


def test_fec():
    """The error-corrected block, end to end, over the impaired channel.

    This is the path both machines now use to receive -- console.py's fecrx
    reads exactly these two steps, sync by correlation then Viterbi. The hard
    path is for eyeballing a link; this is the one that carries data.
    """
    print()
    print("FEC sobre M-ary (sync + Viterbi soft):")
    msg = b"ola mary, como vai voce"

    for name, chan in (("limpo", lambda a: a),
                       ("tilt -16 dB", tilt),
                       ("tilt + limiter", lambda a: limiter(tilt(a))),
                       ("ganho x0.02", lambda a: a * 0.02)):
        audio = chan(mary_fec_air(msg))
        demod = MaryDemodulator(fs=FS, baud=100)
        llr = np.concatenate([demod.demodulate_soft(audio[i:i + 2048])
                              for i in range(0, len(audio), 2048)])
        start = fec.find_sync(llr)
        got = b"" if start is None else fec.decode(llr[start:], len(msg), repeat=2)
        check(f"{name} decodifica o bloco", got == msg,
              "sync nao encontrado" if start is None else repr(got))


def mary_values(bits):
    bits = list(bits) + [0] * (-len(bits) % MARY_BITS)
    return [sum(b << j for j, b in enumerate(bits[i:i + MARY_BITS]))
            for i in range(0, len(bits), MARY_BITS)]


def measured_tail(sig, noise_db, seed, comb_db=6.0):
    """The tail measured on the B->A linear chain, plus a comb and noise.

    Each of the last four transmitted symbols is re-injected whole, one
    symbol later each time, at -14/-14/-15/-15 dB -- what 31 recordings showed
    of tones n-1..n-4 inside window n, about 14 dB under the current tone. A
    delayed copy rather than an exponential reverb, because the measured
    residue does not decay over those four symbols. The comb gives each tone
    its own gain, as the room does, and the noise sets the baseline error
    rate: on a clean channel both paths score zero and the test shows nothing.
    """
    rng = np.random.default_rng(seed)
    f = np.fft.rfftfreq(len(sig), 1 / FS)
    grid = np.arange(500.0, 4000.0, 81.25)
    h = 10 ** (np.interp(f, grid, rng.normal(0, comb_db, len(grid))) / 20)
    x = np.fft.irfft(np.fft.rfft(sig) * h, n=len(sig))
    y = x.copy()
    sps = FS // 100
    for k, db in enumerate((-14, -14, -15, -15), 1):
        y[k * sps:] += 10 ** (db / 20) * x[:-k * sps]
    return y + rng.normal(0, 10 ** (noise_db / 20), len(y))


def test_ifk():
    """IFK by repetition tone: never the previous symbol's tone.

    Round trip first, on a payload full of repeated nibbles so the repetition
    tone actually sounds and chains of it are exercised. Then the measured
    tail, scored at a frozen clock on the right offset: the share of symbols
    decided as the previous transmitted tone is what IFK exists to remove.
    """
    print()
    print("IFK (tom de repeticao) sobre M-ary:")
    msg = b"aa\x00\x00\x00\x00\xff\xff\x11\x11 ola ifk, zzzz"
    vals = mary_values([(b >> i) & 1 for b in msg for i in range(8)])
    tones = ifk_tones(vals)
    check("nunca o mesmo tom duas vezes seguidas",
          all(a != b for a, b in zip(tones, tones[1:])),
          f"{tones.count(16)} tons de repeticao em {len(tones)}")
    mod = MaryModulator(fs=FS, baud=100, ifk=True)
    audio = np.concatenate([mod.modulate(msg), mod.idle(6)])
    for block in (2048, 777):
        out = run(MaryDemodulator(fs=FS, baud=100, ifk=True), audio, block=block)
        check(f"ifk bloco {block} ida e volta", msg in out, f"{out[:len(msg) + 2]!r}")
    out = run(MaryDemodulator(fs=FS, baud=100), audio, block=2048)
    check("sem ifk no receptor nao le um transmissor com ifk", msg not in out)

    rng = np.random.default_rng(7)
    stats = {}
    for ifk in (False, True):
        stats[ifk] = np.zeros(5)
    for seed in range(6):
        payload = bytes(rng.integers(0, 256, 48).tolist())
        bits = fec.preamble_bits('mary', symbol_bits=MARY_BITS) + list(fec.frame(payload, repeat=1))
        vals = mary_values(bits)
        for ifk in (False, True):
            tx = ifk_tones(vals) if ifk else [_GRAY[v] for v in vals]
            mod = MaryModulator(fs=FS, baud=100, ifk=ifk)
            y = measured_tail(np.concatenate([mod.modulate_bits(bits), mod.idle(6)]),
                              6.0, 100 + seed)
            d = MaryDemodulator(fs=FS, baud=100, ifk=ifk, steer=False, skip=0)
            dec, dv, llr = [], [], []
            for i in range(0, len(y), 2048):
                for idx, _c, n in d._symbols(y[i:i + 2048]):
                    dec.append(idx)
                    dv.append(d.value)
            d = MaryDemodulator(fs=FS, baud=100, ifk=ifk, steer=False, skip=0)
            llr = np.concatenate([d.demodulate_soft(y[i:i + 2048])
                                  for i in range(0, len(y), 2048)])
            n = len(vals) - 1
            err = sum(dv[k] != vals[k] for k in range(1, len(vals)))
            prev = sum(dv[k] != vals[k] and dec[k] == tx[k - 1]
                       for k in range(1, len(vals)))
            hard = (llr[:len(bits)] > 0).astype(int)
            start = fec.find_sync(llr)
            ok = start is not None and fec.decode(llr[start:], 48, repeat=1) == payload
            stats[ifk] += (err / n, prev / n, np.mean(hard == np.array(bits)), ok, 1)
    for ifk in (False, True):
        s = stats[ifk]
        print(f"        ifk={'on ' if ifk else 'off'}: simbolos errados {s[0] / s[4]:.1%}, "
              f"no tom anterior {s[1] / s[4]:.1%}, bits antes do FEC {s[2] / s[4]:.1%}, "
              f"blocos {int(s[3])}/{int(s[4])}")
    off, on = stats[False], stats[True]
    check("cauda medida: ifk corta os erros no tom anterior", on[1] * 4 < off[1])
    check("cauda medida: ifk nao piora o erro de simbolo", on[0] <= off[0])
    check("cauda medida: ifk entrega os blocos", on[3] == on[4])


def fsk2_fec_air(msg, repeat=1, sweeps=False):
    """What console.py's fecsend puts on the air in `mode fsk2`.

    Built from the same pieces `_fec_frame` uses -- `fec.preamble_bits` at one
    bit per symbol, `fec.frame`, `idle(6)` -- because console.py cannot be
    imported here (sounddevice).
    """
    mod = MaryModulator(fs=FS, baud=100, **tone_layer('fsk2'))
    body = np.concatenate([
        mod.modulate_bits(fec.preamble_bits('mary', symbol_bits=FSK2_BITS)),
        mod.modulate_bits(list(fec.frame(msg, repeat=repeat))),
        mod.idle(6)])
    if not sweeps:
        return body
    lead = chirp(FS, *SYNC_CHIRP)
    hush = np.zeros(int(0.03 * FS))
    return np.concatenate([lead, hush, body, hush, lead])


def test_fsk2():
    """2-FSK on the M-ary machinery: two tones, one bit per symbol, 100 baud.

    The frame length is checked against `fec.frame_symbols` first, because the
    two-sweep period divides the measured interval by it: an idle tail of the
    wrong length (four bits per idle symbol, as the 16-tone tail is built)
    would be 18 extra symbols, a period 1.4% long -- inside the receiver's
    acceptance window, so accepted silently and wrong.
    """
    print()
    print(f"2-FSK com FEC (100 baud, tons {FSK2_TONES[0]}/{FSK2_TONES[1]} Hz, 1 bit por simbolo):")
    msg = bytes(range(48))
    for rep in (1, 2):
        n = len(fsk2_fec_air(msg, repeat=rep))
        want = fec.frame_symbols(len(msg), rep, FSK2_BITS) * 480
        check(f"quadro rep {rep} tem frame_symbols simbolos", n == want,
              f"{n} amostras, esperado {want}")

    text = b"ola fsk2, como vai voce"
    mod = MaryModulator(fs=FS, baud=100, **tone_layer('fsk2'))
    audio = np.concatenate([mod.modulate(text), mod.idle(6)])
    for block in (2048, 777):
        out = run(MaryDemodulator(fs=FS, baud=100, **tone_layer('fsk2')),
                  audio, block=block)
        check(f"bloco {block} ida e volta sem FEC", text in out,
              f"{out[:len(text) + 2]!r}")

    def soft_decode(audio, **kw):
        d = MaryDemodulator(fs=FS, baud=100, **tone_layer('fsk2'), **kw)
        llr = np.concatenate([d.demodulate_soft(audio[i:i + 2048])
                              for i in range(0, len(audio), 2048)])
        start = fec.find_sync(llr)
        return llr, (b"" if start is None
                     else fec.decode(llr[start:], len(msg), repeat=1))

    air = fsk2_fec_air(msg)
    for name, chan in (("limpo", lambda a: a),
                       ("tilt -16 dB", tilt),
                       ("tilt + limiter", lambda a: limiter(tilt(a))),
                       ("ganho x0.02", lambda a: a * 0.02),
                       ("cauda medida + pente + ruido",
                        lambda a: measured_tail(a, 6.0, 11))):
        llr, got = soft_decode(chan(air))
        check(f"{name} decodifica o bloco (rep 1)", got == msg,
              f"{len(llr)} valores")

    # The sweeps, read the way console.py's `fec_read` and align.py read
    # them: start from the first, period from the interval over the span
    # capture.py stamps.
    y = measured_tail(fsk2_fec_air(msg, sweeps=True), 0.0, 12)
    sps, hush = 480, int(0.03 * FS)
    span = fec.frame_symbols(len(msg), 1, FSK2_BITS) + 2 * hush / sps
    pair = find_chirp_pair(y, chirp(FS, *SYNC_CHIRP), min_gap=int(0.5 * span * sps))
    period = None if pair is None else (pair[1] - pair[0]) / span
    check("varreduras medem o periodo", period is not None
          and abs(period - 480) < 0.1, f"periodo {period}")
    if period is not None:
        skip = pair[0] + int(round(hush * period / sps))
        _llr, got = soft_decode(y, steer=False, skip=skip, period=period)
        check("varreduras decodificam o bloco", got == msg)

    try:
        MaryModulator(fs=FS, baud=100, ifk=True, **tone_layer('fsk2'))
        refused = False
    except ValueError:
        refused = True
    check("ifk recusado com 2 tons", refused)


def chord_fec_air(msg, repeat=1, parallel=False, sweeps=False):
    """What console.py's fecsend puts on the air in `mode mfsk`, voted or
    with `fecpar on`: the MFSK preamble, the coded frame, `idle(4)`, and the
    two sweeps with their silences when `syncsweep on`. Built from the same
    pieces `_fec_frame` uses, since console.py cannot be imported here."""
    k = len(MFSK_PAIRS)
    mod = MFSKModulator(fs=FS, baud=100, parallel=parallel)
    bits = (fec.frame_parallel(msg, k, repeat=repeat) if parallel
            else fec.frame(msg, repeat=repeat))
    body = np.concatenate([
        mod.modulate_bits(fec.preamble_bits('mfsk', npairs=k, parallel=parallel)),
        mod.modulate_bits(list(bits)),
        mod.idle(4)])
    if not sweeps:
        return body
    lead = chirp(FS, *SYNC_CHIRP)
    hush = np.zeros(int(0.03 * FS))
    return np.concatenate([lead, hush, body, hush, lead])


def resample_ppm(sig, ppm):
    """The far machine's crystal off by `ppm`: the same audio, played slower."""
    n = len(sig)
    t = np.arange(int(n * (1 + ppm * 1e-6))) / (1 + ppm * 1e-6)
    return np.interp(t, np.arange(n), sig)


def test_chord_sweeps():
    """The two sync sweeps on the 5x2 layers, voted and parallel.

    The frame length is checked against `fec.layer_frame_symbols` first,
    because the two-sweep period divides the measured interval by it -- and
    the tone layers' count, applied to these frames, is some forty symbols
    long for the voted one. Then the path actually taken is asserted, not just
    the block: on a channel with no clock skew the leading sweep alone at the
    nominal clock decodes too, so a wrong span would pass a decode-only test.
    The drift case is the one that tells them apart.
    """
    print()
    print("Varreduras nas camadas 5x2 (mfsk votada e paralela):")
    k = len(MFSK_PAIRS)
    sps, hush = 480, int(0.03 * FS)
    msg = b"ola mfsk, como vai voce"
    for par in (False, True):
        layer = 'mfsk-par' if par else 'mfsk'
        for rep in (1, 2):
            n = len(chord_fec_air(msg, rep, par))
            want = fec.layer_frame_symbols(layer, len(msg), rep, npairs=k) * sps
            check(f"{layer} rep {rep}: quadro tem layer_frame_symbols simbolos",
                  n == want, f"{n} amostras, esperado {want}")

    def make(par):
        return lambda **kw: MFSKDemodulator(fs=FS, baud=100, parallel=par, **kw)

    for par in (False, True):
        layer = 'mfsk-par' if par else 'mfsk'
        # "limpo" has exact digital silence in the hush on both sides of the
        # frame, which is the case where `_score` used to return two values.
        for name, chan in (("limpo", lambda a: a),
                           ("tilt + limiter + ruido", lambda a: limiter(tilt(a))
                            + np.random.default_rng(2).normal(0, 0.05, len(a))),
                           ("cauda medida + pente + ruido",
                            lambda a: measured_tail(a, -30.0, 11))):
            y = np.concatenate([np.zeros(4000),
                                chan(chord_fec_air(msg, 1, par, sweeps=True)),
                                np.zeros(6000)])
            got, _llr, how, period = read_coded_frame(
                y, make(par), len(msg), 1, layer, hush, float(sps), True,
                npairs=k, template=chirp(FS, *SYNC_CHIRP))
            check(f"{layer} {name}: duas varreduras, periodo ~480, decodifica",
                  how == 'pair' and period is not None and abs(period - sps) < 0.1
                  and got == msg, f"{how}, periodo {period}")
        # Not asserted: that a receiver expecting sweeps falls back to the gate
        # when none were sent. It does not, reliably, on any layer -- a frame
        # with no sweep still correlates with the template at 5-8x its median
        # here, and real plain recordings reach 46x against 21-97x for real
        # sweeps, so `find_chirp`'s threshold of 4 takes a false leading sweep.
        # Both ends agreeing (`b syncsweep on`, checked by capture.py and
        # recvfile.py) is what protects the link, not the fallback.

    # A far crystal 1000 ppm slow: over a 48-byte voted frame's 1285 symbols
    # that is 617 samples, more than a symbol -- the leading sweep alone at the
    # nominal clock walks off the frame, the pair measures the period and
    # stays on it. The gate tracks it too; no synthetic case was found where
    # the gate loses and the sweeps win, which on the air is the collapse the
    # sweeps insure against. The tone layers' count used as the span would be
    # tens of symbols long, a period several percent short, and refused.
    msg = bytes(range(48))
    y = np.concatenate([np.zeros(4000),
                        resample_ppm(chord_fec_air(msg, 1, False, sweeps=True), 1000),
                        np.zeros(6000)])
    y = y + np.random.default_rng(4).normal(0, 0.01, len(y))
    tmpl = chirp(FS, *SYNC_CHIRP)
    span = fec.sweep_span(len(msg), 1, None, hush, sps, layer='mfsk', npairs=k)
    pair = find_chirp_pair(y, tmpl, min_gap=int(0.5 * span * sps))
    period = None if pair is None else (pair[1] - pair[0]) / span
    check("deriva 1000 ppm: periodo medido ~480.48", period is not None
          and abs(period - 480.48) < 0.1, f"periodo {period}")
    wrong = fec.sweep_span(len(msg), 1, 1, hush, sps)   # tone-layer count, 1 bit
    check("contado como camada de tons o vao sairia errado em mais de 1%",
          pair is not None and abs((pair[1] - pair[0]) / wrong - 480.48) > 4.8,
          f"{len(msg)} bytes: {span:.0f} contra {wrong:.0f} simbolos")
    at = find_chirp(y, tmpl)
    lead = MFSKDemodulator(fs=FS, baud=100, steer=False, skip=at + hush)
    llr = np.concatenate([lead.demodulate_soft(y[i:i + 2048])
                          for i in range(0, len(y), 2048)])
    got_lead, _ = fec.decode_block(llr, len(msg), 1)
    got, _llr, how, _p = read_coded_frame(y, make(False), len(msg), 1, 'mfsk',
                                          hush, float(sps), True, npairs=k)
    check("deriva: so a primeira varredura perde, o par recupera",
          got_lead != msg and how == 'pair' and got == msg,
          f"primeira {'ok' if got_lead == msg else 'perdeu'}, par {how}")


def test_int16_transfer():
    """The wire format for bringing a capture back over the serial cable.

    On disk this project keeps 32-bit float because the capture *is* the
    measurement. On the cable that is format rather than information -- and it
    is the difference between 90 seconds and three minutes for one recording
    at 115200 baud. What this checks is the size, the exactness on the 16-bit
    grid, and that the error where it is not exact stays far under the room.
    """
    print()
    print("Transferencia de gravacao em 16 bits:")
    rng = np.random.default_rng(9)
    x = 0.3 * np.sin(2 * np.pi * 1700 * np.arange(48000) / 48000)
    x = x + 0.01 * rng.normal(0, 1, len(x))

    blob = recording.as_int16(x)
    check("metade do tamanho do float32", len(blob) == 2 * len(x),
          f"{len(blob)} bytes para {len(x)} amostras")

    back = recording.from_int16(blob)
    err = float(np.max(np.abs(back - x)))
    # One LSB of the 16-bit grid is -90 dBFS. The room this link lives in
    # measures about -73 dBFS, so the quantisation is 17 dB under the quietest
    # thing the microphone can hear -- which is why sending 16 bits is a
    # saving and not a loss.
    check("erro abaixo do piso da sala", err <= 1.0 / 32767 + 1e-12,
          f"{20 * np.log10(max(err, 1e-12)):.0f} dBFS contra -73 da sala")

    grid = np.round(x * 32767) / 32767
    check("exato para audio ja em 16 bits",
          np.array_equal(recording.from_int16(recording.as_int16(grid)), grid))


def clipped_scene(mod, ceiling, level=0.6, noise_db=-45.0, seed=3):
    """A capture-shaped recording: silence, burst, silence, plus a floor.

    Shaped like a capture on purpose. The metric subtracts the room's own
    out-of-band noise using the quiet stretches, so a bare burst with no
    silence around it cannot exercise the path that actually runs on a
    recording.
    """
    rng = np.random.default_rng(seed)
    b = mod.modulate_bits(list(rng.integers(0, 2, 600)))
    b = b / np.max(np.abs(b))
    b = np.clip(b * level, -ceiling, ceiling)
    sig = np.concatenate([np.zeros(2 * FS), b, np.zeros(2 * FS)])
    return sig + rng.normal(0, 10 ** (noise_db / 20), len(sig))


def test_distortion():
    """The out-of-band metric answers a question no other tool here asks: was
    the *transmitter* clipping? It found this on the real link only because a
    person heard the speaker."""
    print()
    print("Distorcao (energia que ninguem transmitiu):")
    tones = sorted(t for p in MFSK_PAIRS for t in p)
    mod = MFSKModulator(fs=FS, baud=100)
    base = distortion.baseline(mod, tones)

    clean = distortion.measure(clipped_scene(mod, 1.0), FS, tones)
    check("limpo nao acusa", not distortion.saturated(clean, base),
          f"excesso {clean['harm_clean'] - base['harm_rel']:+.1f} dB")

    hard = distortion.measure(clipped_scene(mod, 0.4), FS, tones)
    check("33% do pico ceifado acusa", distortion.saturated(hard, base),
          f"excesso {hard['harm_clean'] - base['harm_rel']:+.1f} dB")

    # The midpoint reading must not be sold as a detector: it does not move
    # under clipping, because the modulation's own sidebands already occupy
    # the midpoints at these baud rates.
    drift = abs(hard['imd_rel'] - clean['imd_rel'])
    check("entre-tons nao serve de detector", drift < 1.5,
          f"{drift:.1f} dB entre limpo e ceifado")

    # A ratio, so it must not follow the volume on a linear channel. Both
    # levels are kept clear of the noise floor: below it the out-of-band
    # excess is genuinely gone and the metric reports None, which is a
    # different statement from "no distortion" and is tested next.
    loud = distortion.measure(clipped_scene(mod, 1.0, level=0.6,
                                            noise_db=-60.0), FS, tones)
    soft = distortion.measure(clipped_scene(mod, 1.0, level=0.15,
                                            noise_db=-60.0), FS, tones)
    spread = abs(soft['harm_clean'] - loud['harm_clean'])
    check("nivel nao move o numero num canal linear", spread < 3.0,
          f"{spread:.1f} dB entre nivel 0.6 e 0.15")

    # Buried in the room, the honest answer is "nothing measurable", not a
    # number. Reporting one would be the failure this whole module exists to
    # avoid: a plausible figure standing in for an absent measurement.
    buried = distortion.measure(clipped_scene(mod, 1.0, level=0.02,
                                              noise_db=-35.0), FS, tones)
    check("sinal enterrado no ruido nao inventa numero",
          buried['harm_clean'] is None and not distortion.saturated(buried, base))


def main():
    test_bell202()
    test_mfsk()
    test_mary()
    test_fec()
    test_ifk()
    test_fsk2()
    test_chord_sweeps()
    test_xfer()
    test_int16_transfer()
    test_distortion()
    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    else:
        print("SUCCESS! All checks passed.")


if __name__ == "__main__":
    main()
