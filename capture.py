"""Record the far machine transmitting a known payload, and keep the audio.

Every demodulator idea tried so far was judged by sending bytes over the air
and looking at what came back. That measures the idea and the room at the same
time, and the room does not hold still: a chair moves, the volume drifts, and
two runs of the same code disagree. Worse, it costs a round trip with a second
machine to test a change to a single `if`.

So capture once and keep it. A recording is a fixed channel. Ten ideas can be
scored against the same eight seconds of real reverberation, and the numbers
are comparable because the audio is literally identical. `bench.py` does the
scoring; this only collects.

The far side needs nothing new -- it answers the `console.py --role agent`
command table it is already running. Stop the local console first, though:
the serial port takes one owner.

    ./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mfsk --label caixa-pc
"""

import argparse
import queue
import sys
import time

import numpy as np
import sounddevice as sd

import recording
from serial_link import Control, pack, unpack

FS = 48000
BLOCK = 2048

# Printable ASCII only: the payload travels inside a `send <text>` command on
# the serial line before it ever reaches the air, and that line is UTF-8 and
# newline-delimited. Bytes outside this set would not survive the trip to the
# transmitter, which has nothing to do with what the air does to them.
ALPHABET = (b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            b"abcdefghijklmnopqrstuvwxyz0123456789")


def make_text_payload(seed, n):
    import random
    rng = random.Random(seed)
    return bytes(rng.choice(ALPHABET) for _ in range(n))


class Recorder:
    """Capture through the callback API, because the device this project
    needs on Windows refuses the blocking one.

    WDM-KS is the host API that bypasses the Windows audio processing that
    destroys these tones, and PortAudio has no blocking read for it -- it
    fails outright with 'Blocking API not supported yet'. So the one machine
    that most needs a recording was the one that could not make one. The
    callback path works on every host API here, which is why there is no
    longer a second one.
    """

    def __init__(self, device):
        self.q = queue.Queue()
        self.stream = sd.InputStream(samplerate=FS, channels=1,
                                     blocksize=BLOCK, device=device,
                                     callback=self._cb)

    def _cb(self, indata, frames, time_info, status):
        # Real-time thread: copy and queue, nothing else.
        self.q.put(indata[:, 0].copy())

    def __enter__(self):
        self.stream.start()
        time.sleep(0.2)          # let the device settle before it counts
        self.drain()
        return self

    def __exit__(self, *exc):
        self.stream.stop()
        self.stream.close()

    def drain(self):
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                return

    def collect(self, secs):
        """Everything heard over the next `secs`, in order."""
        chunks = []
        t0 = time.time()
        while time.time() - t0 < secs:
            try:
                chunks.append(self.q.get(timeout=0.5))
            except queue.Empty:
                pass
        while True:
            try:
                chunks.append(self.q.get_nowait())
            except queue.Empty:
                break
        return np.concatenate(chunks) if chunks else np.zeros(0)


_seq = [0]


