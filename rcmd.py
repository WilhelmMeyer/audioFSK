"""Send commands to the far machine's agent and print the replies, then exit.

`console.py --role console` is a REPL, which is right when someone is sitting
there steering a link by ear and wrong when a measurement has to be scripted:
a test that cannot be run from a script cannot be re-run identically, and this
project's whole discipline is that a number has to be reproducible together
with the settings that produced it.

So this is the same control channel with no keyboard: one process, a list of
commands, the replies on stdout, and the port released on exit. It speaks the
protocol `console.py` already defines -- `CMD <seq> <packed>` out, `OK <seq>
<packed>` back -- rather than inventing a second one, because two framings on
one wire drift apart and the drift shows up as a machine that stopped
answering.

It owns the serial port, so the local console must be stopped first. It does
NOT own any audio device: everything it does happens on the other machine.

    ./venv/bin/python rcmd.py --port /dev/ttyUSB0 "mic on" --wait 10 "level"
"""

import argparse
import sys
import time

from serial_link import Control, pack, unpack


def talk(ctl, cmd, timeout=10.0, seq=[0]):
    """One command over, one reply back, with the sequence number matched.

    Matched rather than "take the next line" because the agent also pushes
    unsolicited `EVT` lines -- a meter reading landing between the command and
    its answer would otherwise be returned as the answer.
    """
    seq[0] += 1
    want = str(seq[0])
    ctl.send(f"CMD {want} {pack(cmd)}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ctl.recv(timeout=max(0.05, deadline - time.time()))
        if line is None:
            break
        if not line.startswith("OK "):
            continue                      # EVT and anything else: not an answer
        gseq, _, body = line[3:].partition(" ")
        if gseq == want:
            return unpack(body)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', required=True)
    ap.add_argument('--sync-baud', type=int, default=115200)
    ap.add_argument('--timeout', type=float, default=10.0)
    ap.add_argument('--wait', type=float, default=0.0,
                    help="segundos de pausa entre um comando e o seguinte")
    ap.add_argument('cmds', nargs='+', help="comandos para a outra maquina")
    args = ap.parse_args()

    ctl = Control(args.port, args.sync_baud)
    time.sleep(0.3)                        # deixa a porta assentar antes do 1o
    failed = False
    try:
        for i, cmd in enumerate(args.cmds):
            if i and args.wait:
                print(f"[rcmd] esperando {args.wait:.1f}s")
                time.sleep(args.wait)
            out = talk(ctl, cmd, args.timeout)
            if out is None:
                print(f"[rcmd] {cmd!r}: sem resposta -- a outra maquina esta "
                      f"rodando --role agent?", file=sys.stderr)
                failed = True
                continue
            print(f"[rcmd] > {cmd}")
            for row in str(out).split("\n"):
                print(f"       {row}")
    finally:
        ctl._stop = True
        ctl.ser.close()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
