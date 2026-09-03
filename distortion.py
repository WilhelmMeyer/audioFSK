"""How much of a recording is energy nobody transmitted.

The link has been graded on how many bytes came back and on how loud the
signal arrived, and neither says whether the *transmitter* was distorting.
That gap cost a measurement here: an output stage was clipping audibly across
the room, and the only thing that noticed was a person hearing it. A recording
should be able to say so by itself.

Two readings, both relative to the tones the layer actually sends, in dB:

  `imd_rel`     -- energy at the exact midpoints between neighbouring tones,
                   where nobody transmits.
  `harm_clean`  -- energy above the transmitted band, with this recording's
                   own room noise subtracted, where the harmonics of the
                   layer's tones land and nothing else does.

Why relative: every *linear* effect in this room -- the comb response,
reverberation, a truncated symbol's spectral leakage -- scales the tones and
the space between them together, so a ratio does not move with the volume. A
nonlinearity does move: its products grow faster than the signal that makes
them. That is the only discrimination a single recording can offer, and it is
why a gain sweep says far more than one reading.

WHAT WAS MEASURED. Four of these say how to read the numbers, so they are
here rather than in a commit message:

1. **`imd_rel` does not detect clipping on these layers, and the reason is
   structural.** Clip a synthetic MFSK burst progressively and it does not
   move: 0% of samples clipped reads -15.6 dB, 5.8% reads -15.5, 27.2% reads
   -15.2. M-ary is flatter still, -7.4 dB from no clipping to 81% of samples
   clipped. The midpoints are not silent to begin with: MFSK sends 100 baud
   with its tones 200 Hz apart, so the modulation's own first sidebands land
   exactly on the midpoint, and M-ary's 162 Hz grid is worse. At these baud
   rates no in-band point is more than 150 Hz from a tone, so there is
   nowhere clean to listen. The figure is still printed, against the layer's
   own leakage baseline, because a *large* excess would mean something. A
   small one means nothing.

2. **The out-of-band reading is the detector, and only after the room is
   subtracted from it.** Microphone and room noise sit above the band too and
   do not scale with the signal, so on a quiet recording they lift the raw
   ratio exactly the way a harmonic would. Measured that way, the corpus's
   *quietest and cleanest* capture (self-capture at gain 0.2) reported +7.8 dB
   of "harmonics" against +0.1 for the gain 0.9 capture recorded minutes
   earlier through the same speaker -- the metric was reporting how little
   signal there was. `harm_clean` estimates the out-of-band noise from the
   recording's own quiet windows, subtracts it in the power domain, and only
   then takes the ratio.

3. **Calibration of the 3 dB threshold, on synthetic scenes built like a real
   capture** (silence, burst, silence, plus a noise floor at -60, -45 and
   -35 dBFS). MFSK: no clipping reads -0.3 to +1.7 dB, 25% of peak removed
   reads +3.2 to +3.6, 33% reads +5.3 to +5.7, 50% reads +9.7 to +10.0. M-ary
   is less sensitive -- clean -2.5 to -1.0, and it takes 33-50% before it
   clears the threshold -- because the third harmonic of its upper tones lands
   past the 8 kHz window this listens to. Widening that window to 16 kHz did
   raise M-ary's sensitivity by about one step and was left off: the channel
   is at the noise floor above 6 kHz, so what is up there depends on the
   recording device's own filtering rather than on the link.

4. **Absence of the signature is not proof of a clean output.** The measured
   channel loses 12 dB by 4 kHz and is at the floor above 6 kHz, which is
   exactly the band the harmonics land in, so a transmitter can clip and have
   the evidence attenuated on the way to the microphone. Read a positive as
   evidence and a negative as silence.

5. **Reverberation does not move it, and that is worth stating because it
   was the obvious objection.** Reverberation is linear: convolution cannot
   put energy at a frequency the source did not have. Measured on synthetic
   scenes at 20, 40, 80 and 160 ms of tail, the out-of-band excess reads -2.1
   dB or reports nothing at all, against +5.6 for 33% of the peak clipped on
   the same burst. So the metric does separate the two -- in one direction.
   In the other it does not: a reverberant channel *hides* clipping, because
   the tail fills the quiet windows the room estimate is taken from and the
   subtraction then eats the evidence. Measured, 80 ms of reverberation plus
   33% clipping reports nothing where the clipping alone reports +5.6.

6. **It cannot tell a lossy codec from a clipping output stage, and both
   speakers on the bench are now Bluetooth.** Both are nonlinear, so both put
   energy where nothing was sent; a psychoacoustic coder decides what to
   discard by its own rules, which have nothing to do with these tones.
   Measured on a synthetic proxy (6 kHz lowpass plus coarse quantisation),
   the out-of-band excess reads +2.2 dB with no clipping anywhere -- under the
   3 dB threshold, but not by much. What *is* measured on the real Bluetooth
   corpus is reassuring and is not proof: twelve self-capture recordings
   through a Bluetooth speaker, including six at deliberately high gain,
   report -0.8 to -3.3 dB and none of them flags. Treat a flag on a Bluetooth
   path as "something nonlinear is happening", not as "the amplifier is
   clipping".

7. **It says nothing on Bell 202's midpoint.** At 1200 baud with the tones
   1000 Hz apart, the modulation covers the midpoint completely: measured on
   three recordings of the real link, `imd_rel` came out *positive*, +7.8 to
   +10.2 dB, meaning more energy between the tones than in them. That is a
   correct reading of a signal whose sidebands are its content, and a
   meaningless one as a distortion figure. `bench.py` marks it rather than
   hiding it. The out-of-band figure on those same three recordings sits +4.5
   to +6.0 dB over the layer's baseline, which is the reading that agrees with
   what was audible in the room.

No I/O and no device here, the same rule `modem.py` follows: samples in,
numbers out.
"""

