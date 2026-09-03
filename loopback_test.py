"""End-to-end DSP test for both physical layers. No audio hardware needed.

The Bell 202 section is the original round trip. The MFSK section is judged
against the impairments actually measured on the two-machine acoustic link,
not against generic AWGN: a high-frequency tilt that pushed the 2300 Hz
content to 9.5% of nominal, the slow envelope an output limiter imposed, and
room reverberation. Those are the conditions the second physical layer exists
to survive, so those are the conditions it has to pass.
"""

import numpy as np

import fec
import xfer
from modem import (FSKModulator, FSKDemodulator,
                   MFSKModulator, MFSKDemodulator,
                   MaryModulator, MaryDemodulator, ZeroWatch)

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


def test_mary_framing():
    """8N1 on the M-ary byte path: the start bit is what fixes nibble phase.

    Without framing a symbol carries four bits and nothing in the stream says
    which nibble is the low one, so beginning one symbol early or late hands
    over every byte with its nibbles swapped -- measured on a near-clean
    synthetic channel, the payload came back 4 times in 16, and never once
    when an odd number of symbols preceded it. That is the whole of the
    "sometimes readable, sometimes not" behaviour that reads like an unstable
    room.

    So the test is an offset sweep, whole symbols included. The frame carries
    the link-layer preamble `app.py` always sends, because that is what a
    receiver actually hears and because the start bit alone is not enough
    from a cold start: a receiver that opens on junk can lock one bit off a
    false start bit and stay there, since ASCII leaves bit 7 clear and the
    wrong stop bit then reads as a right one. The alternating preamble gives
    the framing machine a run of unambiguous edges before any payload. Run
    against the unframed modulator these same offsets scored 4 of 7.
    """
    print()
    print("M-ary 8N1 (fase de nibble):")
    msg = b"ola mary, como vai voce"
    mod = MaryModulator(fs=FS, baud=100)
    sps = mod.samples_per_symbol
    preamble = bytes([0x55] * 10 + [0xFF])
    audio = np.concatenate([mod.modulate(preamble + msg), mod.idle(6)])

    for label, pad in (("0 simbolos", 0), ("1 simbolo", sps),
                       ("2 simbolos", 2 * sps), ("3 simbolos", 3 * sps),
                       ("meio simbolo", sps // 2), ("123 amostras", 123)):
        demod = MaryDemodulator(fs=FS, baud=100)
        out = run(demod, np.concatenate([np.zeros(pad), audio]), block=2048)
        check(f"deslocado de {label}", msg in out, repr(out[-len(msg) - 3:]))

    # The tail must not manufacture bytes. Under 8N1 a run of 1-bits is an
    # idle line; the alternating tail this layer sent before it was framed
    # offers a start bit every other bit, appending invented bytes to every
    # send.
    demod = MaryDemodulator(fs=FS, baud=100)
    out = run(demod, audio, block=2048)
    tail = out[out.index(msg) + len(msg):]
    check("idle nao inventa bytes", len(tail) == 0, repr(tail))


def test_zero_watch():
    """Blocks of exact zeros are no microphone, not a quiet room.

    A source that goes away raises nothing and stops nothing: the callback
    keeps delivering zeros, which count as samples and average in as silence.
    Measured here, 5.5 s of room and 4.5 s of nothing reported a room 10 dB
    quieter than it is, with nothing erroring anywhere.
    """
    print()
    print("Guarda de blocos-zero:")
    w = ZeroWatch(fs=FS, secs=0.2)
    rng = np.random.default_rng(5)
    fired = [w.feed(rng.normal(0, 0.01, 2048)) for _ in range(5)]
    check("sala real nao dispara", not any(fired))

    # 0.2 s at 48 kHz is 9600 samples: five blocks of 2048 cross it.
    fired = [w.feed(np.zeros(2048)) for _ in range(8)]
    check("zeros disparam uma vez so", sum(fired) == 1 and fired[4],
          f"{fired}")
    check("estado morto se le", w.is_dead and w.dead_secs > 0.2,
          f"{w.dead_secs:.2f}s")

    # A source that comes back and goes again is reported again: one warning
    # per outage, not one per process.
    w.feed(rng.normal(0, 0.01, 2048))
    check("volta limpa o estado", not w.is_dead)
    check("segunda queda reporta de novo",
          sum(w.feed(np.zeros(2048)) for _ in range(8)) == 1)


def test_mfsk_frozen_clock():
    """`steer=False` on MFSK: the clock is given, not tracked.

    The early/late gate can only correct itself while the audio goes past, so
    an offset found afterwards -- by a sync sweep, or by a brute-force search
    offline -- cannot be applied to decisions already made. Freezing the clock
    is what lets the same audio be read a second time at a known offset, and
    it is the prerequisite for asking whether the sweeps buy anything on the
    chord layers. The M-ary layer has had this; this checks the chord layer
    now reads the same way.
    """
    print()
    print("MFSK relogio congelado (steer=False):")
    rng = np.random.default_rng(11)
    bits = list(rng.integers(0, 2, 200))
    mod = MFSKModulator(fs=FS, baud=100)
    sps = mod.samples_per_symbol
    pad = 700                              # not a whole number of symbols
    audio = np.concatenate([np.zeros(pad), mod.modulate_bits(bits),
                            mod.idle(4)])

    demod = MFSKDemodulator(fs=FS, baud=100, steer=False, skip=pad)
    llr = demod.demodulate_soft(audio)
    got = (llr[:len(bits)] > 0).astype(int)
    right = int(np.sum(got == np.array(bits)))
    check("no deslocamento certo le os bits", right == len(bits),
          f"{right}/{len(bits)}")

    # Same audio, same frozen clock, deliberately wrong offset: it must get
    # worse, or the parameter is not doing anything.
    bad = MFSKDemodulator(fs=FS, baud=100, steer=False, skip=pad + sps // 2)
    llr_bad = bad.demodulate_soft(audio)
    n = min(len(bits), len(llr_bad))
    wrong = int(np.sum((llr_bad[:n] > 0).astype(int) != np.array(bits[:n])))
    check("no deslocamento errado piora", wrong > 0, f"{wrong} bits errados")

    # A fractional period, the reason it is a float: two sync sweeps measure
    # the interval the symbols actually occupied, and rounding it to a whole
    # sample loses a quarter of a symbol over a 500-symbol block.
    frac = MFSKDemodulator(fs=FS, baud=100, steer=False, skip=pad,
                           period=float(sps))
    right2 = int(np.sum((frac.demodulate_soft(audio)[:len(bits)] > 0).astype(int)
                        == np.array(bits)))
    check("periodo fracionario aceito", right2 == len(bits),
          f"{right2}/{len(bits)}")


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


def main():
    test_bell202()
    test_mfsk()
    test_mary()
    test_mary_framing()
    test_mfsk_frozen_clock()
    test_zero_watch()
    test_fec()
    test_xfer()
    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    else:
        print("SUCCESS! All checks passed.")


if __name__ == "__main__":
    main()
