"""How much of the M-ary error rate is timing, and how much is the channel.

The demodulator acquires its symbol clock with an early/late gate: three
candidate windows per symbol, keep the best, nudge the next one. That is a
tracking loop, and a tracking loop can only be judged against knowing the
answer. This probe supplies the answer by brute force -- it freezes the clock
(`steer=False`) and tries every start offset within a symbol, scoring each --
and reports the best frozen clock beside what the gate actually achieved on
the identical samples.

The gap between the two columns is the prize available to better
synchronisation, and nothing else. If it is small, timing is not what is
costing bits and a sync burst would buy nothing; if it is large, it is worth
building. Measuring it first is cheaper than building it and hoping.

Bit accuracy, not block recovery, is the figure of merit: with a handful of
recordings, neighbouring settings score 8% and 22% purely from which blocks
happened to land, while bit accuracy is stable. Blocks recovered are reported
too, as the thing anyone actually cares about, but do not tune on them.

    ./venv/bin/python align.py captures-self
"""

import argparse
import sys

import numpy as np

import fec
import recording
import spectro
from modem import (MaryDemodulator, MARY_TONES, chirp, find_chirp,
                   find_chirp_pair, SYNC_CHIRP)

BLOCK = 2048


def soft(demod, samples):
    """Feed a capture through in blocks, as the live path would."""
    parts = [demod.demodulate_soft(samples[i:i + BLOCK])
             for i in range(0, len(samples), BLOCK)]
    parts = [p for p in parts if len(p)]
    return np.concatenate(parts) if parts else np.zeros(0)


def bit_accuracy(llr, payload, repeat):
    """Fraction of transmitted bits that came back with the right sign.

    Measured at the alignment that agrees best, always -- never at the one
    `find_sync` happened to pick. Two rules in one column is not a
    measurement: taking the sync position when sync was found and the best
    slide when it was not makes the failures look *better* than the successes,
    because the best slide is chosen to flatter and the sync position is not.
    Observed here before the fix -- the setting with the worst block recovery
    reported the highest bit accuracy, which is not a paradox about the
    channel but two different rulers.

    Sync word and coded block both, so this measures the demodulator alone,
    with the Viterbi decoder's repair work excluded. Blocks recovered stay the
    honest end-to-end number and are reported separately.
    """
    want = np.asarray(fec.frame(payload, repeat=repeat), dtype=np.int8)
    llr = np.asarray(llr, dtype=np.float64)
    if len(llr) < len(want):
        return None
    scores = np.correlate(np.sign(llr), 2.0 * want - 1.0, mode='valid') / len(want)
    if not len(scores):
        return None
    # A normalised correlation of +-1 bits is 2*accuracy - 1.
    return float(0.5 * (np.max(scores) + 1.0))


