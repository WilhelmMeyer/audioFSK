"""Two-machine acoustic link test, synchronized over a serial control channel.

The serial cable is the control channel; the air is the channel under test.
Keeping the two apart is the whole point: the wire arms and triggers both
machines, so the microphone is already capturing before the first sample of
audio leaves the speaker, and the score at the end measures the acoustic path
alone -- never a race between two humans pressing Enter.

    machine A (TX)                       machine B (RX)
      --role tx --port COM4                --role rx --port /dev/ttyUSB0
            |                                     |
            |--------- serial: ARM n seed ------->|  opens mic, warms filters
            |<-------- serial: ARMED -------------|
            |--------- serial: GO --------------->|  starts collecting
            |=== speaker ~~~ air ~~~ microphone ==>|  the link under test
            |--------- serial: DONE ------------->|
            |<-------- serial: RESULT ... --------|

Both sides build the same payload from the seed, so the payload itself never
crosses the wire -- only the air, which is what we are grading.
"""

import argparse
import difflib
import random
import sys
import time

import numpy as np
import sounddevice as sd

from modem import FSKModulator, FSKDemodulator
from serial_link import Control

FS = 48000
BAUD = 1200
BLOCK = 2048

# Same preamble app.py puts in front of a burst: an unbroken mark/space
# alternation to wake up microphone AGC, then 0xFF as the payload marker.
PREAMBLE = bytes([0x55] * 10 + [0xFF])

GUARD = 0.15    # s between GO and the first audio sample; covers serial latency only
TAIL = 0.60     # s of extra capture after DONE, for acoustic + buffer latency


# --- payload -------------------------------------------------------------

def make_payload(seed, n):
    """Deterministic from the seed, so both sides build it independently."""
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(n))


def find_payload_start(rx):
    """Cut the lead-in and preamble off at the 0xFF marker that ends them.

    A fixed offset will not do: everything ahead of the payload is 0x55 bytes,
    but how many depends on --lead and on how much of the lead-in the receiver
    actually caught. So find the run instead -- the longest stretch of
    {0x55, 0xFF} near the head -- and take the last 0xFF inside it. A random
    payload almost never produces four such bytes in a row, and leading garbage
    from a cold microphone is skipped rather than fatal.
    """
    head = rx[:96]
    best_run = best_marker = None
    i = 0
    while i < len(head):
        if head[i] not in (0x55, 0xFF):
            i += 1
            continue
        start, marker = i, None
        while i < len(head) and head[i] in (0x55, 0xFF):
            if head[i] == 0xFF:
                marker = i
            i += 1
        run = i - start
        if marker is not None and run >= 4 and (best_run is None or run > best_run):
            best_run, best_marker = run, marker
    return (best_marker + 1, True) if best_marker is not None else (0, False)


