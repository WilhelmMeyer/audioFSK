"""Throwaway: BER tolerance of four FEC variants on a 64-byte block."""
import csv
import os
import sys, numpy as np
from scipy.special import erfcinv
from multiprocessing import Pool
sys.path.insert(0, '/home/willj/audioFSK')
import fec

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resultado.csv')

BASE = 20260907
NBYTES = 64
NTRIALS = 200
BERS = [round(0.02 + 0.01 * i, 2) for i in range(39)]  # 0.02 .. 0.40

VARIANTS = [
    ("1/2 hard",      fec.POLYS_R12, 1, True),
    ("1/2 soft",      fec.POLYS_R12, 1, False),
    ("1/3 soft",      fec.POLYS_R13, 1, False),
    ("1/3 soft r=2",  fec.POLYS_R13, 2, False),
]


def sigma_for(p):
    # BPSK x=+-1 in AWGN: P(error) = Q(1/sigma) = 0.5*erfc(1/(sigma*sqrt2))
    return 1.0 / (np.sqrt(2.0) * erfcinv(2.0 * p))


def run_point(job):
    vi, bi = job
    name, polys, repeat, hard = VARIANTS[vi]
    p = BERS[bi]
    sig = sigma_for(p)
    rng = np.random.default_rng([BASE, vi, bi])
    ok = 0
    flips = 0
    tot = 0
    for _ in range(NTRIALS):
        data = rng.integers(0, 256, NBYTES, dtype=np.uint8).tobytes()
        coded = fec.encode(data, polys=polys, depth=16, repeat=repeat)
        x = 2.0 * coded.astype(np.float64) - 1.0
        y = x + rng.normal(0.0, sig, len(x))
        flips += int(np.sum(np.sign(y) != np.sign(x)))
        tot += len(x)
        llr = np.sign(y) if hard else y
        got = fec.decode(llr, NBYTES, polys=polys, depth=16, repeat=repeat)
        ok += (got == data)
    return vi, bi, ok, flips / tot


def selftest():
    for vi, (name, polys, repeat, hard) in enumerate(VARIANTS):
        data = bytes(range(64))
        coded = fec.encode(data, polys=polys, depth=16, repeat=repeat)
        llr = 2.0 * coded.astype(np.float64) - 1.0
        assert fec.decode(llr, NBYTES, polys=polys, depth=16, repeat=repeat) == data, name
    print("selftest ok: noiseless round-trip byte-identical for all 4 variants")


def last_contiguous(counts, need):
    best = None
    for bi, c in enumerate(counts):
        if c >= need:
            best = BERS[bi]
        else:
            break
    return best


if __name__ == '__main__':
    selftest()
    jobs = [(vi, bi) for vi in range(len(VARIANTS)) for bi in range(len(BERS))]
    res = {}
    real = {}
    with Pool(12) as pool:
        for vi, bi, ok, fr in pool.imap_unordered(run_point, jobs):
            res[(vi, bi)] = ok
            real[(vi, bi)] = fr
    print()
    print(f"payload {NBYTES} B, {NTRIALS} trials/point, seed base {BASE}, depth=16, no find_sync")
    print()
    print("| variante | BER ate 100% integro | BER ate 90% integro |")
    print("|---|---|---|")
    rows = []
    for vi, (name, *_r) in enumerate(VARIANTS):
        counts = [res[(vi, bi)] for bi in range(len(BERS))]
        a = last_contiguous(counts, NTRIALS)
        b = last_contiguous(counts, int(0.9 * NTRIALS))
        f = lambda v: ("< 0.02" if v is None else (">= 0.40" if v == BERS[-1] else f"{v:.2f}"))
        print(f"| {name} | {f(a)} | {f(b)} |")
        rows.append((name, counts))
    print()
    print("counts of 200 trials delivering the block byte-identical, BER 0.02..0.40:")
    for name, counts in rows:
        print(f"{name:14s} " + " ".join(f"{c:3d}" for c in counts))
    print()
    print("realized flip fraction vs nominal (variant 0):")
    print("  " + " ".join(f"{real[(0,bi)]:.3f}" for bi in range(len(BERS))))

    with open(CSV_PATH, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["variante", "ber", "trials", "integros"])
        for vi, (name, *_r) in enumerate(VARIANTS):
            for bi in range(len(BERS)):
                w.writerow([name, BERS[bi], NTRIALS, res[(vi, bi)]])
    print(f"\nwrote {CSV_PATH}")
