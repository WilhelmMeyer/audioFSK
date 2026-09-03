import numpy as np
import scipy.signal as signal

class FSKModulator:
    def __init__(self, fs=48000, baud=1200, f_space=2200, f_mark=1200):
        self.fs = fs
        self.baud = baud
        self.f_space = f_space # 0
        self.f_mark = f_mark   # 1
        self.samples_per_symbol = int(fs / baud)
        self.phase = 0.0

    def reset(self):
        """Drop carrier phase. Only between streams -- resetting mid-stream
        splices a discontinuity into the carrier, which clicks and spreads
        energy out of band."""
        self.phase = 0.0

    def modulate_byte(self, byte_val):
        # UART framing: 1 start bit (0), 8 data bits (LSB first), 1 stop bit (1)
        bits = [0] # Start bit
        for i in range(8):
            bits.append((byte_val >> i) & 1)
        bits.append(1) # Stop bit
        return self.modulate_bits(bits)

    def modulate_bits(self, bits):
        # Continuous phase FSK
        samples = []
        for b in bits:
            f = self.f_mark if b == 1 else self.f_space
            t = np.arange(self.samples_per_symbol) / self.fs
            # Phase accumulation to keep continuous phase
            omega = 2 * np.pi * f
            symbol_samples = np.sin(omega * t + self.phase)
            self.phase += omega * self.samples_per_symbol / self.fs
            self.phase %= 2 * np.pi
            samples.append(symbol_samples)
        return np.concatenate(samples) if samples else np.array([])
        
    def modulate(self, data: bytes):
        chunks = []
        for b in data:
            chunks.append(self.modulate_byte(b))
        if chunks:
            return np.concatenate(chunks)
        return np.array([])