def genie_floor(samples, payload, meta, sps, repeat, skip):
    """The per-tone divisor a perfect pilot scheme would converge to, or None.

    For each tone, the average energy it arrived with in the symbols where it
    was actually transmitted. That is the channel's gain at that frequency,
    measured rather than inferred, and dividing by it is what a pilot symbol
    would eventually buy.

    It is a ceiling, not a proposal: no real scheme gets every symbol's worth
    of evidence for free. If the ceiling is close to what the blind estimate
    already achieves, pilots are not worth their air time, and that is the
    only reason to compute it.
    """
    want = spectro.tx_tone_indices(payload, repeat)
    # Deliberately the *same* offset the frozen-clock column used, not one
    # found independently. Two alignments and two divisors changing at once
    # produce a difference that cannot be attributed to either -- which is
    # what the first version of this probe did, and it made the perfect floor
    # look ten points worse than the blind one for reasons that were partly
    # its worse alignment.
    start = skip
    ones = np.ones(len(MARY_TONES))
    d = MaryDemodulator(fs=meta['fs'], baud=meta['baud'], steer=False,
                        skip=start, floor_fixed=ones,
                        gap=meta.get('gap', 0.0), band=meta.get('band', 0.0),
                        chord=bool(meta.get('chord')))
    # With the divisor pinned at one, the `norm` the demodulator yields is the
    # raw per-tone energy -- no separate accessor needed.
    decided, energies = [], []
    for i, _c, n in _stream(d, samples):
        decided.append(i)
        energies.append(n)
    if len(decided) < len(want) // 2:
        return None, start

    # Which transmitted symbol does the first decoded window hold? The frozen
    # clock starts at the best-scoring offset, which is a symbol boundary but
    # not necessarily the burst's first symbol. Slide the known sequence
    # against the decided one and take the lag that agrees most.
    lag, hits = 0, -1
    for k in range(0, max(1, len(decided) - len(want) // 2)):
        n = min(len(want), len(decided) - k, 200)
        if n < 60:
            break
        h = sum(decided[k + j] == want[j] for j in range(n)) / n
        if h > hits:
            lag, hits = k, h
    if hits < 0.4:
        return None, start

    # Two divisors, and which one is right is the whole question.
    #
    #   sinal  the energy tone t arrives with in the symbols where it *was*
    #          transmitted: the channel's gain at that frequency. This is what
    #          a pilot symbol can measure, and the obvious thing to divide by.
    #   ruido  the energy tone t shows in the symbols where it was *not*
    #          transmitted: the noise floor at that frequency. This is the
    #          perfect version of what the blind running estimate already
    #          approximates, and dividing by it is the likelihood ratio the
    #          decision actually wants.
    sig = np.zeros(len(MARY_TONES));  nsig = np.zeros(len(MARY_TONES))
    noi = np.zeros(len(MARY_TONES));  nnoi = np.zeros(len(MARY_TONES))
    for j, t in enumerate(want):
        k = lag + j
        if k >= len(energies):
            break
        e = energies[k]
        sig[t] += e[t]
        nsig[t] += 1
        for u in range(len(MARY_TONES)):
            if u != t:
                noi[u] += e[u]
                nnoi[u] += 1
    if not (nsig.all() and nnoi.all()):
        return None, start
    return (sig / nsig, noi / nnoi), start


def _stream(demod, samples):
    for i in range(0, len(samples), BLOCK):
        yield from demod._symbols(samples[i:i + BLOCK])


def probe(samples, payload, meta, step):
    fs, baud = meta['fs'], meta['baud']
    sps = int(fs / baud)
    repeat = meta.get('fec_repeat', 1) or 1
    kw = dict(fs=fs, baud=baud, gap=meta.get('gap', 0.0),
              band=meta.get('band', 0.0), chord=bool(meta.get('chord')))

    d = MaryDemodulator(**kw)
    llr = soft(d, samples)
    gate_acc = bit_accuracy(llr, payload, repeat)
    gate_ok = (fec.find_sync(llr) is not None
               and fec.decode(llr[fec.find_sync(llr):], len(payload),
                              repeat=repeat) == payload)

    best = (-1.0, 0, False)
    for skip in range(0, sps, step):
        d = MaryDemodulator(steer=False, skip=skip, **kw)
        llr = soft(d, samples)
        acc = bit_accuracy(llr, payload, repeat)
        if acc is None:
            continue
        start = fec.find_sync(llr)
        ok = (start is not None
              and fec.decode(llr[start:], len(payload), repeat=repeat) == payload)
        if acc > best[0]:
            best = (acc, skip, ok)

    # What the sync burst finds, when the capture carries one. This is the
    # only column that a receiver could actually produce: the frozen-clock
    # column knows the answer by brute force, and this one has to earn it.
    chirp_res = (None, None, None)
    pair_res = (None, None, None)
    if meta.get('sync_chirp'):
        tmpl = chirp(fs, *SYNC_CHIRP)
        hush = int(meta.get('sync_hush', 0.0) * fs)
        at = find_chirp(samples, tmpl)
        if at is not None:
            skip = at + hush
            d = MaryDemodulator(steer=False, skip=skip, **kw)
            llr = soft(d, samples)
            acc = bit_accuracy(llr, payload, repeat)
            st = fec.find_sync(llr)
            ok = (st is not None
                  and fec.decode(llr[st:], len(payload), repeat=repeat) == payload)
            chirp_res = (acc, ok, skip)

        # Both sweeps: start from the first, period from the interval.
        span = meta.get('sync_span_symbols', 0.0)
        pair = find_chirp_pair(samples, tmpl, min_gap=int(0.5 * span * sps)) if span else None
        if pair is not None:
            first, second = pair
            period = (second - first) / span
            # A period wildly off nominal means one of the peaks was not a
            # sweep. Trusting it would be worse than not having it.
            if 0.98 * sps <= period <= 1.02 * sps:
                skip2 = first + int(round(hush * period / sps))
                d = MaryDemodulator(steer=False, skip=skip2, period=period, **kw)
                llr = soft(d, samples)
                acc = bit_accuracy(llr, payload, repeat)
                st = fec.find_sync(llr)
                ok = (st is not None
                      and fec.decode(llr[st:], len(payload), repeat=repeat) == payload)
                pair_res = (acc, ok, period)

    floors, start = genie_floor(samples, payload, meta, sps, repeat, best[1])
    genie = [(None, None), (None, None)]
    if floors is not None:
        for i, f in enumerate(floors):
            d = MaryDemodulator(steer=False, skip=start, floor_fixed=f, **kw)
            llr = soft(d, samples)
            acc = bit_accuracy(llr, payload, repeat)
            st = fec.find_sync(llr)
            ok = (st is not None
                  and fec.decode(llr[st:], len(payload), repeat=repeat) == payload)
            genie[i] = (acc, ok)
    return gate_acc, gate_ok, best, genie, chirp_res, pair_res


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('directory', nargs='?', default='captures-self')
    ap.add_argument('--step', type=int, default=16,
                    help="passo da busca, em amostras (480 = um simbolo)")
    args = ap.parse_args()

    caps = [c for c in recording.load_all(args.directory)
            if c[2].get('kind') == 'fec' and c[2].get('mode') == 'mary']
    if not caps:
        sys.exit(f"[align] nenhuma captura mary com --fec em {args.directory}/")

    gate_accs, best_accs = [], []
    sig_accs, noi_accs, chirp_accs, chirp_err = [], [], [], []
    pair_accs, periods = [], []
    gate_blocks = best_blocks = sig_blocks = noi_blocks = 0
    chirp_blocks = pair_blocks = 0
    print(f"{'gravacao':<18} {'gate':>7} {'travado':>8} {'/sinal':>8} "
          f"{'/ruido':>8} {'skip':>6}")
    for samples, payload, meta in caps:
        (g_acc, g_ok, (b_acc, b_skip, b_ok), genie,
         (c_acc, c_ok, c_skip), (p_acc, p_ok, p_period)) = probe(
            samples, payload, meta, args.step)
        if c_acc is not None:
            chirp_accs.append(c_acc)
            chirp_blocks += bool(c_ok)
            # Both are symbol phases, so compare them modulo a symbol: the
            # sweep gives an absolute index in the recording and the brute
            # force searches only within one symbol, and subtracting them raw
            # reported a 25000-sample error for an alignment that was right.
            sps = int(meta['fs'] / meta['baud'])
            d = (c_skip - b_skip) % sps
            chirp_err.append(min(d, sps - d))
        if p_acc is not None:
            pair_accs.append(p_acc)
            pair_blocks += bool(p_ok)
            periods.append(p_period)
        if g_acc is None or b_acc is None:
            print(f"{meta['recorded']:<18}  captura curta demais, ignorada")
            continue
        gate_accs.append(g_acc)
        best_accs.append(b_acc)
        gate_blocks += bool(g_ok)
        best_blocks += bool(b_ok)
        cells = []
        for acc_list, blocks_name, (acc, ok) in (
                (sig_accs, 'sig', genie[0]), (noi_accs, 'noi', genie[1])):
            if acc is None:
                cells.append("      --")
                continue
            acc_list.append(acc)
            if blocks_name == 'sig':
                sig_blocks += bool(ok)
            else:
                noi_blocks += bool(ok)
            cells.append(f"{100*acc:7.1f}%")
        print(f"{meta['recorded']:<18} {100*g_acc:6.1f}% {100*b_acc:7.1f}% "
              f"{cells[0]} {cells[1]} {b_skip:6d}")

    n = len(caps)
    print(f"\nmedia de bits certos")
    print(f"  gate early/late, como esta hoje            {100*np.mean(gate_accs):5.1f}%"
          f"   {gate_blocks}/{n} blocos")
    print(f"  relogio travado no melhor offset           {100*np.mean(best_accs):5.1f}%"
          f"   {best_blocks}/{n} blocos")
    if sig_accs:
        print(f"  travado, dividindo pelo GANHO por tom      {100*np.mean(sig_accs):5.1f}%"
              f"   {sig_blocks}/{n} blocos   <- o que um piloto mede")
    if noi_accs:
        print(f"  travado, dividindo pelo RUIDO por tom      {100*np.mean(noi_accs):5.1f}%"
              f"   {noi_blocks}/{n} blocos   <- o que o codigo ja estima sozinho")
    if chirp_accs:
        print(f"  varredura de sincronismo no inicio do frame  "
              f"{100*np.mean(chirp_accs):5.1f}%   {chirp_blocks}/{len(chirp_accs)}"
              f" blocos   <- o S, alinhamento que um receptor consegue de fato")
        print(f"    erro medio contra o melhor offset: "
              f"{np.mean(chirp_err):.0f} amostras de {int(caps[0][2]['fs']/caps[0][2]['baud'])}")
    if pair_accs:
        print(f"  duas varreduras: inicio E periodo medidos    "
              f"{100*np.mean(pair_accs):5.1f}%   {pair_blocks}/{len(pair_accs)}"
              f" blocos   <- S no comeco e no fim")
        print(f"    periodo medido: {np.mean(periods):.2f} amostras por simbolo "
              f"(nominal {int(caps[0][2]['fs']/caps[0][2]['baud'])}), "
              f"desvio {np.std(periods):.2f}")
    print("\nlinha 2 - linha 1 = o que uma sincronizacao melhor pode render.")
    print("linha 4 - linha 2 = o teto do estimador de piso, sabendo a resposta.")
    print("linha 3          = um piloto por tom, no melhor caso possivel.")


if __name__ == '__main__':
    main()
