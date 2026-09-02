"""Forward error correction: convolutional coding with soft-decision Viterbi.

The acoustic link delivers 10-25% of its bits wrong. That is not a channel a
CRC can rescue -- a CRC only tells you the block is ruined -- and it is far
past what a retransmit strategy can carry, since at that rate almost every
block is ruined. The bits have to be repairable where they land.

Two things make that possible here, and both are free.

The first is that the demodulator already knows more than it says. Deciding
each tone pair as a hard 0 or 1 and then counting votes throws away how
*confident* each pair was; a pair that split 51/49 counts exactly as much as
one that split 99/1. Feeding the analog confidence to the decoder instead is
worth roughly 2 dB, which on this link is the difference between a decodable
block and a ruined one.

The second is that dropping UART framing inside a block removes an entire
failure mode rather than mitigating it. Under 8N1 a single corrupted start or
stop bit shifts every byte that follows, so one bad bit destroys the rest of
the block. A fixed-length block has nothing to shift.

No audio, no I/O, no state: bits and log-likelihoods in, bytes out. The
layering rule that keeps modem.py testable applies here too.
"""

import numpy as np

# Constraint length 7, the NASA/Voyager standard polynomials. Widely used
# because they are the best known K=7 pair, and being standard means the
# behaviour is documented far better than anything hand-rolled.
K = 7
POLYS_R12 = (0o171, 0o133)
POLYS_R13 = (0o171, 0o133, 0o165)

NSTATES = 1 << (K - 1)


def _parity(x):
    x ^= x >> 8
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return x & 1


def _tables(polys):
    """Output bits and next state for every (state, input) pair.

    Precomputed once per rate: the encoder and the decoder both walk the same
    trellis, and building it in one place means they cannot disagree about it.
    """
    out = np.zeros((NSTATES, 2, len(polys)), dtype=np.int8)
    nxt = np.zeros((NSTATES, 2), dtype=np.int32)
    for state in range(NSTATES):
        for bit in (0, 1):
            reg = (bit << (K - 1)) | state
            for i, p in enumerate(polys):
                out[state, bit, i] = _parity(reg & p)
            nxt[state, bit] = reg >> 1
    return out, nxt


_TABLES = {POLYS_R12: _tables(POLYS_R12), POLYS_R13: _tables(POLYS_R13)}


def encode_bits(bits, polys=POLYS_R12):
    """Convolutionally encode, flushing the register at the end.

    The tail of K-1 zero bits costs a little rate and buys a decoder that
    knows where it finished: without it the last few bits are decoded from a
    state the decoder has to guess, and they are the bits most likely to be
    wrong.
    """
    out_tab, nxt_tab = _TABLES[polys]
    state = 0
    coded = []
    for bit in list(bits) + [0] * (K - 1):
        coded.extend(out_tab[state, bit])
        state = nxt_tab[state, bit]
    return np.array(coded, dtype=np.int8)


def decode_soft(llr, nbits, polys=POLYS_R12):
    """Viterbi over the trellis, taking log-likelihood ratios.

    `llr` is positive where the channel leans towards a 1 and negative
    towards 0, with magnitude meaning confidence. A hard decision is just the
    special case where every magnitude is the same, so this decoder accepts
    both -- but handing it real confidences is the whole point.

    Vectorised over the 64 states rather than looped: at 100 baud the decoder
    must keep up with the audio thread, and a per-state Python loop does not.
    """
    out_tab, nxt_tab = _TABLES[polys]
    n = len(polys)
    steps = nbits + K - 1
    llr = np.asarray(llr, dtype=np.float64)[:steps * n].reshape(-1, n)
    if len(llr) < steps:
        raise ValueError(f"precisa de {steps * n} llrs, recebi {llr.size}")

    # Branch metric: agreement between the expected output bits and the
    # channel's opinion. Expected bit 1 wants positive llr, bit 0 negative.
    signs = 2 * out_tab.astype(np.float64) - 1          # (state, input, n)

    INF = 1e18
    metric = np.full(NSTATES, -INF)
    metric[0] = 0.0                                      # encoder starts at 0
    back = np.zeros((steps, NSTATES), dtype=np.int8)

    prev_for = np.zeros((NSTATES, 2), dtype=np.int32)
    inp_for = np.zeros((NSTATES, 2), dtype=np.int8)
    seen = np.zeros(NSTATES, dtype=np.int8)
    for state in range(NSTATES):
        for bit in (0, 1):
            ns = nxt_tab[state, bit]
            prev_for[ns, seen[ns]] = state
            inp_for[ns, seen[ns]] = bit
            seen[ns] += 1

    for t in range(steps):
        # Score of each (state, input) branch against this step's llrs.
        branch = (signs * llr[t]).sum(axis=2)             # (state, input)
        cand = np.empty((NSTATES, 2))
        for j in (0, 1):
            src = prev_for[:, j]
            cand[:, j] = metric[src] + branch[src, inp_for[:, j]]
        best = np.argmax(cand, axis=1)
        metric = cand[np.arange(NSTATES), best]
        back[t] = best
        metric -= metric.max()                            # keep it bounded

    # The tail drove the encoder back to state 0, so that is where to start.
    bits = np.zeros(steps, dtype=np.int8)
    state = 0
    for t in range(steps - 1, -1, -1):
        j = back[t, state]
        prev = prev_for[state, j]
        bits[t] = inp_for[state, j]
        state = prev
    return bits[:nbits]


