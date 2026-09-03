"""Record *this* machine transmitting, on the far machine's microphone.

`capture.py` can only measure one direction. It owns the serial port and the
local microphone at once, so what it records is always the far side playing --
which means every number this project has is a statement about one chain:
B's speaker, the air, A's microphone, A's capture gain. The reverse chain
shares none of those elements, so it cannot be deduced from them.

This is the mirror. The far side records with `grave`, which already exists in
the shared command table; the transmission happens here, through the same
`AudioNode` and the same `fecsend` the live link uses, so the frame on the air
is the frame the link would send. The recording then comes back over the
serial cable and is written in `recording.py`'s format under the *same* stem
it was recorded under, with the payload and the settings stamped into the
JSON -- because the far side does not know what was transmitted and its own
sidecar therefore cannot say.

The result is a pair of files `bench.py`, `align.py`, `spectro.py` and
`resultado.py` score without knowing which direction produced them.

It owns the serial port, so the local console must be stopped first.

    ./venv/bin/python capture_a2b.py --port /dev/ttyUSB0 --out-device 20 \
        --mode mary --fec --repeat 2 --gain 1.0 --bytes 48 --trials 3 \
        --label mary-base-A2B --out captures-a2b
"""

import argparse
import json
import sys
import time

import numpy as np

import recording
from capture import ask, make_text_payload, sync_span, SYNC_HUSH, FS
from console import AudioNode, execute, fetch_recording
from serial_link import Control


def remote_fn(ctl, timeout=20.0):
    """`fetch_recording` wants a callable that talks to the far side."""
    # `''` and not `None`: `fetch_file` was written against console.py's own
    # `remote()`, which answers with a string even when the far side stays
    # quiet, and it calls `.split()` on the answer without checking. `ask`
    # returns None on a timeout, so one lost packet in the ~20000 this
    # campaign pulls would end the run in an AttributeError three frames deep.
    return lambda cmd, timeout=timeout: (ask(ctl, cmd, timeout=timeout) or '')


