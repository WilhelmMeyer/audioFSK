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
import queue
import sys
import time

import numpy as np
import sounddevice as sd

import fec
import xfer
from modem import MFSKDemodulator, MaryDemodulator, MARY_BITS
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
    p.add_argument("--fec", action="store_true",
                   help="pacotes com correcao de erro em vez do fluxo 8N1")
    p.add_argument("--mode", choices=("mfsk", "mary"), default="mfsk",
                   help="camada fisica; mary = 16 tons, 4 bits por simbolo")
    p.add_argument("--packet-size", type=int, default=xfer.PAYLOAD_SIZE,
                   help="bytes de carga por pacote; maior amortiza o preambulo")
    p.add_argument("--retries", type=int, default=4, help="tentativas por pacote")
    p.add_argument("--margin", type=float, default=3.0, help="segundos extras de escuta por pacote")
    args = p.parse_args()

    rem = Remote(args.port, args.sync_baud)
    if rem.cmd("ping") != "pong":
        print("outra maquina nao responde no canal serial.", file=sys.stderr)
        return 1

    for setup in (f"mode {args.mode}", "spk on", f"gain {args.gain}", "mic off"):
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

    # fileinfo reports packets at the default size; recompute for ours.
    npackets = -(-size // args.packet_size)
    packet_bytes = len(xfer.build(0, b"x" * args.packet_size))

    if args.fec:
        # A coded block is one sync word, the rate-1/3 code repeated, plus the
        # preamble the receiver needs to lock its symbol clock. That preamble
        # is paid once per packet, which is why a bigger packet is cheaper per
        # byte -- 28% of the air time at 32 bytes, 19% at 64.
        bits_per_symbol = MARY_BITS if args.mode == "mary" else 1
        coded = len(fec.frame(b"x" * packet_bytes, repeat=1))
        per_packet = (120 + coded / bits_per_symbol + 6) / MFSK_BAUD
    else:
        per_packet = xfer.air_seconds(packet_bytes, MFSK_BAUD)
    print(f"~{per_packet:.1f}s de audio por pacote, ~{per_packet * npackets / 60:.1f} min no melhor caso\n")

    if args.mode == "mary":
        demod = MaryDemodulator(fs=FS, baud=MFSK_BAUD)
    else:
        demod = MFSKDemodulator(fs=FS, baud=MFSK_BAUD)
    chunks = {}
    started = time.time()
    retries_used = 0

    # Callback capture, not blocking reads: the WDM-KS host API on Windows --
    # the only input here that bypasses the driver effects mangling the signal
    # -- rejects the blocking API outright with "Blocking API not supported
    # yet". The callback path works on every host API.
    blocks = queue.Queue()

    def on_audio(indata, frames, time_info, status):
        blocks.put(indata[:, 0].copy())

    stream = sd.InputStream(samplerate=FS, channels=1, blocksize=BLOCK,
                            device=args.device, callback=on_audio)
    stream.start()
    time.sleep(0.3)                                   # let it settle

    def progress(done_packets):
        pct = done_packets * 100 // npackets
        bar = "#" * (pct * 30 // 100)
        elapsed = time.time() - started
        eta = (elapsed / done_packets * (npackets - done_packets)) if done_packets else 0
        return (f"[{bar:<30}] {pct:3d}%  {done_packets}/{npackets} pacotes  "
                f"{len(chunks) * xfer.PAYLOAD_SIZE:4d}/{size} bytes  "
                f"{elapsed:4.0f}s decorridos" + (f", ~{eta:.0f}s restantes" if eta else ""))

    try:
        for seq in range(npackets):
            for attempt in range(1, args.retries + 1):
                demod.reset()
                buf = bytearray()
                while not blocks.empty():             # drop audio captured
                    blocks.get_nowait()               # while we were parsing

                if args.fec:
                    reply = rem.cmd(f"fecpkt {args.remote_file} {seq} {args.packet_size}")
                else:
                    reply = rem.cmd(f"sendpkt {args.remote_file} {seq}")
                if reply is None or not reply.startswith("tx "):
                    print(f"  pkt {seq}: recusado pelo remoto: {reply}")
                    break
                print(f"  -> remoto envia {reply}")

                deadline = time.time() + per_packet + args.margin
                last_tick, got = time.time(), None
                soft = []
                while time.time() < deadline:
                    try:
                        data = blocks.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    if args.fec:
                        # A coded block cannot be parsed as it arrives: the
                        # decoder needs the whole thing before any of it means
                        # anything, so collect first and decode at the end.
                        soft.append(demod.demodulate_soft(data))
                        continue
                    buf += demod.demodulate(data)
                    got = xfer.parse(buf, want_seq=seq)
                    if got:
                        break
                    if time.time() - last_tick >= 3.0:
                        last_tick = time.time()
                        heard = len(buf) * 100 // (xfer.PAYLOAD_SIZE + xfer.HEADER +
                                                   xfer.TRAILER + len(xfer.LEAD))
                        print(f"      ... pkt {seq}: {min(heard, 99):2d}% ouvido "
                              f"({len(buf)} bytes brutos)")

                if args.fec:
                    llr = np.concatenate(soft) if soft else np.zeros(0)
                    start = fec.find_sync(llr)
                    if start is not None:
                        block = fec.decode(llr[start:], packet_bytes, repeat=1)
                        got = xfer.parse(block, want_seq=seq)
                    buf = llr

                if got:
                    chunks[seq] = got[1]
                    print(f"  {progress(len(chunks))}   pkt {seq} OK "
                          f"({len(got[1])} bytes, tentativa {attempt})")
                    break
                retries_used += 1
                print(f"  pkt {seq:2d}: tentativa {attempt} falhou "
                      f"({len(buf)} {'simbolos' if args.fec else 'bytes brutos'}, "
                      f"CRC nao fechou)")
            else:
                print(f"  pkt {seq}: DESISTINDO apos {args.retries} tentativas")
    finally:
        stream.stop()
        stream.close()

    rem.cmd("spk off")
    rem.close()

    missing = [i for i in range(npackets) if i not in chunks]
    # Zero-fill a packet that never arrived rather than omitting it. Omitting
    # shortens the file and shifts every byte after the gap, so one lost packet
    # ruins the whole remainder; padding keeps every later byte at its correct
    # offset and confines the damage to the hole. For an image that is the
    # difference between a few wrong pixels and an unreadable file.
    filled = []
    for i in range(npackets):
        if i in chunks:
            filled.append(chunks[i])
        else:
            last = i == npackets - 1
            gap = (size - (npackets - 1) * args.packet_size) if last else args.packet_size
            filled.append(b"\x00" * max(0, gap))
    data = b"".join(filled)
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