class FSKDemodulator:
    def __init__(self, fs=48000, baud=1200, f_space=2200, f_mark=1200, squelch=0.001):
        self.fs = fs
        self.baud = baud
        self.f_space = f_space
        self.f_mark = f_mark
        self.samples_per_symbol = int(fs / baud)
        self.squelch = squelch
        
        # Design filters
        nyq = 0.5 * fs
        # Bandpass filter around our frequencies (e.g., 800 Hz to 2600 Hz)
        self.bpf_b, self.bpf_a = signal.butter(4, [800 / nyq, 2600 / nyq], btype='band')
        
        # Discriminator delay
        center_f = (f_space + f_mark) / 2.0
        # 90 degree phase shift at center frequency
        self.delay = int(fs / (4 * center_f)) 
        if self.delay == 0:
            self.delay = 1
            
        # Lowpass filter for baseband (cut off around baud rate)
        self.lpf_b, self.lpf_a = signal.butter(4, (baud * 1.5) / nyq, btype='low')
        
        # State for streaming
        self.prev_samples = np.zeros(self.delay)
        self.lpf_state = signal.lfilter_zi(self.lpf_b, self.lpf_a)
        self.bpf_state = signal.lfilter_zi(self.bpf_b, self.bpf_a)
        
        # UART state machine
        self.state = 'IDLE' # IDLE, START, DATA, STOP
        self.bit_idx = 0
        self.current_byte = 0
        self.sample_count = 0
        self.last_bb = 0

        # Level metrics from the most recent block, for link tuning.
        # Measured before squelch and before bit decision, so they reflect
        # what the sound card actually delivered.
        self.input_rms = 0.0   # RMS of the raw input
        self.input_peak = 0.0  # peak of the raw input (clipping check)
        self.level_rms = 0.0   # RMS after the bandpass, i.e. in-band energy

    def reset(self):
        self.prev_samples = np.zeros(self.delay)
        self.lpf_state = signal.lfilter_zi(self.lpf_b, self.lpf_a)
        self.bpf_state = signal.lfilter_zi(self.bpf_b, self.bpf_a)
        self.state = 'IDLE'
        self.last_bb = 0
        self.input_rms = 0.0
        self.input_peak = 0.0
        self.level_rms = 0.0

    def demodulate(self, samples):
        # 1. Bandpass filter
        filtered, self.bpf_state = signal.lfilter(self.bpf_b, self.bpf_a, samples, zi=self.bpf_state)

        # Level metrics for tuning. Cheap, and only over this block.
        if len(samples):
            self.input_rms = float(np.sqrt(np.mean(np.square(samples))))
            self.input_peak = float(np.max(np.abs(samples)))
            self.level_rms = float(np.sqrt(np.mean(np.square(filtered))))

        # 2. Delay and multiply discriminator
        # Pad with previous samples to do delay
        padded = np.concatenate((self.prev_samples, filtered))
        delayed = padded[:-self.delay]
        self.prev_samples = padded[-self.delay:]
        
        mult = filtered * delayed
        
        # 3. Lowpass filter
        baseband, self.lpf_state = signal.lfilter(self.lpf_b, self.lpf_a, mult, zi=self.lpf_state)
        
        # Squelch: If energy is low, force baseband to positive (Idle/Mark)
        # We can use the same LPF for the energy envelope
        energy = filtered ** 2
        # Since we need state for energy LPF too for streaming, let's just do a simple block-wise check for now, 
        # or just add state for it. Actually, block-wise is fine for high baud rates, but let's just use it directly.
        # To avoid adding another state, we can just use a simple rolling mean or just block mean for the squelch.
        # But wait, lfilter without zi is bad for streaming. 
        # Let's just do a simple absolute value check on the filtered signal, smoothed by a simple leaky integrator in pure python? No, that's slow.
        # Let's just check the energy of the whole block for now. If the whole block is noise, squelch it.
        # Wait, the block can contain the start of a packet.
        # Let's add state for energy_lpf.
        # Actually, simpler: mult is already proportional to energy! If the signal is just noise, mult has very low amplitude.
        # baseband also has low amplitude. We can just use an absolute threshold on baseband!
        # When there's a strong carrier, baseband amplitude is large. When it's noise, baseband amplitude is near 0.
        # If baseband is between -squelch and squelch, we can force it to Mark (positive).
        baseband = np.where(np.abs(baseband) < self.squelch, 1.0, baseband)
        
        # Mark and Space mapping
        # For f_mark=1200, f_space=2200, delay=7 (at 48kHz). 
        # phase shift = 2 * pi * f * delay / fs
        # phase_mark = 2 * pi * 1200 * 7 / 48000 = 1.099 rad -> cos(1.099) > 0 (Mark is positive)
        # phase_space = 2 * pi * 2200 * 7 / 48000 = 2.015 rad -> cos(2.015) < 0 (Space is negative)
        
        # 4. UART recovery
        output_bytes = []
        
        for bb in baseband:
            if self.state == 'IDLE':
                # Look for falling edge (1 to 0 transition)
                if self.last_bb > 0 and bb <= 0:
                    self.state = 'START'
                    # Wait half a symbol to sample at the center of the start bit
                    self.sample_count = self.samples_per_symbol // 2
            
            elif self.state == 'START':
                self.sample_count -= 1
                if self.sample_count <= 0:
                    # Check if it's still 0 (valid start bit)
                    if bb <= 0:
                        self.state = 'DATA'
                        self.bit_idx = 0
                        self.current_byte = 0
                        self.sample_count = self.samples_per_symbol
                    else:
                        # False start
                        self.state = 'IDLE'
                        
            elif self.state == 'DATA':
                self.sample_count -= 1
                if self.sample_count <= 0:
                    bit_val = 1 if bb > 0 else 0
                    self.current_byte |= (bit_val << self.bit_idx)
                    self.bit_idx += 1
                    self.sample_count = self.samples_per_symbol
                    
                    if self.bit_idx == 8:
                        self.state = 'STOP'
                        
            elif self.state == 'STOP':
                self.sample_count -= 1
                if self.sample_count <= 0:
                    bit_val = 1 if bb > 0 else 0
                    if bit_val == 1:
                        # Valid stop bit
                        output_bytes.append(self.current_byte)
                    # Return to idle
                    self.state = 'IDLE'
            
            self.last_bb = bb
            
        return bytes(output_bytes)


# --- Multi-tone FSK ------------------------------------------------------
#
# A second physical layer, alongside the Bell 202 one above, for links where
# amplitude cannot be trusted. The scheme above decides bits by the sign of a
# delay-and-multiply discriminator, so anything that weakens one tone relative
# to the other biases every decision the same way. On a real acoustic link
# here, a channel that pushed the 2300 Hz content to 9.5% of nominal produced
# bytes like d5/df -- 0x55 with extra 1 bits and never missing ones -- and
# decoded 0 payload bytes while the level meter still read 100% in band.
#
# Here each symbol is a chord of several tones, and the decision compares the
# energy of the two chords. Scaling the whole signal scales both sides, so the
# comparison is unchanged: gain drops out entirely. Several tones per symbol
# add frequency diversity, so a tone landing in a null of the channel costs
# accuracy rather than the symbol.
#
# Tones are chosen so no 2nd or 3rd harmonic of one symbol's tone lands on a
# tone of the other symbol. Speakers and microphones distort, and distortion
# manufactures harmonics; a harmonic falling on the opposite chord would be
# evidence for the wrong symbol. Within one chord it is harmless -- it
# reinforces the right answer. Both chords carry the same mean frequency, so a
# tilted channel attenuates them equally.
# The tones come in *pairs*, and each pair is one vote. Both members of a
# pair sit 200 Hz apart, so whatever the channel does to one it does to the
# other, and the comparison between them survives tilt, distance and volume.
# Five pairs vote; the majority is the bit. That is what makes a lone loud
# tone harmless: summing energy lets one strong spurious tone outweigh five
# modest correct ones, but it can only ever carry one vote. Measured on a real
# link, summing gave a chord twice the energy of its rival and 27% of bytes
# right; a vote cannot be bought that way.
#
# Polarity alternates along the band -- on pairs 0, 2 and 4 the lower tone
# means 0, on pairs 1 and 3 it means 1 -- so both chords end up with the same
# mean frequency (1620 vs 1660 Hz) and a tilted channel favours neither bit.
MFSK_PAIRS = (
    # (tone for bit 0, tone for bit 1)
    (700, 900),
    (1320, 1120),
    (1540, 1740),
    (2160, 1960),
    (2380, 2580),
)

