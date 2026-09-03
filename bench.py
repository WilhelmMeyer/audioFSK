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

import distortion
import fec
import recording
from modem import (FSKDemodulator, FSKModulator, MFSKDemodulator,
                   MFSKModulator, MFSK_PAIRS, MaryDemodulator, MaryModulator,
                   MARY_TONES)
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


# The frequencies each layer actually sends. The midpoints between
# neighbours are where nobody transmits, and above the top one is where only
# harmonics land -- which is what `distortion` listens to.
def layer_tones(mode):
    if mode == 'mary':
        return sorted(float(t) for t in MARY_TONES)
    if mode in ('mfsk', 'mfsk-par'):
        return sorted(float(t) for p in MFSK_PAIRS for t in p)
    if mode == 'fsk':
        return [1200.0, 2200.0]
    return None


_BASELINES = {}


def layer_baseline(mode, meta):
    """The same ratios for a clean synthetic burst of the layer.

    Cached per mode and baud: it is the leakage the modulation itself puts
    between the tones and above the band, and subtracting it is what makes the
    recorded figure a statement about the channel rather than about the
    waveform.
    """
    baud = meta.get('baud') or (1200 if mode == 'fsk' else 100)
    key = (mode, baud, meta.get('fs', 48000))
    if key not in _BASELINES:
        fs = meta.get('fs', 48000)
        factory = {'fsk': FSKModulator, 'mfsk': MFSKModulator,
                   'mfsk-par': MFSKModulator, 'mary': MaryModulator}[mode]
        _BASELINES[key] = distortion.baseline(factory(fs=fs, baud=baud),
                                              layer_tones(mode), fs=fs)
    return _BASELINES[key]


def distortion_line(meta, samples):
    """One line saying how much of this recording nobody transmitted.

    Printed for every capture of a tone layer, alongside whatever else the
    recording is being scored for. See `distortion.py` for what the two
    numbers can and cannot say -- in short, the out-of-band figure detects a
    clipping transmitter and the midpoint figure does not, and on the Bell 202
    layer the midpoint figure is not interpretable at all.
    """
    mode = meta.get('mode')
    tones = layer_tones(mode)
    if tones is None:
        return None
    r = distortion.measure(np.asarray(samples, dtype=np.float64),
                           meta.get('fs', 48000), tones)
    if r is None:
        return None
    base = layer_baseline(mode, meta)
    imd_note = ("  (entre-tons sem sentido em fsk 1200: a modulacao ocupa o meio)"
                if mode == 'fsk' else "")
    flag = "  SATURADO?" if distortion.saturated(r, base) else ""
    hc = r['harm_clean']
    harm = (f"{hc:+6.1f} dB (exc {hc - base['harm_rel']:+5.1f})" if hc is not None
            else "  sem excesso acima da banda")
    return (f"  distorcao            entre-tons {r['imd_rel']:+6.1f} dB "
            f"(exc {r['imd_rel'] - base['imd_rel']:+5.1f})   "
            f"acima da banda {harm}{flag}{imd_note}")


def run_fec(meta, samples, nbytes, repeat):
    """Soft-decode an error-corrected capture: sync, then Viterbi.

    Returns the payload or b'' -- a FEC block either decodes or it does not,
    so there is no partial result to score generously. That is the point of
    it: the 8N1 path hands back plausible-looking garbage.
    """
    if meta.get('mode') == 'mary':
        d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                            gap=meta.get('gap', 0.0),
                            band=meta.get('band', 0.0),
                            chord=bool(meta.get('chord')))
        llr = np.concatenate([d.demodulate_soft(samples[i:i + BLOCK])
                              for i in range(0, len(samples), BLOCK)])
        start = fec.find_sync(llr)
        return b'' if start is None else fec.decode(llr[start:], nbytes, repeat=repeat)

    par = bool(meta.get('parallel'))
    npairs = len(MFSK_PAIRS)
    d = MFSKDemodulator(fs=meta['fs'], baud=meta['baud'], parallel=par,
                        grouped=bool(meta.get('grouped')))
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
                  f"{' MARY' if meta.get('mode') == 'mary' else (' PARALELO' if meta.get('parallel') else ' voto')}"
                  f"  {len(payload)}B  "
                  f"rms={meta.get('rms',0):.4f}")
            print(f"  {'viterbi soft':<20}  {'OK, bloco inteiro' if ok else f'falhou ({hits}/{len(payload)} bytes)'}")
            line = distortion_line(meta, samples)
            if line:
                print(line)
            totals.setdefault('viterbi soft', []).append(100.0 if ok else 0.0)
            continue
        print(f"\n{meta['recorded']}  {meta.get('label','')}  modo={meta['mode']} "
              f"{len(payload)}B  rms={meta.get('rms',0):.4f} pico={meta.get('peak',0):.3f}")
        line = distortion_line(meta, samples)
        if line:
            print(line)
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
