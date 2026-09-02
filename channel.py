"""What this link does to each frequency, measured rather than assumed.

Every tone set in this project was picked from a band taken on faith --
700-2900 Hz, because that is where speech lives and small speakers are
supposed to work. Measured, the 700 Hz tone turned out to carry no
information at all: it arrived 0.8 dB *quieter* when transmitted than when
not. Five tones voting, and one of the votes was a coin.

A sweep answers the question directly. The far side plays a linear chirp,
this side records it, and the recording is compared against the noise the
room makes on its own. What comes out is a usable-frequency map: where the
speaker and the microphone actually deliver, and by how much they beat the
noise floor there. Tone frequencies belong on the peaks of that map.

    ./venv/bin/python capture.py --port /dev/ttyUSB0 --chirp --label sala
    ./venv/bin/python channel.py captures/<stem>.json
"""

import argparse
import sys

import numpy as np

import recording


def response(samples, fs, f0, f1, secs, bins=64):
    """Received level per frequency band, and the noise floor beside it.

    The sweep is linear in frequency and flat in amplitude, so time maps
    straight onto frequency: the band around f is measured in the slice of the
    recording where the sweep was passing through f. The noise floor comes
    from the tail after the sweep ends, which is the same room and the same
    microphone gain with nothing transmitted.
    """
    edges = np.linspace(f0, f1, bins + 1)
    swept = int(secs * fs)
    quiet = samples[swept + int(0.2 * fs):]

    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        a = int((lo - f0) / (f1 - f0) * swept)
        b = int((hi - f0) / (f1 - f0) * swept)
        seg = samples[a:b]
        if len(seg) < 64:
            continue
        # Measure only inside the band being swept: the microphone hears the
        # room's own noise across the whole spectrum at once, and counting it
        # all would bury a quiet band under noise it never actually competes
        # with.
        sig = _band_rms(seg, fs, lo, hi)
        noi = _band_rms(quiet, fs, lo, hi) if len(quiet) > 64 else 0.0
        out.append((0.5 * (lo + hi), sig, noi))
    return out


def _band_rms(x, fs, lo, hi):
    w = np.hanning(len(x))
    F = np.abs(np.fft.rfft(x * w)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / fs)
    m = (f >= lo) & (f < hi)
    return float(np.sqrt(F[m].mean())) if m.any() else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('capture', help="the .json of a --chirp capture")
    ap.add_argument('--bins', type=int, default=48)
    args = ap.parse_args()

    samples, _, meta = recording.load(args.capture)
    if meta.get('kind') != 'chirp':
        sys.exit(f"[channel] {args.capture} nao e uma varredura (--chirp)")
    f0, f1, secs = meta['chirp']

    rows = response(samples, meta['fs'], f0, f1, secs, args.bins)
    peak = max(r[1] for r in rows)

    print(f"varredura {f0:.0f}-{f1:.0f} Hz em {secs:.1f}s   "
          f"(nivel relativo ao melhor ponto; SNR vs a sala em silencio)\n")
    print("   freq |  nivel | SNR dB | ")
    best = []
    for f, sig, noi in rows:
        rel = 20 * np.log10(max(sig, 1e-30) / peak)
        snr = 20 * np.log10(max(sig, 1e-30) / max(noi, 1e-30))
        best.append((snr, f))
        bar = "#" * max(0, min(40, int(snr)))
        print(f"{f:7.0f} | {rel:6.1f} | {snr:6.1f} | {bar}")

    best.sort(reverse=True)
    print("\nmelhores faixas (maior SNR primeiro):")
    for snr, f in best[:12]:
        print(f"  {f:7.0f} Hz   {snr:5.1f} dB")


if __name__ == '__main__':
    main()