import numpy as np

# Half-width of the probe around each frequency, in Hz. Wide enough to catch a
# tone whose window was truncated (which broadens it), narrow enough that a
# probe on a midpoint does not reach the tones 81 Hz either side of it in the
# M-ary layer.
PROBE_HZ = 25.0

# How far above the layer's own leakage baseline `harm_rel` has to sit before
# the recording is called saturated. Calibrated on the synthetic sweep above,
# where +3 dB falls between 3.2% and 5.8% of samples clipped -- distortion
# that is audible and well past what a working link should carry. It is not
# calibrated against a *recorded* clipping case, because the corpus does not
# contain one that was confirmed independently; when one exists, re-derive it
# here rather than trusting this number.
HARM_EXCESS_DB = 3.0


def active_segment(samples, fs, hop_ms=20.0, floor_db=-12.0):
    """The stretch that actually carries the burst, first window to last.

    Silence before and after is not neutral: it leaves the room floor in the
    numerator and takes the tones out of the denominator, so both ratios read
    worse the longer the recording's tail. Windows within `floor_db` of the
    loudest count as signal.
    """
    n = max(1, int(hop_ms / 1000 * fs))
    if len(samples) < 2 * n:
        return samples
    frames = samples[:len(samples) // n * n].reshape(-1, n)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    if not rms.any():
        return samples
    keep = np.nonzero(rms >= rms.max() * 10 ** (floor_db / 20.0))[0]
    if len(keep) < 2:
        return samples
    return samples[keep[0] * n:(keep[-1] + 1) * n]


def midpoints(tones):
    """The exact midpoint between each pair of neighbouring tones."""
    t = sorted(tones)
    return [(a + b) / 2.0 for a, b in zip(t, t[1:])]


def _spectrum(seg, fs):
    win = np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(seg * win)) ** 2
    return np.fft.rfftfreq(len(seg), 1 / fs), spec


def _band_power(freq, spec, lo, hi):
    mask = (freq >= lo) & (freq <= hi)
    return float(spec[mask].sum()) if mask.any() else 0.0


def _ratios(seg, fs, tones, probe_hz, above_to):
    freq, spec = _spectrum(seg, fs)
    tone_p = sum(_band_power(freq, spec, t - probe_hz, t + probe_hz)
                 for t in tones)
    mids = midpoints(tones)
    mid_p = sum(_band_power(freq, spec, m - probe_hz, m + probe_hz)
                for m in mids)
    # Start clear of the top tone's own skirt.
    top = (tones[-1] + (tones[-1] - tones[-2]) / 2.0 if len(tones) > 1
           else tones[-1] * 1.5)
    hi = min(above_to, fs / 2)
    above_p = _band_power(freq, spec, top, hi)

    # Per probe, so a ten-tone layer compares with a two-tone one: the sums
    # above count a different number of probes on each side. The out-of-band
    # stretch is one wide band, so it is normalised by its width in probes.
    def db(p, n):
        return 10.0 * np.log10(max(p / max(n, 1e-9), 1e-30))

    t_db = db(tone_p, len(tones))
    return (t_db,
            db(mid_p, max(1, len(mids))) - t_db,
            db(above_p, max(1.0, (hi - top) / (2 * probe_hz))) - t_db)


def _powers(seg, fs, tones, probe_hz, above_to):
    """Linear power per probe width: (tones, midpoints, above the band).

    Linear, not dB, because these get *subtracted* -- the room's contribution
    above the band has to come off the signal's before any ratio is taken, and
    a difference of decibels is not a difference of powers.
    """
    freq, spec = _spectrum(seg, fs)
    tone_p = sum(_band_power(freq, spec, t - probe_hz, t + probe_hz)
                 for t in tones) / len(tones)
    mids = midpoints(tones)
    mid_p = (sum(_band_power(freq, spec, m - probe_hz, m + probe_hz)
                 for m in mids) / len(mids)) if mids else 0.0
    top = (tones[-1] + (tones[-1] - tones[-2]) / 2.0 if len(tones) > 1
           else tones[-1] * 1.5)
    hi = min(above_to, fs / 2)
    width = max(1.0, (hi - top) / (2 * probe_hz))
    return tone_p, mid_p, _band_power(freq, spec, top, hi) / width


