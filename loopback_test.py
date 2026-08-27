"""End-to-end DSP test for both physical layers. No audio hardware needed.

The Bell 202 section is the original round trip. The MFSK section is judged
against the impairments actually measured on the two-machine acoustic link,
not against generic AWGN: a high-frequency tilt that pushed the 2300 Hz
content to 9.5% of nominal, the slow envelope an output limiter imposed, and
room reverberation. Those are the conditions the second physical layer exists
to survive, so those are the conditions it has to pass.
"""

import numpy as np

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
        ("tilt + reverb 80 ms", lambda s: reverb(tilt(s))),
        ("tilt + limiter + noise", lambda s: limiter(tilt(s)) + np.random.default_rng(2).normal(0, 0.05, len(s))),
    ]:
        mod = MFSKModulator(fs=FS, baud=100)
        got = run(MFSKDemodulator(fs=FS, baud=100), impair(mfsk_frame(mod, payload)))
        check(name, payload in got, f"{len(got)} bytes")

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


def main():
    test_bell202()
    test_mfsk()
    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
    else:
        print("SUCCESS! All checks passed.")


if __name__ == "__main__":
    main()