def ask(ctl, cmd, timeout=8.0):
    """One command to the agent, its reply back, or None if it stayed quiet.

    Same `CMD <seq>` / `OK <seq>` exchange console.py speaks, sequence number
    included: the agent also emits unsolicited `EVT` lines, and a meter left
    running on the far side would otherwise be mistaken for an answer.
    """
    _seq[0] += 1
    want = str(_seq[0])
    ctl.send(f"CMD {want} {pack(cmd)}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ctl.recv(timeout=max(0.05, deadline - time.time()))
        if line is None or not line.startswith("OK "):
            continue
        seq, _, body = line[3:].partition(" ")
        if seq == want:
            return unpack(body)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', required=True, help="serial port to the other machine")
    ap.add_argument('--sync-baud', type=int, default=115200)
    ap.add_argument('--device', help="input device (index or name)")
    ap.add_argument('--mode', choices=('fsk', 'mfsk', 'mary'), default='mfsk')
    ap.add_argument('--gain', type=float, help="far side output amplitude 0..1")
    ap.add_argument('--bytes', type=int, default=48)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--trials', type=int, default=1)
    ap.add_argument('--tail', type=float, default=2.0,
                    help="seconds to keep recording after the burst should have ended")
    ap.add_argument('--text', help="send this exact text instead of a random "
                                   "payload (for a readable demonstration)")
    ap.add_argument('--gap', type=float, default=None,
                    help="silence at the end of each M-ary symbol, as a "
                         "fraction; both machines must agree")
    ap.add_argument('--repeat', type=int, default=2,
                    help="how many times each coded bit is sent")
    ap.add_argument('--parallel', action='store_true',
                    help="with --fec, give each tone pair its own bit instead "
                         "of having them all vote on one")
    ap.add_argument('--fec', action='store_true',
                    help="transmit an error-corrected block instead of a raw "
                         "byte stream")
    ap.add_argument('--chirp', nargs='?', const='300 22000 4', metavar='"f0 f1 s"',
                    help="record a frequency sweep instead of a payload, to "
                         "measure what the link does to each frequency")
    ap.add_argument('--out', default='captures')
    ap.add_argument('--label', default='', help="goes in the filename; name the setup")
    args = ap.parse_args()

    if args.device is not None and args.device.isdigit():
        args.device = int(args.device)

    ctl = Control(args.port, args.sync_baud)
    if ask(ctl, "ping") != "pong":
        sys.exit(f"[capture] sem resposta em {args.port} -- a outra maquina esta em --role agent?")

    print(f"[capture] agent respondeu. modo={args.mode}")
    ask(ctl, f"mode {args.mode}")
    ask(ctl, "spk on")
    if args.fec:
        ask(ctl, f"fecpar {'on' if args.parallel else 'off'}")
        ask(ctl, f"fecrep {args.repeat}")
    if args.gap is not None:
        ask(ctl, f"marygap {args.gap}")
    if args.gain is not None:
        ask(ctl, f"gain {args.gain}")

    # 10 bits per byte framed, plus the console's 11-byte preamble and the
    # modulator's idle tail. Generous rather than tight: a truncated capture
    # is worthless, and disk is free.
    if args.chirp:
        f0, f1, secs = (float(x) for x in args.chirp.split())
        with Recorder(args.device) as rec:
            reply = ask(ctl, f"chirp {f0:.0f} {f1:.0f} {secs}")
            if reply is None or 'chirp' not in reply:
                sys.exit(f"[capture] a outra maquina recusou o chirp: {reply!r}")
            samples = rec.collect(secs + 2.0)
        stem = recording.save(args.out, samples, b'', kind='chirp',
                              label=args.label or 'chirp', mode=args.mode,
                              baud=0, fs=FS, chirp=[f0, f1, secs],
                              gain=args.gain, device=str(args.device),
                              rms=float(np.sqrt(np.mean(np.square(samples)))),
                              peak=float(np.max(np.abs(samples))))
        print(f"[capture] {stem.name}  {len(samples)/FS:.1f}s")
        ctl.close()
        print(f"[capture] agora: ./venv/bin/python channel.py {stem.with_suffix('.json')}")
        return

    baud = 1200 if args.mode == 'fsk' else 100
    for trial in range(1, args.trials + 1):
        seed = args.seed if args.seed is not None else int(time.time() * 1000) & 0xFFFFFF
        payload = (args.text.encode() if args.text
                   else make_text_payload(seed, args.bytes))
        # A FEC block is one sync word plus rate-1/3 coding repeated twice,
        # so it spends far longer on the air than its byte count suggests.
        if args.fec:
            coded = (len(payload) * 8 + 6) * 3 * args.repeat
            if args.mode == 'mary':
                airtime = (120 + 8 + coded / 4 + 6) / baud
            elif args.parallel:
                airtime = (31 + 80 + coded / 5) / baud
            else:
                airtime = (31 + 80 + coded) / baud
        else:
            airtime = (len(payload) + 16) * 10 / baud
        duration = airtime + args.tail + 1.0

        with Recorder(args.device) as rec:
            verb = "fecsend" if args.fec else "send"
            reply = ask(ctl, f"{verb} " + payload.decode())
            if reply is None or ('enviando' not in reply and 'fecsend' not in reply):
                print(f"[capture] a outra maquina recusou o envio: {reply!r}")
                break
            samples = rec.collect(duration)
        rms = float(np.sqrt(np.mean(np.square(samples)))) if len(samples) else 0.0
        peak = float(np.max(np.abs(samples))) if len(samples) else 0.0

        stem = recording.save(args.out, samples, payload,
                              label=args.label or args.mode, mode=args.mode,
                              kind='fec' if args.fec else 'stream',
                              fec_repeat=args.repeat if args.fec else 0,
                              parallel=bool(args.fec and args.parallel),
                              gap=args.gap or 0.0,
                              baud=baud, fs=FS, seed=seed, gain=args.gain,
                              device=str(args.device), rms=rms, peak=peak,
                              airtime_s=round(airtime, 2))
        print(f"[capture] {trial}/{args.trials}  {stem.name}  "
              f"{len(samples)/FS:.1f}s  rms={rms:.4f} pico={peak:.3f}")

    ctl.close()
    print(f"[capture] pronto. Agora: ./venv/bin/python bench.py {args.out}")


if __name__ == '__main__':
    main()
