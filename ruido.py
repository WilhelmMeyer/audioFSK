"""Record the room with nothing transmitting, and keep the recording.

Every other number in this project is a ratio against something this one
measures. A tone arriving at -30 dBFS means one thing in a quiet room and
nothing at all in a loud one, and until the floor is written down beside the
signal the two cases are indistinguishable in the log.

So this is the first test of a bench, and it deliberately sends nothing. It
opens the microphone, throws away the first moment while the stream settles,
records, and writes the same `recording.py` pair every other capture uses --
which means `spectro.py` draws it and the rest of the offline tools read it
without knowing it holds silence.

The per-band table is the part worth reading. A single rms hides the shape of
the noise, and the shape is what decides whether a layer is usable: a floor
that is flat costs every tone the same, while a floor with a hum at 120 Hz and
nothing above 2 kHz says the high tones are the ones with margin. The bands
here are the ones the modem actually uses.

    ./venv/bin/python ruido.py --device 26 --secs 10 --label lvl-base
"""

import argparse
import queue
import sys
import time

import numpy as np
import sounddevice as sd

import recording
from modem import MARY_TONES, MFSK_PAIRS

FS = 48000
BLOCK = 2048

# The bands are the modem's, not decades: what matters is the noise sitting
# where a tone has to be heard. The last one is above everything transmitted
# and exists as a control -- if it moves with the others the noise is
# broadband, if it does not the room has a source with a spectrum.
BANDS = [(50, 300), (300, 550), (550, 1200), (1200, 2000),
         (2000, 3000), (3000, 3600), (3600, 6000), (6000, 12000)]


def record(device, secs, settle):
    """Samples from the microphone, with the settling period already dropped.

    Through the callback API rather than a blocking read for the same reason
    `capture.py` uses it: the host APIs this project needs do not all offer a
    blocking one, and having two paths means the machine that most needs a
    recording is the one whose path was never exercised.
    """
    q = queue.Queue()

    def cb(indata, frames, time_info, status):
        if status:
            print(f"[ruido] {status}", file=sys.stderr)
        q.put(indata[:, 0].copy())

    with sd.InputStream(samplerate=FS, blocksize=BLOCK, channels=1,
                        dtype='float32', device=device, callback=cb):
        t0 = time.time()
        while time.time() - t0 < settle:
            try:
                q.get(timeout=0.5)
            except queue.Empty:
                pass
        got, want = [], int(secs * FS)
        n, dead = 0, 0
        while n < want:
            try:
                blk = q.get(timeout=2.0)
            except queue.Empty:
                sys.exit("[ruido] o dispositivo parou de entregar audio")
            # A source that goes away does not raise and does not stop the
            # callback: it keeps delivering blocks of exact zeros, which count
            # as samples and average into the floor as silence. Observed here
            # -- five seconds of room followed by five of nothing read as a
            # room 3 dB quieter than it is, and the only tell was the picture.
            # Exact zeros are not a quiet microphone, they are no microphone.
            if not np.any(blk):
                dead += len(blk)
                if dead > 0.2 * FS:
                    sys.exit(f"[ruido] a fonte parou de entregar sinal depois "
                             f"de {n / FS:.1f}s (blocos de zero exato). "
                             f"A medida seria mentira -- nada gravado.")
            else:
                dead = 0
            got.append(blk)
            n += len(blk)
    return np.concatenate(got)[:want]


def band_rms(samples, lo, hi):
    """Rms inside one band, by Goertzel-style probes rather than a filter.

    A filter would need state and a settling time of its own, and this is a
    one-shot measurement of a fixed buffer -- there is no stream to keep in
    step with.
    """
    n = min(len(samples), 8 * FS)
    seg = samples[:n] * np.hanning(n)
    spec = np.abs(np.fft.rfft(seg)) ** 2
    freqs = np.fft.rfftfreq(n, 1.0 / FS)
    sel = (freqs >= lo) & (freqs < hi)
    if not sel.any():
        return 0.0
    # Parseval, with the window's power gain divided back out, so the number
    # is comparable to the plain rms of the same samples.
    gain = np.mean(np.hanning(n) ** 2)
    return float(np.sqrt(2 * spec[sel].sum() / (n * n * gain)))


def dbfs(x):
    return -99.0 if x <= 1e-9 else 20 * np.log10(x)


def tone_floor(samples, tones, width=25.0):
    """The floor at each frequency the modem transmits on."""
    return [(f, band_rms(samples, f - width, f + width)) for f in tones]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--device', help="dispositivo de entrada (indice ou nome)")
    ap.add_argument('--secs', type=float, default=10.0)
    ap.add_argument('--settle', type=float, default=1.5,
                    help="segundos descartados no comeco, enquanto o stream assenta")
    ap.add_argument('--tones', choices=('mary', 'mfsk', 'nenhum'), default='mary',
                    help="mede tambem o piso em cada tom dessa camada")
    ap.add_argument('--out', default='captures')
    ap.add_argument('--label', default='ruido')
    ap.add_argument('--link', default='desconhecido',
                    help="como esta maquina ouve: interno, bluetooth, p2...")
    args = ap.parse_args()

    dev = args.device
    if dev is not None and dev.isdigit():
        dev = int(dev)

    print(f"[ruido] gravando {args.secs:.0f}s com NADA transmitindo "
          f"(descartando {args.settle:.1f}s de assentamento)")
    samples = record(dev, args.secs, args.settle)

    rms = float(np.sqrt(np.mean(samples ** 2)))
    peak = float(np.max(np.abs(samples)))
    stem = recording.save(args.out, samples, b'',
                          kind='ruido', mode='nenhum', fs=FS, label=args.label,
                          link=args.link, device=str(args.device),
                          secs=args.secs, rms=rms, peak=peak)

    print(f"\n[ruido] rms {rms:.6f} ({dbfs(rms):+.1f} dBFS)   "
          f"pico {peak:.6f} ({dbfs(peak):+.1f} dBFS)")
    print("\n  faixa            rms        dBFS")
    for lo, hi in BANDS:
        v = band_rms(samples, lo, hi)
        print(f"  {lo:5.0f}-{hi:5.0f} Hz  {v:.6f}  {dbfs(v):+7.1f}")

    if args.tones != 'nenhum':
        tones = (MARY_TONES if args.tones == 'mary'
                 else sorted(t for pair in MFSK_PAIRS for t in pair))
        print(f"\n  piso em cada tom {args.tones} (+-25 Hz)")
        for f, v in tone_floor(samples, tones):
            print(f"  {f:6.0f} Hz  {v:.6f}  {dbfs(v):+7.1f}")

    # `recording.save` returns the full path stem, not a bare name.
    print(f"\n[ruido] gravado em {stem}.wav")


if __name__ == '__main__':
    main()