def score(expected, received):
    """Match with alignment, because bytes get dropped, not just corrupted.

    A dropped byte shifts everything after it, so an index-by-index compare
    would score a nearly perfect link as total garbage. SequenceMatcher
    tolerates insertions and deletions. autojunk must stay off: above 200
    elements it treats common byte values as noise and wrecks the alignment.
    """
    start, found = find_payload_start(received)
    payload_rx = received[start:]
    sm = difflib.SequenceMatcher(None, expected, payload_rx, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    return matched, payload_rx, found


# --- roles ---------------------------------------------------------------

def run_tx(args, ctl):
    print(f"[tx] handshake em {args.port} @ {args.sync_baud}...")
    ctl.drain()
    t0 = time.time()
    ctl.send("SYNC?")
    reply = ctl.recv(timeout=args.wait)
    if reply != "SYNC!":
        print(f"[tx] sem resposta do RX (recebido: {reply!r}).")
        print("     Confira: TX de um lado no RX do outro, GND comum,")
        print("     mesmo --sync-baud, e '--role rx' rodando na outra maquina.")
        return 1
    print(f"[tx] controle OK, ida-e-volta {(time.time() - t0) * 1000:.1f} ms")

    mod = FSKModulator(fs=FS, baud=BAUD)
    failures = 0

    for trial in range(1, args.trials + 1):
        seed = random.randrange(1 << 30)
        payload = make_payload(seed, args.bytes)

        ctl.send(f"ARM {args.bytes} {seed}")
        if ctl.recv(timeout=args.wait) != "ARMED":
            print(f"[tx] trial {trial}: RX nao armou.")
            failures += 1
            continue

        # Lead-in tone first: microphone AGC needs a moment to settle, and a
        # burst that starts cold loses its own preamble.
        lead = mod.modulate(bytes([0x55]) * args.lead)
        frame = mod.modulate(PREAMBLE + payload)
        samples = (np.concatenate([lead, frame]) * args.gain).astype(np.float32)

        ctl.send("GO")
        time.sleep(GUARD)
        sd.play(samples, FS, device=args.device, blocking=True)
        ctl.send("DONE")

        line = ctl.recv(timeout=args.wait + TAIL + 5)
        if line is None or not line.startswith("RESULT"):
            print(f"[tx] trial {trial}: sem resultado do RX (recebido: {line!r}).")
            failures += 1
            continue

        fields = {}
        for tok in line.split()[1:]:
            key, _, val = tok.partition("=")
            fields[key] = val
        report(trial, args.bytes, fields, len(samples) / FS)
        if float(fields.get("acc", 0.0)) < 0.99:
            failures += 1

    return 1 if failures else 0


def report(trial, nbytes, f, airtime):
    matched = int(f.get("matched", 0))
    got = int(f.get("got", 0))
    acc = float(f.get("acc", 0.0))
    peak = float(f.get("peak", 0.0))
    inband = float(f.get("inband", 0.0))
    synced = f.get("sync", "0") == "1"

    # Ordered so the cheapest and most likely cause is named first, the same
    # way tune_rx_loop does it.
    if peak >= 0.99:
        verdict = "CLIPPING no mic - baixe o volume"
    elif not synced:
        verdict = "preambulo nao achado - rode --tune antes"
    elif acc >= 0.999:
        verdict = "PERFEITO"
    elif acc >= 0.99:
        verdict = "bom"
    elif inband < 0.5:
        verdict = "ruido dominando - sem portadora na banda"
    else:
        verdict = "RUIM - ajuste volume/distancia"

    print(f"[tx] trial {trial}: {matched}/{nbytes} bytes  acc {acc * 100:6.2f}%  "
          f"recebidos {got}  pico {peak:.2f}  in-band {inband * 100:3.0f}%  "
          f"{airtime:.1f}s no ar  -> {verdict}")


def run_rx(args, ctl):
    demod = FSKDemodulator(fs=FS, baud=BAUD, squelch=args.squelch)
    print(f"[rx] escutando o controle em {args.port} @ {args.sync_baud}")
    print("[rx] Ctrl+C para sair.")

    while True:
        line = ctl.recv(timeout=None)
        if line is None:
            continue

        if line == "SYNC?":
            ctl.send("SYNC!")
            print("[rx] handshake respondido.")
            continue

        if not line.startswith("ARM "):
            continue

        try:
            _, nbytes, seed = line.split()
            nbytes, seed = int(nbytes), int(seed)
        except ValueError:
            print(f"[rx] ARM malformado: {line!r}")
            continue

        expected = make_payload(seed, nbytes)

        # The stream opens and warms up *before* we answer ARMED, so device
        # startup latency is off the critical path and GO can act immediately.
        with sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCK,
                            device=args.device) as stream:
            for _ in range(3):
                stream.read(BLOCK)
            demod.reset()
            ctl.send("ARMED")
            print(f"[rx] armado: {nbytes} bytes, seed {seed}. Aguardando GO...")

            received = bytearray()
            peak = 0.0
            rms_sum = level_sum = 0.0
            blocks = 0
            collecting = False
            deadline = None

            while True:
                data, _ = stream.read(BLOCK)
                out = demod.demodulate(data[:, 0].copy())

                if collecting:
                    received += out
                    peak = max(peak, demod.input_peak)
                    # Ratio of the sums, not the mean of per-block ratios: a
                    # near-silent block has an almost-zero denominator and
                    # would push the window's in-band figure past 100%.
                    rms_sum += demod.input_rms
                    level_sum += demod.level_rms
                    blocks += 1

                msg = ctl.poll()
                if msg == "GO" and not collecting:
                    demod.reset()
                    received.clear()
                    collecting = True
                    print("[rx] GO - capturando.")
                elif msg == "DONE" and deadline is None:
                    deadline = time.time() + TAIL

                if deadline is not None and time.time() >= deadline:
                    break

        matched, payload_rx, synced = score(expected, bytes(received))
        acc = matched / len(expected) if expected else 0.0
        inband = min(1.0, level_sum / rms_sum) if rms_sum > 1e-9 else 0.0

        ctl.send(f"RESULT matched={matched} expected={len(expected)} "
                 f"got={len(payload_rx)} acc={acc:.4f} peak={peak:.3f} "
                 f"inband={inband:.3f} sync={'1' if synced else '0'}")
        print(f"[rx] {matched}/{len(expected)} bytes ({acc * 100:.2f}%), "
              f"pico {peak:.2f}, in-band {inband * 100:.0f}%")


