"""Ask the far machine for one pure tone, record it here, and report the margin.

Measure a frequency by sending that frequency. A chirp answers a different
question and has already answered it wrongly on this hardware -- it put 1700 Hz
at -27 dB, the worst point of the sweep, where a stepped tone at the same
frequency arrived at +50 dB. A sweep spends a few milliseconds per bin and any
transient in the room lands inside one of them; a held tone does not have that
problem.

What comes out is a margin, not a level: the rms inside a narrow band around
the tone, against the rms in that same band with nothing playing. That ratio is
the only form of the number that survives a change of microphone gain, and both
machines here have different gains.

Repetitions are taken and the **median** is reported, never the best. One noise
passing in the room lands in a single trial: taking the best hides it and taking
the worst invents a dead tone.

Serial and audio in one process on purpose, as in `capture.py`: the far side
starts playing the moment it is asked, so anything that has to be drained must
be drained before the request goes out, and that is only knowable from inside
the same process. Stop the local console first -- the port takes one owner.

    ./venv/bin/python tom.py --port /dev/ttyUSB0 --freq 1700 --trials 3
"""

import argparse
import queue
import sys
import time

import numpy as np
import sounddevice as sd

import recording
from ruido import band_rms, dbfs
from serial_link import Control, pack, unpack

FS = 48000
BLOCK = 2048


