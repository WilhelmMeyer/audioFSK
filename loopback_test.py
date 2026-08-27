"""End-to-end DSP test for both physical layers. No audio hardware needed.

The Bell 202 section is the original round trip. The MFSK section is judged
against the impairments actually measured on the two-machine acoustic link,
not against generic AWGN: a high-frequency tilt that pushed the 2300 Hz
content to 9.5% of nominal, the slow envelope an output limiter imposed, and
room reverberation. Those are the conditions the second physical layer exists
to survive, so those are the conditions it has to pass.
"""

import numpy as np

import xfer
from modem import (FSKModulator, FSKDemodulator,
                   MFSKModulator, MFSKDemodulator)

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


def main():
    test_bell202()
    test_mfsk()
    test_xfer()
    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    else:
        print("SUCCESS! All checks passed.")


if __name__ == "__main__":
    main()