def run_check(args, ctl):
    """Serial wiring only -- nothing acoustic, so a failure here is the cable."""
    ctl.drain()
    print(f"[check] {args.port} @ {args.sync_baud}: CTS={ctl.ser.cts} DSR={ctl.ser.dsr}")
    for i in range(3):
        t0 = time.time()
        ctl.send("SYNC?")
        if ctl.recv(timeout=2.0) == "SYNC!":
            print(f"[check] ping {i + 1}: OK, {(time.time() - t0) * 1000:.1f} ms")
        else:
            print(f"[check] ping {i + 1}: FALHOU")
            print("        TX de um lado deve ir no RX do outro, GND comum,")
            print("        mesmo --sync-baud, e '--role rx' rodando la.")
            return 1
    return 0


def main():
    p = argparse.ArgumentParser(
        description="Teste de link acustico FSK sincronizado por porta serial")
    p.add_argument("--role", choices=["tx", "rx"], help="lado deste computador")
    p.add_argument("--port", help="porta serial de controle (COM4, /dev/ttyUSB0)")
    p.add_argument("--sync-baud", type=int, default=115200,
                   help="baud do canal de controle (padrao 115200)")
    p.add_argument("--bytes", type=int, default=256, help="bytes de payload por trial")
    p.add_argument("--trials", type=int, default=1, help="numero de repeticoes")
    p.add_argument("--lead", type=int, default=24,
                   help="bytes 0x55 de lead-in para acordar o AGC do microfone")
    p.add_argument("--gain", type=float, default=0.8, help="amplitude de saida, 0..1")
    p.add_argument("--squelch", type=float, default=0.005, help="squelch do demodulador")
    p.add_argument("--device", default=None, help="indice ou nome do dispositivo de audio")
    p.add_argument("--wait", type=float, default=15.0, help="timeout do handshake, em s")
    p.add_argument("--check", action="store_true", help="testa so o cabo serial e sai")
    p.add_argument("--list-devices", action="store_true",
                   help="lista dispositivos de audio e portas seriais e sai")
    args = p.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        print("\nPortas seriais:")
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            print(f"  {port.device:<16} {port.description}")
        return 0

    if not args.port:
        p.error("--port e obrigatorio (ex: COM4 no Windows, /dev/ttyUSB0 no Linux)")
    if not args.check and not args.role:
        p.error("--role tx ou --role rx e obrigatorio")

    if args.device is not None and args.device.isdigit():
        args.device = int(args.device)

    try:
        ctl = Control(args.port, args.sync_baud)
    except Exception as e:
        print(f"Nao consegui abrir {args.port}: {e}", file=sys.stderr)
        return 1

    try:
        if args.check:
            return run_check(args, ctl)
        if args.role == "tx":
            return run_tx(args, ctl)
        return run_rx(args, ctl)
    except KeyboardInterrupt:
        print("\nInterrompido.")
        return 0
    finally:
        ctl.close()


if __name__ == "__main__":
    sys.exit(main())
