"""Pull a file across the acoustic link, one packet at a time.

Stop-and-wait ARQ driven entirely from the receiving end. The far side stays
stateless: it is told `sendpkt <file> <n>` over the serial cable and plays that
packet, nothing more. This side decides what to ask for and when to ask again,
which is what makes a lost packet cost one retry instead of the whole file.

The serial cable carries only the requests. Every byte of the file itself
crosses the air, which is still the thing under test.

    python recvfile.py --port COM4 --remote-file testcard.bmp --out got.bmp

Reception ends a packet the moment its CRC checks out, so a clean packet costs
only its own air time and a bad one costs the timeout.
"""

import argparse
import sys
import time

import numpy as np
import sounddevice as sd

import xfer
from modem import MFSKDemodulator
from serial_link import Control, pack, unpack

FS = 48000
BLOCK = 2048
MFSK_BAUD = 100


class Remote:
    def __init__(self, port, baud):
        self.ctl = Control(port, baud)
        self.seq = 0
        time.sleep(0.3)
        self.ctl.drain()

    def cmd(self, text, timeout=15.0):
        self.seq += 1
        want = str(self.seq)
        self.ctl.send(f"CMD {want} {pack(text)}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.ctl.recv(timeout=max(0.05, deadline - time.time()))
            if line is None or not line.startswith("OK "):
                continue
            got, _, body = line[3:].partition(" ")
            if got == want:
                return unpack(body)
        return None

    def close(self):
        self.ctl.close()


def main():
    p = argparse.ArgumentParser(description="Recebe um arquivo pelo link acustico")
    p.add_argument("--port", required=True)
    p.add_argument("--sync-baud", type=int, default=115200)
    p.add_argument("--remote-file", required=True, help="caminho do arquivo na outra maquina")
    p.add_argument("--out", required=True, help="onde gravar deste lado")
    p.add_argument("--device", type=int, default=None, help="indice do dispositivo de entrada")
    p.add_argument("--gain", type=float, default=0.35, help="ganho de saida da outra maquina")
    p.add_argument("--retries", type=int, default=4, help="tentativas por pacote")
    p.add_argument("--margin", type=float, default=3.0, help="segundos extras de escuta por pacote")
    args = p.parse_args()

    rem = Remote(args.port, args.sync_baud)
    if rem.cmd("ping") != "pong":
        print("outra maquina nao responde no canal serial.", file=sys.stderr)
        return 1

    for setup in ("mode mfsk", "spk on", f"gain {args.gain}", "mic off"):
        print(f"  remoto: {setup:16s} -> {rem.cmd(setup)}")

    info = rem.cmd(f"fileinfo {args.remote_file}")
    if not info or "size=" not in info:
        print(f"fileinfo falhou: {info}", file=sys.stderr)
        return 1
    fields = dict(tok.split("=", 1) for tok in info.split() if "=" in tok)
    size = int(fields["size"])
    npackets = int(fields["packets"])
    want_crc = int(fields["crc32"], 16)
    print(f"\n{args.remote_file}: {size} bytes, {npackets} pacotes, crc32 {want_crc:08x}")

    per_packet = xfer.air_seconds(len(xfer.build(0, b"x" * xfer.PAYLOAD_SIZE)), MFSK_BAUD)
    print(f"~{per_packet:.1f}s de audio por pacote, ~{per_packet * npackets / 60:.1f} min no melhor caso\n")

    demod = MFSKDemodulator(fs=FS, baud=MFSK_BAUD)
    chunks = {}
    started = time.time()
    retries_used = 0

    with sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCK,
                        device=args.device) as stream:
        for _ in range(3):
            stream.read(BLOCK)          # warm up before the first request

        for seq in range(npackets):
            for attempt in range(1, args.retries + 1):
                demod.reset()
                buf = bytearray()
                # Drain whatever the stream buffered while we were parsing,
                # so the packet is not preceded by stale audio.
                while stream.read_available >= BLOCK:
                    stream.read(BLOCK)

                reply = rem.cmd(f"sendpkt {args.remote_file} {seq}")
                if reply is None or reply.startswith(("caixa", "seq", "uso", "sendpkt")):
                    print(f"  pkt {seq}: recusado pelo remoto: {reply}")
                    break

                deadline = time.time() + per_packet + args.margin
                got = None
                while time.time() < deadline:
                    data, _ = stream.read(BLOCK)
                    buf += demod.demodulate(data[:, 0].copy())
                    got = xfer.parse(buf, want_seq=seq)
                    if got:
                        break

                if got:
                    chunks[seq] = got[1]
                    done = len(chunks)
                    bar = "#" * (done * 30 // npackets)
                    print(f"  [{bar:<30}] pkt {seq:2d}/{npackets - 1}  "
                          f"{len(got[1]):3d} bytes  tentativa {attempt}")
                    break
                retries_used += 1
                print(f"  pkt {seq:2d}: tentativa {attempt} falhou "
                      f"({len(buf)} bytes brutos, CRC nao fechou)")
            else:
                print(f"  pkt {seq}: DESISTINDO apos {args.retries} tentativas")

    rem.cmd("spk off")
    rem.close()

    missing = [i for i in range(npackets) if i not in chunks]
    data = b"".join(chunks.get(i, b"") for i in range(npackets))
    elapsed = time.time() - started

    print(f"\n{len(data)}/{size} bytes em {elapsed:.0f}s "
          f"({len(data) / elapsed:.1f} B/s efetivos, {retries_used} retransmissoes)")
    if missing:
        print(f"pacotes faltando: {missing}")

    got_crc = xfer.crc32(data)
    if len(data) == size and got_crc == want_crc:
        with open(args.out, "wb") as fh:
            fh.write(data)
        print(f"CRC32 {got_crc:08x} confere. Arquivo gravado em {args.out}")
        return 0

    # Write it anyway: a partial file is worth inspecting, but it must not be
    # mistaken for a good one.
    with open(args.out, "wb") as fh:
        fh.write(data)
    print(f"CRC32 {got_crc:08x} != {want_crc:08x} esperado. "
          f"Gravado em {args.out} MESMO ASSIM, para inspecao -- nao confie nele.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