def measure(samples, fs, tones, probe_hz=PROBE_HZ, above_to=8000.0,
            window_s=1.0):
    """`{tones_db, imd_rel, harm_rel, harm_rel_worst, seconds}`, or None.

    `harm_rel_worst` is the worst one-second window rather than the average
    over the burst. Clipping is driven by the peak, so it can occupy a small
    part of a long recording and be diluted to nothing by the rest -- a 25 s
    capture averages away a second of a flattened output.
    """
    seg = np.asarray(active_segment(samples, fs), dtype=np.float64)
    if len(seg) < 64:
        return None
    tones = sorted(float(t) for t in tones)
    t_db, imd, harm = _ratios(seg, fs, tones, probe_hz, above_to)
    peak_rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0

    n = int(window_s * fs)
    worst = harm
    if n >= 4096:
        # Only windows that actually carry the burst. A window sitting in a
        # gap between trials has almost no tone energy in its denominator, so
        # its ratio explodes on room noise alone -- measured, that reported
        # +24 dB of "harmonics" on the quietest recording in the corpus, which
        # is the loudest possible way to be wrong. Judge a window against the
        # strongest one, not against silence.
        wins = [(i, _ratios(seg[i:i + n], fs, tones, probe_hz, above_to))
                for i in range(0, len(seg) - n + 1, n)]
        if wins:
            loudest = max(w[1][0] for w in wins)
            live = [w[1][2] for w in wins if w[1][0] >= loudest - 12.0]
            if live:
                worst = max(live)
    # The out-of-band reading has to have the room subtracted from it before
    # it means anything. Microphone and room noise sit above the band too and
    # do not scale with the signal, so on a quiet recording they raise
    # `harm_rel` exactly the way a harmonic would -- and the ratio then
    # reports the *weakest* recording in the corpus as the most distorted.
    # Measured: the 0.2-gain self capture read +7.8 dB of "harmonics" that
    # way, against +0.1 for the 0.9-gain one recorded minutes earlier through
    # the same speaker.
    #
    # So estimate the out-of-band noise power from this recording's own quiet
    # windows, subtract it from the loud ones, and only then take the ratio.
    # What survives is energy that arrived *with* the signal.
    full = np.asarray(samples, dtype=np.float64)
    harm_clean = None
    if n >= 4096 and len(full) >= 2 * n:
        loud, quiet = [], []
        for i in range(0, len(full) - n + 1, n):
            w = full[i:i + n]
            rms = float(np.sqrt(np.mean(w ** 2)))
            p = _powers(w, fs, tones, probe_hz, above_to)
            (loud if rms >= peak_rms * 10 ** (-12.0 / 20.0)
             else quiet).append(p)
        if loud and quiet:
            room = float(np.median([q[2] for q in quiet]))
            best = max(loud, key=lambda p: p[2] - room)
            excess = best[2] - room
            # Everything above the band was the room, so there is nothing to
            # attribute to the transmitter. None rather than a large negative
            # number, which would read like a measurement.
            if excess > 0 and best[0] > 0:
                harm_clean = 10.0 * np.log10(excess / best[0])

    return {
        'tones_db': t_db,
        'imd_rel': imd,
        'harm_rel': harm,
        'harm_rel_worst': worst,
        # Out-of-band energy with the room's own contribution removed,
        # relative to the tones. None when nothing above the band exceeded
        # the room, or when the recording has no quiet window to estimate it
        # from. This is the figure `saturated()` reads.
        'harm_clean': harm_clean,
        'seconds': len(seg) / fs,
    }


def baseline(modulator, tones, nbits=400, seed=0, fs=48000, **kw):
    """The same two ratios for a clean, synthetic burst of the same layer.

    This is the only honest reference: the modulation itself puts energy
    between the tones and, through the symbol edges, a little above the band.
    Subtracting a layer's own leakage is what turns the readings from "what
    this waveform looks like" into "what the channel did to it".
    """
    rng = np.random.default_rng(seed)
    bits = list(rng.integers(0, 2, nbits))
    sig = np.asarray(modulator.modulate_bits(bits), dtype=np.float64)
    peak = float(np.max(np.abs(sig))) if len(sig) else 0.0
    if peak > 0:
        sig = sig / peak
    return measure(sig, fs, tones, **kw)


def saturated(reading, base, threshold_db=HARM_EXCESS_DB):
    """Does this recording show a transmitter running past its ceiling?

    Only the out-of-band figure votes, and only the room-subtracted one
    (`harm_clean`), against the layer's own synthetic leakage: the midpoint
    reading was measured not to move under clipping at all, and the raw
    out-of-band ratio moves with how quiet the recording was.

    A False is weak evidence on this hardware -- the channel is 12 dB down by
    4 kHz and at the floor above 6 kHz, which is exactly where the harmonics
    land, so a clipping transmitter can have its evidence attenuated on the
    way to the microphone. Read a True as evidence and a False as silence.
    """
    if reading is None or base is None or reading.get('harm_clean') is None:
        return False
    return (reading['harm_clean'] - base['harm_rel']) >= threshold_db