def talk(ctl, cmd, timeout=10.0, seq=[0]):
    """One command to the agent, its matching reply back. See `rcmd.py`."""
    seq[0] += 1
    want = str(seq[0])
    ctl.send(f"CMD {want} {pack(cmd)}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ctl.recv(timeout=max(0.05, deadline - time.time()))
        if line is None:
            break
        if not line.startswith("OK "):
            continue
        gseq, _, body = line[3:].partition(" ")
        if gseq == want:
            return unpack(body)
    return None


class Mic:
    """The input stream, with a queue the caller can drain on demand."""

    def __init__(self, device):
        self.q = queue.Queue()
        self.stream = sd.InputStream(samplerate=FS, blocksize=BLOCK, channels=1,
                                     dtype='float32', device=device,
                                     callback=self._cb)
        self.dead = 0

    def _cb(self, indata, frames, time_info, status):
        self.q.put(indata[:, 0].copy())

    def drain(self):
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                return

    def take(self, secs):
        got, want, n = [], int(secs * FS), 0
        while n < want:
            try:
                blk = self.q.get(timeout=2.0)
            except queue.Empty:
                sys.exit("[tom] o dispositivo parou de entregar audio")
            # Exact zeros are a source that went away, not a quiet room. See
            # `ruido.py` -- averaging them in produces a clean-looking lie.
            if not np.any(blk):
                self.dead += len(blk)
                if self.dead > 0.2 * FS:
                    sys.exit("[tom] a fonte parou de entregar sinal (zeros "
                             "exatos). Microfone mudo? `wpctl status`.")
            else:
                self.dead = 0
            got.append(blk)
            n += len(blk)
        return np.concatenate(got)[:want]


def reverse(ctl, args):
    """This machine plays, the far side measures with its own `meas`.

    The link has to work in both directions and this project has already had
    the case where it only worked in one -- and not for an acoustic reason.
    Neither direction can be deduced from the other here: the two ends have
    different speakers and different microphones.

    The far side reports through `console.py`'s `meas`, whose dB are not dBFS
    (an unnormalised FFT), so only the difference it prints is portable: the
    band against the wide-band level of the *same* window. That is the number
    compared against a silent baseline taken the same way.
    """
    out = args.out_device
    if out is not None and out.isdigit():
        out = int(out)

    print(f"[tom] {talk(ctl, 'mic on')}")
    time.sleep(1.5)                       # o mic da outra ponta enche o tail
    base = talk(ctl, f'meas {args.freq:.0f} 1.0')
    print(f"[tom] piso remoto: {base}")

    phase = 0.0
    playing = [False]

    def cb(outdata, frames, time_info, status):
        nonlocal phase
        if not playing[0]:
            outdata[:] = 0.0
            return
        n = np.arange(frames)
        outdata[:, 0] = 0.5 * np.sin(2 * np.pi * args.freq * (phase + n) / FS)
        phase += frames

    stream = sd.OutputStream(samplerate=FS, blocksize=BLOCK, channels=1,
                             dtype='float32', device=out, callback=cb)
    stream.start()
    time.sleep(0.5)
    rows = []
    try:
        for k in range(args.trials):
            playing[0] = True
            # Ask while the tone is still sounding: `meas` reads the tail the
            # far side has already buffered, so a request sent after the tone
            # stopped would measure the silence that followed it.
            time.sleep(args.secs * 0.7)
            reply = talk(ctl, f'meas {args.freq:.0f} 1.0')
            time.sleep(args.secs * 0.3)
            playing[0] = False
            print(f"[tom] trial {k + 1}/{args.trials}  {reply}")
            rows.append(reply)
            if k < args.trials - 1:
                time.sleep(args.gap)
    finally:
        playing[0] = False
        stream.stop()
        stream.close()
        talk(ctl, 'mic off')
        ctl._stop = True
        ctl.ser.close()

    def ratio(line):
        try:
            return float(line.split('razao')[1].split('dB')[0])
        except (IndexError, ValueError, AttributeError):
            return None

    vals = sorted(v for v in (ratio(r) for r in rows) if v is not None)
    if vals:
        b = ratio(base)
        med = vals[len(vals) // 2]
        print(f"\n[tom] razao banda/larga mediana: {med:+.1f} dB"
              + (f", piso {b:+.1f} dB, ganho {med - b:+.1f} dB" if b is not None else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', required=True, help="serial para a outra maquina")
    ap.add_argument('--sync-baud', type=int, default=115200)
    ap.add_argument('--device', help="entrada local (indice ou nome)")
    ap.add_argument('--freq', type=float, default=1700.0)
    ap.add_argument('--secs', type=float, default=3.0, help="duracao do tom")
    ap.add_argument('--trials', type=int, default=3)
    ap.add_argument('--gap', type=float, default=2.0, help="pausa entre trials")
    ap.add_argument('--width', type=float, default=25.0, help="meia-banda em Hz")
    ap.add_argument('--out', default='captures')
    ap.add_argument('--label', default='tom')
    ap.add_argument('--reverse', action='store_true',
                    help="inverte: esta maquina toca, a outra mede com `meas`")
    ap.add_argument('--out-device', help="saida local (indice ou nome), so com --reverse")
    args = ap.parse_args()

    dev = args.device
    if dev is not None and dev.isdigit():
        dev = int(dev)

    ctl = Control(args.port, args.sync_baud)
    time.sleep(0.3)
    if talk(ctl, 'ping') != 'pong':
        sys.exit("[tom] a outra maquina nao respondeu ao ping")

    if args.reverse:
        return reverse(ctl, args)

    mic = Mic(dev)
    mic.stream.start()
    time.sleep(1.0)                       # o stream assenta antes de qualquer medida

    lo, hi = args.freq - args.width, args.freq + args.width
    rows = []
    try:
        print(f"[tom] {talk(ctl, 'spk on')}")
        # The floor first and through the same path as the signal: a margin
        # against a floor measured on another day, at another gain, is not a
        # margin.
        mic.drain()
        quiet = mic.take(1.5)
        floor = band_rms(quiet, lo, hi)
        wide_floor = float(np.sqrt(np.mean(quiet ** 2)))
        print(f"[tom] piso em {args.freq:.0f} Hz: {dbfs(floor):+.1f} dBFS   "
              f"banda larga {dbfs(wide_floor):+.1f} dBFS")

        chunks = [quiet]
        for k in range(args.trials):
            # Drain BEFORE asking, never after: the far side starts playing on
            # receipt, so audio arriving during the serial round trip is
            # already the head of the burst.
            mic.drain()
            reply = talk(ctl, f'tonef {args.freq:.0f} {args.secs:.1f}')
            if reply is None:
                sys.exit("[tom] sem resposta ao tonef")
            seg = mic.take(args.secs + 0.3)
            chunks.append(seg)
            # Skip the first and last 15%: the far side's stream starts and
            # stops inside this window and neither edge is the tone.
            g = int(0.15 * len(seg))
            body = seg[g:len(seg) - g]
            band = band_rms(body, lo, hi)
            wide = float(np.sqrt(np.mean(body ** 2)))
            rows.append((band, wide, float(np.max(np.abs(body)))))
            print(f"[tom] trial {k + 1}/{args.trials}  "
                  f"tom {dbfs(band):+7.1f} dBFS   "
                  f"banda larga {dbfs(wide):+7.1f}   "
                  f"pico {rows[-1][2]:.3f}   "
                  f"margem {dbfs(band) - dbfs(floor):+6.1f} dB")
            if k < args.trials - 1:
                time.sleep(args.gap)
    finally:
        talk(ctl, 'spk off')
        mic.stream.stop()
        mic.stream.close()
        ctl._stop = True
        ctl.ser.close()

    bands = sorted(r[0] for r in rows)
    med = bands[len(bands) // 2]
    print(f"\n[tom] mediana em {args.freq:.0f} Hz: {dbfs(med):+.1f} dBFS, "
          f"margem sobre o piso {dbfs(med) - dbfs(floor):+.1f} dB "
          f"(espalhamento {dbfs(bands[-1]) - dbfs(bands[0]):.1f} dB)")

    stem = recording.save(args.out, np.concatenate(chunks), b'',
                          kind='tom', mode='nenhum', fs=FS, label=args.label,
                          freq=args.freq, secs=args.secs, trials=args.trials,
                          device=str(args.device),
                          floor=floor, floor_wide=wide_floor,
                          bands=[r[0] for r in rows],
                          wides=[r[1] for r in rows],
                          peaks=[r[2] for r in rows])
    print(f"[tom] gravado em {stem}.wav")


if __name__ == '__main__':
    main()