def interleave_index(n, depth):
    """Block interleaver as a permutation, so both directions share one map.

    Errors on this link arrive in runs -- a moment of drifting symbol timing
    takes out a stretch of bits together -- and a convolutional code is at its
    worst against exactly that. Spreading consecutive coded bits far apart
    turns one long run into many isolated errors, which is the case the code
    is good at.
    """
    rows = int(np.ceil(n / depth))
    idx = np.arange(rows * depth).reshape(rows, depth).T.ravel()
    return idx[idx < n]


# A 31-bit maximum-length sequence. Its defining property is that shifting it
# against itself gives -1 everywhere except at perfect alignment, where it
# gives 31 -- so correlating it against the soft stream produces one sharp
# peak and no runner-up. Counting symbols instead does not work: the early/late
# gate consumes a different number of samples per symbol as it steers, so the
# block start drifts by a symbol or two over a preamble, and a block that
# starts one bit late decodes to nothing.
SYNC = np.array([1,0,0,1,0,1,0,1,1,0,0,1,1,1,1,1,
                 0,0,0,1,1,0,1,1,1,0,1,0,1,0,0], dtype=np.int8)


def frame(data, polys=POLYS_R13, depth=16, repeat=1):
    """Sync word followed by the coded block, as bits ready to modulate."""
    return np.concatenate([SYNC, encode(data, polys, depth, repeat)])


def find_sync(llr, threshold=0.55):
    """Where the block starts in a stream of soft values, or None.

    Correlates against the sync word and takes the sharpest peak. The
    threshold is on the normalised score, so it means the same thing whatever
    the signal level -- the same reason every decision in this path is a ratio.
    """
    llr = np.asarray(llr, dtype=np.float64)
    if len(llr) < len(SYNC):
        return None
    want = 2.0 * SYNC - 1.0
    scores = np.correlate(np.sign(llr), want, mode='valid') / len(SYNC)
    best = int(np.argmax(scores))
    if scores[best] < threshold:
        return None
    return best + len(SYNC)


def bytes_to_bits(data):
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder='little')


def bits_to_bytes(bits):
    bits = np.asarray(bits, dtype=np.uint8)
    bits = bits[:len(bits) // 8 * 8]
    return np.packbits(bits, bitorder='little').tobytes()


def encode(data, polys=POLYS_R13, depth=16, repeat=1):
    """Bytes in, coded bits out: encoded, repeated, then interleaved.

    Repetition extends the code past what the polynomials alone reach. Rate
    1/3 holds to about 16% of bits wrong and this link reaches 25% at its
    worst, so the margin has to come from somewhere; `repeat` is the honest
    way to buy it, since combining copies of a bit is exactly addition in the
    log-likelihood domain and costs no guesswork about polynomials.

    Interleaving is applied *after* repetition, deliberately: copies of the
    same bit end up far apart in time, so a burst that destroys one copy
    leaves the others intact. Repeating adjacent bits would put every copy
    inside the same burst and buy nothing.
    """
    coded = encode_bits(bytes_to_bits(data), polys)
    if repeat > 1:
        coded = np.tile(coded, repeat)
    return coded[interleave_index(len(coded), depth)]


def decode(llr, nbytes, polys=POLYS_R13, depth=16, repeat=1):
    """Coded llrs in, bytes out. `nbytes` is the length the sender used."""
    nbits = nbytes * 8
    ncoded = (nbits + K - 1) * len(polys)
    total = ncoded * repeat

    llr = np.asarray(llr, dtype=np.float64)[:total]
    if len(llr) < total:
        llr = np.concatenate([llr, np.zeros(total - len(llr))])

    deint = np.zeros(total)
    deint[interleave_index(total, depth)] = llr
    # Summing the copies is optimal combining, not a shortcut: for independent
    # observations of one bit the log-likelihoods simply add, so a confident
    # copy outweighs a doubtful one without any thresholding.
    return bits_to_bytes(decode_soft(deint.reshape(repeat, ncoded).sum(axis=0),
                                     nbits, polys))