MFSK_TONES_0 = tuple(p[0] for p in MFSK_PAIRS)
MFSK_TONES_1 = tuple(p[1] for p in MFSK_PAIRS)

# A vote is a ratio, so five tones of pure noise still elect a bit --
# confidently, and forever. Observed: 485 bytes decoded out of an empty room.
# So a vote is not enough on its own; the demodulator also has to know whether
# anything was transmitted at all, and the reference for that is already in
# hand. Each pair's losing tone is a frequency nobody sent: with a signal the
# winner towers over it, with noise alone the two are the same size. No extra
# probe frequencies needed -- and none would fit anyway, since the gaps
# between pairs are only 220 Hz wide and a probe placed there would pick up
# the very tones it is meant to ignore.
MFSK_PRESENCE_MIN = 1.3   # winner/loser energy ratio, median across pairs


class MFSKModulator:
    """Multi-tone FSK. One chord per bit, UART 8N1 framing as above."""

    def __init__(self, fs=48000, baud=100, tones_0=MFSK_TONES_0,
                 tones_1=MFSK_TONES_1, parallel=False):
        # parallel=False: every pair sounds the same bit and the receiver
        # votes -- robust, one bit per symbol. parallel=True: each pair carries
        # its own bit, so a symbol carries as many bits as there are pairs.
        # Same symbol duration either way; the speed comes from spending the
        # frequencies on separate bits instead of all of them on one.
        self.parallel = parallel
        self.fs = fs
        self.baud = baud
        self.tones_0 = tuple(tones_0)
        self.tones_1 = tuple(tones_1)
        self.samples_per_symbol = int(fs / baud)
        # Phase is carried per tone across calls, for the same reason the Bell
        # 202 modulator carries one: restarting a tone mid-stream splices a
        # discontinuity into it, which is a click and out-of-band energy.
        self.phase = {f: 0.0 for f in self.tones_0 + self.tones_1}

    def reset(self):
        for f in self.phase:
            self.phase[f] = 0.0

    def _symbol(self, bit):
        """One symbol: a single bit, or one bit per pair when parallel."""
        if self.parallel:
            tones = [(self.tones_1 if b else self.tones_0)[i]
                     for i, b in enumerate(bit)]
        else:
            tones = self.tones_1 if bit else self.tones_0
        n = np.arange(self.samples_per_symbol)
        out = np.zeros(self.samples_per_symbol)
        for f in tones:
            w = 2 * np.pi * f / self.fs
            out += np.sin(w * n + self.phase[f])
            self.phase[f] = (self.phase[f] + w * self.samples_per_symbol) % (2 * np.pi)
        # Normalised by chord size, so a chord never clips where a single tone
        # would not, and both chords carry equal power.
        return out / len(tones)

    def modulate_bits(self, bits):
        if self.parallel:
            k = len(self.tones_0)
            bits = list(bits)
            if len(bits) % k:                       # pad out the last symbol
                bits += [0] * (k - len(bits) % k)
            chunks = [self._symbol(bits[i:i + k]) for i in range(0, len(bits), k)]
        else:
            chunks = [self._symbol(b) for b in bits]
        return np.concatenate(chunks) if chunks else np.array([])

    def modulate_byte(self, byte_val):
        bits = [0]                                        # start
        bits += [(byte_val >> i) & 1 for i in range(8)]   # LSB first
        bits.append(1)                                    # stop
        return self.modulate_bits(bits)

    def modulate(self, data: bytes):
        chunks = [self.modulate_byte(b) for b in data]
        return np.concatenate(chunks) if chunks else np.array([])

    def idle(self, symbols):
        """Continuous mark. Timing recovery needs transitions, so a link-layer
        preamble should alternate rather than idle."""
        k = len(self.tones_0) if self.parallel else 1
        return self.modulate_bits([1] * symbols * k)