def wait_recording(ctl, timeout):
    """Poll `gravou` until the far side has written the pair, or give up.

    The far side arms instantly and collects on its demodulator thread, so the
    only way to know it finished is to ask. A recording that never reports
    `pronto` is a microphone that did not deliver -- the same failure mode
    `capture.py` guards against locally -- and is worth failing loudly on
    rather than fetching a truncated file.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        reply = ask(ctl, "gravou", timeout=8.0) or ''
        if reply.startswith("pronto "):
            return reply.split()[1]
        if reply.startswith("ERRO"):
            return None
        time.sleep(1.0)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', required=True)
    ap.add_argument('--sync-baud', type=int, default=115200)
    ap.add_argument('--out-device', default=None,
                    help="dispositivo de saida local (indice ou nome)")
    ap.add_argument('--mode', choices=('fsk', 'mfsk', 'mary'), default='mary')
    ap.add_argument('--gain', type=float, default=1.0,
                    help="amplitude de saida DESTA maquina, 0..1")
    ap.add_argument('--bytes', type=int, default=48)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--trials', type=int, default=1)
    ap.add_argument('--tail', type=float, default=2.0)
    ap.add_argument('--text', help="envia este texto em vez de um payload aleatorio")
    ap.add_argument('--band', type=float, default=None)
    ap.add_argument('--grouped', action='store_true')
    ap.add_argument('--chord', action='store_true')
    ap.add_argument('--gap', type=float, default=None)
    ap.add_argument('--repeat', type=int, default=2)
    ap.add_argument('--parallel', action='store_true')
    ap.add_argument('--fec', action='store_true')
    ap.add_argument('--sync-chirp', action='store_true')
    ap.add_argument('--chirp', nargs='?', const='300 6000 4', metavar='"f0 f1 s"',
                    help="varredura em vez de payload, para medir o canal A->B")
    ap.add_argument('--tone', nargs='?', const='1700 3', metavar='"hz s"',
                    help="um tom puro em vez de payload")
    ap.add_argument('--silence', type=float, default=None,
                    help="nao transmite nada; so grava o piso do microfone de la")
    ap.add_argument('--exact', action='store_true',
                    help="traz o audio em float32 em vez de int16 (bem mais lento)")
    ap.add_argument('--out', default='captures-a2b')
    ap.add_argument('--label', default='')
    args = ap.parse_args()
    if args.fec and args.mode == 'fsk':
        ap.error("--fec so existe em mfsk ou mary; o Bell 202 e linha serial burra")

    dev_out = args.out_device
    if dev_out is not None and dev_out.isdigit():
        dev_out = int(dev_out)

    ctl = Control(args.port, args.sync_baud)
    if ask(ctl, "ping") != "pong":
        sys.exit(f"[a2b] sem resposta em {args.port} -- a outra maquina esta em --role agent?")
    print("[a2b] agent respondeu.")

    # The far side only listens. Its speaker stays off so nothing of its own
    # lands in the recording, and its mic has to be on before `grave` will arm.
    print("[a2b] remoto:", ask(ctl, "spk off"))
    print("[a2b] remoto:", ask(ctl, "mic on"))

    node = AudioNode(gain=args.gain, dev_out=dev_out, dev_in=None,
                     on_event=lambda t: None)
    # A Bluetooth sink that another process just released is present and
    # advertises zero channels for a second or two, and an open in that window
    # fails with `Invalid number of channels`. Retrying does not help; waiting
    # does. This script is launched once per point, so it hits that window on
    # every point of a sweep.
    for attempt in range(1, 5):
        try:
            print("[a2b] local:", execute(node, "spk on"))
            break
        except Exception as e:
            print(f"[a2b] a saida nao abriu ({e}); tentativa {attempt} de 4")
            time.sleep(3.0)
    else:
        sys.exit("[a2b] a caixa local nao abriu em 4 tentativas")
    print("[a2b] local:", execute(node, f"mode {args.mode}"))
    print("[a2b] local:", execute(node, f"gain {args.gain}"))
    if args.fec:
        execute(node, f"fecpar {'on' if args.parallel else 'off'}")
        execute(node, f"fecrep {args.repeat}")
        execute(node, f"syncsweep {'on' if args.sync_chirp else 'off'}")
    if args.gap is not None:
        execute(node, f"marygap {args.gap}")
    if args.band is not None:
        execute(node, f"maryband {args.band}")
    if args.chord:
        execute(node, "marychord on")
    if args.grouped:
        execute(node, "mfskgroup on")

    baud = 1200 if args.mode == 'fsk' else 100
    label = args.label or f"{args.mode}-A2B"

    def one_trial(trial):
        """Arm the far side, transmit, bring the pair back, stamp the JSON."""
        extra = {}
        if args.silence is not None:
            secs, payload, cmd, kind, want = args.silence, b'', None, 'room', ''
        elif args.chirp:
            f0, f1, cs = (float(x) for x in args.chirp.split())
            secs, payload = cs + 2.0, b''
            cmd, kind, want = f"chirp {f0:.0f} {f1:.0f} {cs}", 'chirp', 'chirp'
            extra['chirp'] = [f0, f1, cs]
        elif args.tone:
            hz, ts = (float(x) for x in args.tone.split())
            secs, payload = ts + 2.0, b''
            cmd, kind, want = f"tonef {hz:.0f} {ts}", 'tone', 'tonef'
            extra['tone_hz'] = hz
        else:
            seed = (args.seed if args.seed is not None
                    else int(time.time() * 1000) & 0xFFFFFF)
            payload = (args.text.encode() if args.text
                       else make_text_payload(seed, args.bytes))
            if args.fec:
                # `fec_plan` is the transmitter's own answer for how long the
                # burst lasts, mirroring `_fec_frame`. Deriving it a second
                # time here is how a recording ends up stopping before the
                # frame does.
                _, airtime = node.fec_plan(payload)
                cmd, kind, want = "fecsend " + payload.decode(), 'fec', 'fecsend'
            else:
                airtime = (len(payload) + 16) * 10 / baud
                cmd, kind, want = "send " + payload.decode(), 'stream', 'enviando'
            secs = airtime + args.tail + 1.0
            extra.update(seed=seed, airtime_s=round(airtime, 2),
                         fec_repeat=args.repeat if args.fec else 0,
                         parallel=bool(args.fec and args.parallel),
                         sync_span_symbols=(sync_span(len(payload), args.repeat)
                                            if args.sync_chirp else 0.0))

        secs = min(secs, 120.0)
        if secs > 120.0:
            # `grave` clamps to 120 s without saying so, and a clamped window
            # is a burst cut off mid-frame: audio that scores as a dead link
            # and looks like one.
            print(f"[a2b] {secs:.0f}s passa do limite de 120s do `grave` -- "
                  f"reduza --bytes ou --repeat")
            return False
        reply = ask(ctl, f"grave {secs:.1f} {label}")
        # `startswith`, not `in`: the refusal for a recording already running
        # is "ja esta gravando (...)", which contains the word and would pass a
        # substring test. That path leaves the previous `rec_stem` in place, so
        # `gravou` would then hand back the *previous* recording and this
        # script would stamp the new payload onto the old audio -- garbage that
        # scores as a bad channel and says nothing about one.
        if not reply.startswith('gravando '):
            print(f"[a2b] a outra maquina recusou gravar: {reply!r}")
            return False
        # The far side is already collecting; a beat of margin keeps the
        # first preamble symbols off the edge of its window.
        time.sleep(0.4)
        if cmd is not None:
            out = str(execute(node, cmd))
            # The success token, not the refusal. `execute` refuses in a dozen
            # different sentences -- "caixa desligada - rode 'spk on' antes",
            # "fecsend so em mfsk ou mary", "comando desconhecido" -- and a
            # test that enumerates them is a test that will miss the next one.
            # Every accepting branch answers with its own verb; that is the
            # thing to look for. Same test `capture.py` makes of the far side.
            if want not in out:
                print(f"[a2b] o transmissor local recusou: {out!r}")
                return False
            print(f"[a2b] local: {out}")

        stem = wait_recording(ctl, timeout=secs + 30.0)
        if stem is None:
            print("[a2b] a gravacao nao ficou pronta")
            return False
        print(f"[a2b] trazendo {stem} pelo cabo...")
        got = fetch_recording(remote_fn(ctl), stem, args.out,
                              note=lambda t: print('   ' + str(t).strip()),
                              exact=args.exact)
        if got is None:
            print("[a2b] a transferencia falhou")
            return False

        # The far side recorded audio and knows nothing about what was played,
        # so its sidecar cannot say. Stamp it here, in the same fields
        # `capture.py` writes, or the offline tools score a payload of zero
        # bytes against a real burst.
        jpath = got.with_name(got.name + '.json')
        meta = json.loads(jpath.read_text())
        samples = recording.read_wav(got.with_name(got.name + '.wav'))
        meta.update(kind=kind, label=label, mode=args.mode, baud=baud,
                    fs=FS, gain=args.gain, direction='A2B',
                    gap=args.gap or 0.0, band=args.band or 0.0,
                    chord=bool(args.chord), grouped=bool(args.grouped),
                    sync_chirp=bool(args.sync_chirp),
                    sync_hush=SYNC_HUSH if args.sync_chirp else 0.0,
                    device=str(dev_out),
                    rms=float(np.sqrt(np.mean(np.square(samples)))) if len(samples) else 0.0,
                    peak=float(np.max(np.abs(samples))) if len(samples) else 0.0,
                    **extra)
        for drop in ('payload_hex', 'payload_len', 'samples'):
            meta.pop(drop, None)
        recording.save_as(got, samples, payload, **meta)
        print(f"[a2b] {trial}/{args.trials}  {got.name}  {len(samples)/FS:.1f}s  "
              f"rms={meta['rms']:.4f} pico={meta['peak']:.3f}")
        return True

    done = 0
    try:
        for trial in range(1, args.trials + 1):
            # `continue`, not `break`: one refused trial is not a reason to
            # abandon the other three, and a point recorded 3 times out of 4 is
            # still a point.
            if one_trial(trial):
                done += 1
    finally:
        try:
            execute(node, "spk off")
        except Exception:
            pass
        # The far side's speaker was switched off so nothing of its own landed
        # in the recording. Leaving it off outlives this process and would meet
        # the next B->A measurement as "caixa desligada".
        try:
            ask(ctl, "spk on")
        except Exception:
            pass
        ctl.close()
    print(f"[a2b] {done} de {args.trials} gravacoes. "
          f"Agora: ./venv/bin/python bench.py {args.out}")
    # A non-zero status is the only thing the shell driver can see, and without
    # it a point that recorded nothing at all printed its heading and was
    # walked past. Silent loss of a point is the failure that costs a campaign.
    if done == 0:
        sys.exit(1)
    if done < args.trials:
        sys.exit(2)


if __name__ == '__main__':
    main()
