"""Score demodulator variants against recorded audio, offline.

The recordings are the fixed part and the demodulator is the variable one --
the reverse of testing on the air, where both move at once and no two runs
agree. Here every variant sees the identical samples, so the column that wins
won because of the code.

Adding an idea means adding one entry to VARIANTS. It costs seconds and no
second machine.

    ./venv/bin/python capture.py --port /dev/ttyUSB0 --mode mfsk --trials 3
    ./venv/bin/python bench.py                    # scores captures/
    ./venv/bin/python bench.py --detail           # also prints what came back

Scoring is `scoring.score`, the same alignment-tolerant match linktest.py uses
on the live link, so a gain measured here means the same thing there.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

import fec
import recording
from modem import FSKDemodulator, MFSKDemodulator, MFSK_PAIRS
from scoring import score

BLOCK = 2048


def run(demod, samples):
    """Feed a capture through in blocks, exactly as the live path would.

    Not one call with the whole array: both demodulators carry filter and
    timing state across calls, and a single giant block would hide any bug
    that only appears at a boundary -- which is where the live path spends
    all of its time.
    """
    out = bytearray()
    for i in range(0, len(samples), BLOCK):
        out += demod.demodulate(samples[i:i + BLOCK])
    return bytes(out)


# Each variant is (name, applicable mode, factory). The factory takes the
# capture's metadata so a variant can follow the recorded baud rather than
# assume one.
VARIANTS = [
    ("mfsk atual", 'mfsk',
     lambda m: MFSKDemodulator(fs=m['fs'], baud=m['baud'])),
    ("mfsk contraste 0.15", 'mfsk',
     lambda m: MFSKDemodulator(fs=m['fs'], baud=m['baud'], contrast_min=0.15)),
    ("mfsk contraste 0.55", 'mfsk',
     lambda m: MFSKDemodulator(fs=m['fs'], baud=m['baud'], contrast_min=0.55)),
    ("mfsk guarda 0.30", 'mfsk',
     lambda m: MFSKDemodulator(fs=m['fs'], baud=m['baud'], guard=0.30)),
    ("mfsk guarda 0.45", 'mfsk',
     lambda m: MFSKDemodulator(fs=m['fs'], baud=m['baud'], guard=0.45)),
    ("fsk atual", 'fsk',
     lambda m: FSKDemodulator(fs=m['fs'], baud=m['baud'])),
    ("fsk squelch 0.0005", 'fsk',
     lambda m: FSKDemodulator(fs=m['fs'], baud=m['baud'], squelch=0.0005)),
]


def run_fec(meta, samples, nbytes, repeat):
    """Soft-decode an error-corrected capture: sync, then Viterbi.

    Returns the payload or b'' -- a FEC block either decodes or it does not,
    so there is no partial result to score generously. That is the point of
    it: the 8N1 path hands back plausible-looking garbage.
    """
    par = bool(meta.get('parallel'))
    npairs = len(MFSK_PAIRS)
    d = MFSKDemodulator(fs=meta['fs'], baud=meta['baud'], parallel=par)
    llr = np.concatenate([d.demodulate_soft(samples[i:i + BLOCK])
                          for i in range(0, len(samples), BLOCK)])
    if par:
        start = fec.find_sync_parallel(llr, npairs)
        if start is None:
            return b''
        return fec.decode_parallel(llr[start:], nbytes, npairs, repeat=repeat)
    start = fec.find_sync(llr)
    if start is None:
        return b''
    return fec.decode(llr[start:], nbytes, repeat=repeat)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('directory', nargs='?', default='captures')
    ap.add_argument('--detail', action='store_true',
                    help="print the recovered bytes, not just the score")
    ap.add_argument('--only', help="run just the variants whose name contains this")
    args = ap.parse_args()

    captures = recording.load_all(args.directory)
    if not captures:
        sys.exit(f"[bench] nenhuma gravacao em {args.directory}/ -- rode capture.py primeiro")

    variants = [v for v in VARIANTS if not args.only or args.only in v[0]]
    width = max(len(v[0]) for v in variants)
    totals = {v[0]: [] for v in variants}

    for samples, payload, meta in captures:
        if meta.get('kind') == 'chirp':
            continue
        if meta.get('kind') == 'fec':
            got = run_fec(meta, samples, len(payload), meta.get('fec_repeat', 2))
            ok = got == payload
            hits = sum(a == b for a, b in zip(got, payload))
            print(f"\n{meta['recorded']}  {meta.get('label','')}  FEC"
                  f"{' PARALELO' if meta.get('parallel') else ' voto'}  {len(payload)}B  "
                  f"rms={meta.get('rms',0):.4f}")
            print(f"  {'viterbi soft':<20}  {'OK, bloco inteiro' if ok else f'falhou ({hits}/{len(payload)} bytes)'}")
            totals.setdefault('viterbi soft', []).append(100.0 if ok else 0.0)
            continue
        print(f"\n{meta['recorded']}  {meta.get('label','')}  modo={meta['mode']} "
              f"{len(payload)}B  rms={meta.get('rms',0):.4f} pico={meta.get('peak',0):.3f}")
        for name, mode, factory in variants:
            if mode != meta['mode']:
                continue
            got = run(factory(meta), samples)
            matched, payload_rx, synced = score(payload, got)
            pct = 100.0 * matched / max(1, len(payload))
            totals[name].append(pct)
            flag = "sync" if synced else "SEM SYNC"
            print(f"  {name:<{width}}  {pct:5.1f}%  {matched:3d}/{len(payload)}  "
                  f"{len(got):4d}B brutos  {flag}")
            if args.detail:
                text = "".join(chr(b) if 32 <= b < 127 else "." for b in payload_rx[:len(payload)])
                print(f"  {'':<{width}}  {text}")

    print("\nmedia por variante:")
    ranked = sorted(((np.mean(v), k) for k, v in totals.items() if v), reverse=True)
    for avg, name in ranked:
        print(f"  {name:<{width}}  {avg:5.1f}%  ({len(totals[name])} gravacoes)")


if __name__ == '__main__':
    main()