class MFSKDemodulator:
    """Energy-ratio detector with its own symbol clock.

    The Bell 202 demodulator above gets symbol timing for free: it hunts for
    the falling edge of a UART start bit in a continuous waveform. Energy over
    a window has no such edge to find, so this one recovers timing explicitly,
    with an early/late gate steered by the very contrast it uses to decide
    bits -- contrast peaks when the window sits inside one symbol and collapses
    when it straddles two.
    """

    def __init__(self, fs=48000, baud=100, tones_0=MFSK_TONES_0,
                 tones_1=MFSK_TONES_1, guard=0.15, contrast_min=0.3,
                 parallel=False):
        self.fs = fs
        self.baud = baud
        self.tones_0 = tuple(tones_0)
        self.tones_1 = tuple(tones_1)
        self.samples_per_symbol = int(fs / baud)
        self.contrast_min = contrast_min
        self.parallel = parallel

        # Skip the head of every symbol: that is where the previous symbol's
        # reverberation is still ringing. Measured, this took accuracy from
        # 76.5% to 100% on a channel with an 80 ms tail.
        self.guard = int(guard * self.samples_per_symbol)

        n = np.arange(self.guard, self.samples_per_symbol)
        self.probe_0 = np.exp(-2j * np.pi * np.outer(self.tones_0, n) / fs)
        self.probe_1 = np.exp(-2j * np.pi * np.outer(self.tones_1, n) / fs)

        # No per-tone equaliser here. One was tried -- divide each tone by a
        # running average of its own energy, to stop a tone sitting on a room
        # resonance from carrying a permanently louder vote. It cost the
        # reverberant cases outright: the average absorbs the previous
        # symbol's decaying tail and starts treating it as that tone's normal
        # level. Pairing already does the job it was meant to do, and does it
        # without memory -- the two tones of a pair are 200 Hz apart, so a
        # resonance that lifts one lifts the other.

        # Early/late gate geometry. The on-time window starts `delta` into the
        # buffer, leaving margin on each side to look earlier and later.
        self.delta = max(1, self.samples_per_symbol // 8)
        self.step = max(1, self.samples_per_symbol // 32)

        self.reset()

    def reset(self):
        self.buf = np.zeros(0, dtype=np.float64)
        self.state = 'IDLE'
        self.bit_idx = 0
        self.current_byte = 0
        self.last_bit = 1
        self.framing_errors = 0
        self.input_rms = 0.0
        self.input_peak = 0.0
        self.contrast = 0.0

    def _score(self, start):
        """Bit and vote margin for the symbol window beginning at `start`.

        Five pairs of tones, one vote each: within a pair the two frequencies
        are 200 Hz apart, so the channel treats them alike and whichever
        arrives stronger names the bit. The majority wins.

        Summing the chords instead -- what this did before -- lets amplitude
        buy the answer. Measured on a real link, one chord arrived with twice
        the energy of the other, 227 against 114, and the detector called
        almost everything the louder symbol: 27% of bytes right. Under a vote
        a tone that is loud for the wrong reason still carries one vote, and
        four others outrank it. That is the whole point of sounding five
        frequencies at once, and summing threw it away.
        """
        seg = self.buf[start + self.guard:start + self.samples_per_symbol]
        e0 = np.abs(self.probe_0 @ seg) ** 2
        e1 = np.abs(self.probe_1 @ seg) ** 2
        if not np.any(e0) and not np.any(e1):
            return 1, 0.0

        votes = e1 > e0
        ones = int(np.count_nonzero(votes))
        bit = 1 if ones * 2 > len(votes) else 0

        # The vote decides the bit; it must not also steer the clock. A tally
        # of five is quantised -- the margin can only be 0.2, 0.6 or 1.0 --
        # and the early/late gate needs to tell "almost centred" from
        # "centred", which three values cannot express. Measured: with the
        # tally steering, symbol timing never locked on a real capture and
        # recovery sat at 6%; brute-forcing the correct offset on the same
        # audio gave 87-94% of bits right, so the votes were never the
        # problem. Steer on the per-pair contrast instead, which is
        # continuous, and let it stay a ratio so it means the same at any
        # volume.
        contrast = float(np.mean(np.abs(e1 - e0) / np.maximum(e1 + e0, 1e-30)))

        # Did anyone actually transmit? Each pair's losing tone is a frequency
        # that was not sent, so the winner/loser ratio separates a real symbol
        # from a room decoding its own noise. The median ignores the pair that
        # happened to land in a null.
        win = np.where(votes, e1, e0)
        lose = np.where(votes, e0, e1)
        # The soft value the error-correcting decoder wants: how far each pair
        # leaned, summed, rather than which way it leaned. A pair that split
        # 51/49 and one that split 99/1 are the same vote and very different
        # evidence, and throwing that difference away costs about 2 dB --
        # measured, the difference between correcting 8% of bits wrong and
        # 13%. Each pair's term is a ratio, so this stays amplitude-independent
        # like everything else in this layer.
        per_pair = (e1 - e0) / np.maximum(e1 + e0, 1e-30)
        llr = per_pair if self.parallel else float(np.sum(per_pair))

        presence = float(np.median(win / np.maximum(lose, 1e-30)))
        if presence < MFSK_PRESENCE_MIN:
            return bit, 0.0, llr

        return bit, contrast, llr

    def _feed_bit(self, bit, output):
        """UART 8N1 on the recovered bit stream, the same framing the Bell 202
        path uses, so either physical layer presents the same dumb serial line."""
        if self.state == 'IDLE':
            if bit == 0:
                self.state = 'DATA'
                self.bit_idx = 0
                self.current_byte = 0
        elif self.state == 'DATA':
            self.current_byte |= (bit << self.bit_idx)
            self.bit_idx += 1
            if self.bit_idx == 8:
                self.state = 'STOP'
        elif self.state == 'STOP':
            # Emit even when the stop bit is wrong, unlike the Bell 202 path.
            # Dropping it would turn one bad bit into a missing *byte*, and a
            # deletion shifts every byte after it, which is the one error a
            # CRC-checked packet cannot absorb -- one loss and the rest of the
            # packet is garbage. A substitution stays local, and the CRC is
            # what decides whether the packet is good. Keeping the byte keeps
            # the alignment; that is worth more than the byte being right.
            if bit != 1:
                self.framing_errors += 1
            output.append(self.current_byte)
            self.state = 'IDLE'

    def _symbols(self, samples):
        """Timing recovery and one decision per symbol, as a generator.

        Framed bytes and raw soft values are two readings of the same symbol
        stream, so they share this loop rather than each carrying a copy of
        the early/late gate. Two copies of symbol timing would be two things
        to keep correct.
        """
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples):
            self.input_rms = float(np.sqrt(np.mean(np.square(samples))))
            self.input_peak = float(np.max(np.abs(samples)))
        self.buf = np.concatenate((self.buf, samples))

        need = self.samples_per_symbol + 2 * self.delta
        while len(self.buf) >= need:
            bit_e, c_e, l_e = self._score(0)
            bit_o, c_o, l_o = self._score(self.delta)
            bit_l, c_l, l_l = self._score(2 * self.delta)

            # Steer toward whichever gate sees the cleanest separation: best
            # contrast means the window sits most fully inside one symbol.
            if c_l > c_o and c_l >= c_e:
                adjust, bit, self.contrast, llr = self.step, bit_l, c_l, l_l
            elif c_e > c_o and c_e > c_l:
                adjust, bit, self.contrast, llr = -self.step, bit_e, c_e, l_e
            else:
                adjust, bit, self.contrast, llr = 0, bit_o, c_o, l_o

            # Steering was once gated on transitions -- freeze the clock
            # through a run of identical symbols, the way a PLL flywheel
            # coasts, since a run carries no timing information. It was
            # reverted: it showed no measurable benefit and cost accuracy on a
            # reverberant channel, where timing genuinely drifts and needs
            # correcting every symbol rather than only at edges.
            self.last_bit = bit
            self.buf = self.buf[self.samples_per_symbol + adjust:]
            yield bit, self.contrast, llr

    def demodulate(self, samples):
        output = []
        for bit, contrast, _llr in self._symbols(samples):
            # Amplitude-independent squelch. An absolute threshold would put
            # back the very dependence this layer exists to remove; contrast is
            # a ratio, so it means the same thing at any volume.
            if contrast < self.contrast_min:
                self.state = 'IDLE'
            else:
                self._feed_bit(bit, output)
        return bytes(output)

    def demodulate_soft(self, samples):
        """Log-likelihoods for the error-correcting decoder.

        One value per symbol when voting, one per pair per symbol when
        parallel. No squelch and no framing: a weak symbol is reported as a
        weak opinion, which the decoder can weigh, where dropping it would
        silently shorten the block and misalign everything after it -- the
        very failure that framing inside a block causes.
        """
        vals = [llr for _b, _c, llr in self._symbols(samples)]
        if not vals:
            return np.zeros((0, len(self.tones_0))) if self.parallel else np.zeros(0)
        return np.array(vals).ravel() if self.parallel else np.array(vals)


# --- M-ary FSK: one tone at a time, four bits per tone ----------------------
#
# The two multi-tone layers above spend several frequencies to carry one bit,
# or one frequency per bit. This one spends *all* of them on one symbol: 16
# tones, exactly one sounding at a time, and which tone it is names four bits.
#
# The reason is power, and it is the largest single lever measured on this
# link. A chord of five tones has to be divided by five to stay inside the
# same peak amplitude, so every tone leaves the speaker 14 dB down. Measured
# on recorded audio, a transmitted tone arrived only 2 to 7 dB above the same
# frequency when it was not transmitted -- which is where 15-30% per-pair
# error rates come from. Sounding one tone at a time gets that 14 dB back.
#
# The cost is that a tone parked in a null of the room's comb response can
# never win a comparison, so its symbol is never detected. The defence is that
# with 16 tones each one is silent 15/16 of the time, so its long-run average
# energy *is* the noise floor at that frequency. Dividing by it before
# comparing is a per-frequency calibrated detector -- and unlike the
# normalisation that failed on the chord layers, the estimate is not
# contaminated by the signal it is meant to measure.
MARY_TONES = (888, 1050, 1212, 1375, 1538, 1700, 1862, 2025,
              2188, 2350, 2512, 2675, 2838, 3000, 3162, 3325)
MARY_BITS = 4

# One nibble as a *chord* of three tones instead of a single one. Sixteen
# patterns, any two sharing at most one tone, so the distance between any two
# nibbles is four tone positions: mistaking one tone cannot change the nibble.
# Every tone is used in exactly three patterns, so no frequency carries more of
# the alphabet than another.
#
# The trade is power against diversity. One tone at a time puts the whole
# amplitude on the frequency that carries the symbol; three tones must be
# divided by three to stay inside the same peak, costing 9.5 dB each. That is
# a bad bargain on a channel that spreads energy in time and a good one on a
# channel with deep, narrow nulls -- and this link measures as the second:
# a comb with 13-18 dB troughs, and no reverberation tail above the noise
# floor. Simulated on a comb plus tilt, chords scored 94.5% against 90.5% for
# single tones; add reverberation and it reverses to 40.8% against 50.8%.
#
# Off by default. Which of those two channels this room really is, on the day,
# is a measurement and not a preference.
MARY_CODES = (
    (0, 2, 12), (0, 4, 6), (0, 8, 9), (1, 3, 14),
    (1, 6, 10), (1, 7, 15), (2, 6, 13), (2, 9, 14),
    (3, 5, 15), (3, 10, 11), (4, 5, 9), (4, 8, 15),
    (5, 12, 13), (7, 10, 13), (7, 11, 14), (8, 11, 12),
)


def _gray(i):
    return i ^ (i >> 1)


# Neighbouring tones are the ones the channel confuses, so Gray coding makes
# that confusion cost one bit instead of up to four.
_GRAY = [_gray(i) for i in range(1 << MARY_BITS)]
_UNGRAY = {g: i for i, g in enumerate(_GRAY)}


class MaryModulator:
    """One tone per symbol, at full amplitude. Four bits per symbol.

    With `gap` non-zero the tone stops early and the rest of the symbol is
    silence. That silence is not wasted time -- it is the only timing
    reference in this layer that does not depend on the data. The clock is
    otherwise steered by the contrast of the decision itself, which is
    circular: to know where the boundary is you must already be deciding well.
    Measured on a simulated channel with an unknown start offset, symbol
    accuracy went from 69% to 100% clean and from 54% to 72% under 80 ms of
    reverberation.

    Silence rather than a pilot tone, and the difference is not small: a pilot
    reverberates too, so its own tail fills the gap it was meant to mark. Under
    the same reverberation the pilot scored 43% against silence's 72%.
    """

    def __init__(self, fs=48000, baud=100, tones=MARY_TONES, gap=0.0,
                 chord=False):
        self.fs = fs
        self.baud = baud
        self.tones = tuple(tones)
        self.gap = gap
        self.chord = chord
        self.samples_per_symbol = int(fs / baud)
        # Samples the tone actually sounds for. The rest is the gap.
        self.samples_per_tone = self.samples_per_symbol - int(gap * self.samples_per_symbol)
        # Every tone's phase advances every symbol, whether or not it sounded,
        # so each behaves as a free-running oscillator that is switched on and
        # off. Restarting a tone's phase when it returns would splice a
        # discontinuity into it, which is a click and out-of-band energy.
        self.phase = np.zeros(len(self.tones))

    def reset(self):
        self.phase[:] = 0.0

    def _advance(self):
        w = 2 * np.pi * np.array(self.tones) / self.fs
        self.phase = (self.phase + w * self.samples_per_symbol) % (2 * np.pi)

    def _symbol(self, value):
        v = value & ((1 << MARY_BITS) - 1)
        nd = self.samples_per_tone
        n = np.arange(nd)
        if self.chord:
            idxs = MARY_CODES[v]
            out = np.zeros(nd)
            for i in idxs:
                w = 2 * np.pi * self.tones[i] / self.fs
                out += np.sin(w * n + self.phase[i])
            # Divided by the count, not its square root: the same peak budget
            # as a single tone, so the two schemes can be compared without one
            # of them quietly running hotter into the far side's limiter.
            out /= len(idxs)
        else:
            idx = _GRAY[v]
            w = 2 * np.pi * self.tones[idx] / self.fs
            out = np.sin(w * n + self.phase[idx])
        self._advance()
        if nd < self.samples_per_symbol:
            out = np.concatenate([out, np.zeros(self.samples_per_symbol - nd)])
        return out

    def modulate_bits(self, bits):
        bits = list(bits)
        if len(bits) % MARY_BITS:
            bits += [0] * (MARY_BITS - len(bits) % MARY_BITS)
        chunks = []
        for i in range(0, len(bits), MARY_BITS):
            v = 0
            for j, b in enumerate(bits[i:i + MARY_BITS]):
                v |= (b & 1) << j
            chunks.append(self._symbol(v))
        return np.concatenate(chunks) if chunks else np.array([])

    def modulate(self, data: bytes):
        bits = []
        for byte in data:
            bits += [(byte >> i) & 1 for i in range(8)]
        return self.modulate_bits(bits)

    def idle(self, symbols):
        """A tail so the receiver's last symbols are not stranded in its
        buffer. Alternating, not constant: timing recovery needs transitions
        and a repeated symbol teaches it nothing."""
        return self.modulate_bits([0, 1, 0, 1] * symbols)


class MaryDemodulator:
    """Pick the loudest tone, after dividing each by its own noise floor."""

    def __init__(self, fs=48000, baud=100, tones=MARY_TONES, guard=0.15,
                 contrast_min=0.15, floor_alpha=0.02, gap=0.0, band=0.0,
                 chord=False):
        self.fs = fs
        self.baud = baud
        self.tones = np.array(tones, dtype=np.float64)
        self.samples_per_symbol = int(fs / baud)
        self.contrast_min = contrast_min
        self.floor_alpha = floor_alpha
        self.gap = gap
        self.chord = chord

        # With a transmitted gap the tone occupies only the head of the symbol,
        # so measure there and leave the tail to the clock.
        self.samples_per_tone = (self.samples_per_symbol
                                 - int(gap * self.samples_per_symbol))
        self.guard = int(guard * self.samples_per_tone)

        # Measure a small band around each tone rather than the single exact
        # frequency. A point probe assumes the tone arrives exactly where it
        # was sent; it does not, because the symbol window is misaligned by up
        # to a third of a symbol on this link and truncating a tone broadens
        # it. Measured on the corpus, summing probes 20 Hz either side took
        # symbol accuracy from 59.5% to 61.3%. Past about 40 Hz it reverses --
        # the band starts collecting the neighbouring tone, which is 162 Hz
        # away.
        n = np.arange(self.guard, self.samples_per_tone)
        self.band = band
        offsets = (0.0,) if not band else (-band, 0.0, band)
        self.probes = [np.exp(-2j * np.pi * np.outer(self.tones + o, n) / fs)
                       for o in offsets]
        self.probe = self.probes[0]

        self.delta = max(1, self.samples_per_symbol // 8)
        self.step = max(1, self.samples_per_symbol // 32)
        self.reset()

    def reset(self):
        self.buf = np.zeros(0, dtype=np.float64)
        self.floor = np.zeros(len(self.tones))
        # Bits left over when a block does not end on a byte boundary. A
        # symbol carries four bits and a byte takes two symbols, but audio
        # arrives in 2048-sample blocks holding 4.27 symbols -- so a block
        # that yields an odd number of symbols ends mid-byte. Dropping that
        # half byte shifts every byte after it by a nibble, which is why a
        # perfect channel decoded a message readable at each end and destroyed
        # in the middle, wherever a boundary happened to fall. The soft path
        # never had this, since it emits one value per bit and never packs.
        self.bits = []
        self.input_rms = 0.0
        self.input_peak = 0.0
        self.contrast = 0.0
        # Absolute sample index of the head of the buffer, and of the window
        # the last decision was measured on. Nothing in the decoding needs
        # these. A diagnostic that reconstructs them from the buffer length
        # gets them wrong by up to a quarter of a symbol, because the
        # early/late gate measures at an offset inside the buffer and then
        # consumes a different amount than it measured -- which drew the
        # receiver as misaligned when the misalignment was in the bookkeeping.
        self.consumed = 0
        self.last_window = 0

    def _energies(self, start):
        seg = self.buf[start + self.guard:start + self.samples_per_tone]
        if len(self.probes) == 1:
            return np.abs(self.probe @ seg) ** 2
        return sum(np.abs(p @ seg) ** 2 for p in self.probes)

    def _gap_energy(self, start):
        """Power in the stretch the transmitter left silent.

        This is the timing reference, and its virtue is that it says nothing
        about the data -- it is low when the window is aligned and rises the
        moment the window slides onto a neighbouring tone. Steering on the
        decision's own contrast instead is circular, since a window that has
        lost the boundary also stops deciding well.
        """
        seg = self.buf[start + self.samples_per_tone:start + self.samples_per_symbol]
        return float(np.mean(np.square(seg))) if len(seg) else 0.0

    def _nibble_scores(self, norm):
        """How well each of the sixteen patterns explains this symbol.

        For single tones the pattern is the tone, so the score is the tone.
        For chords it is the sum over the three tones -- which is why a tone
        lost in a null costs a third of the evidence rather than all of it.
        """
        if not self.chord:
            return norm
        return np.array([norm[list(c)].sum() for c in MARY_CODES])

    def _score(self, start):
        e = self._energies(start)
        # Divide by the running floor before comparing. A tone in a null and a
        # tone on a peak are then judged against what each of them looks like
        # when nobody is transmitting on it, which is the only fair comparison
        # on a channel whose response swings 17 dB between neighbours.
        norm = e / np.maximum(self.floor, 1e-30)
        scores = self._nibble_scores(norm)
        order = np.argsort(scores)
        top, second = scores[order[-1]], scores[order[-2]]
        contrast = (top - second) / max(top + second, 1e-30)
        return int(order[-1]), contrast, norm

    def _update_floor(self, e):
        # Each tone is silent 15 symbols out of 16, so its average energy is
        # its noise floor. The winner is left out of the update so the floor
        # never chases the signal it exists to measure.
        mask = np.ones(len(self.tones), dtype=bool)
        mask[int(np.argmax(e))] = False
        if not self.floor.any():
            self.floor[:] = e.mean()
            return
        a = self.floor_alpha
        self.floor[mask] += a * (e[mask] - self.floor[mask])

    def _symbols(self, samples):
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples):
            self.input_rms = float(np.sqrt(np.mean(np.square(samples))))
            self.input_peak = float(np.max(np.abs(samples)))
        self.buf = np.concatenate((self.buf, samples))

        need = self.samples_per_symbol + 2 * self.delta
        while len(self.buf) >= need:
            i_e, c_e, n_e = self._score(0)
            i_o, c_o, n_o = self._score(self.delta)
            i_l, c_l, n_l = self._score(2 * self.delta)

            if self.gap:
                # Steer toward whichever window leaves the quietest gap. Lower
                # is better here, the opposite sense to contrast, so the scores
                # are negated and the same comparison below still applies.
                c_e = -self._gap_energy(0)
                c_o = -self._gap_energy(self.delta)
                c_l = -self._gap_energy(2 * self.delta)

            if c_l > c_o and c_l >= c_e:
                adjust, idx, norm, at = self.step, i_l, n_l, 2 * self.delta
                self.contrast = self._score(at)[1]
            elif c_e > c_o and c_e > c_l:
                adjust, idx, norm, at = -self.step, i_e, n_e, 0
                self.contrast = self._score(at)[1]
            else:
                adjust, idx, norm, at = 0, i_o, n_o, self.delta
                self.contrast = self._score(at)[1]

            self._update_floor(self._energies(at))
            self.last_window = self.consumed + at
            step = self.samples_per_symbol + adjust
            self.consumed += step
            self.buf = self.buf[step:]
            yield idx, self.contrast, norm

    def demodulate(self, samples):
        out = []
        for idx, contrast, _norm in self._symbols(samples):
            # In chord mode the winning index *is* the nibble, since the
            # patterns are indexed by value. With single tones it is a tone
            # index and Gray coding has to be undone first.
            v = idx if self.chord else _UNGRAY[idx]
            self.bits += [(v >> j) & 1 for j in range(MARY_BITS)]
        while len(self.bits) >= 8:
            chunk = self.bits[:8]
            del self.bits[:8]
            out.append(sum(b << j for j, b in enumerate(chunk)))
        return bytes(out)

    def demodulate_soft(self, samples):
        """One log-likelihood per bit, max-log style.

        For each bit position, the best tone that would have carried a 1 is
        compared against the best that would have carried a 0. Working in the
        log domain means the comparison is between *ratios* of energy, so it
        means the same at any volume -- the property every decision in this
        project is built on.
        """
        out = []
        for _idx, _c, norm in self._symbols(samples):
            # Score the sixteen *nibbles*, not the sixteen tones. They differ
            # once a nibble is a chord: the evidence for a value is then the
            # sum over its three tones, and a bit's likelihood has to be read
            # off the values that carry it, whatever they are made of.
            log_e = np.log(np.maximum(self._nibble_scores(norm), 1e-30))
            place = (lambda v: v) if self.chord else (lambda v: _GRAY[v])
            for j in range(MARY_BITS):
                ones = [log_e[place(v)] for v in range(1 << MARY_BITS) if (v >> j) & 1]
                zeros = [log_e[place(v)] for v in range(1 << MARY_BITS) if not (v >> j) & 1]
                out.append(max(ones) - max(zeros))
        return np.array(out)
