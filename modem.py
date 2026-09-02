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
                 tones_1=MFSK_TONES_1):
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
        return self.modulate_bits([1] * symbols)


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
                 tones_1=MFSK_TONES_1, guard=0.15, contrast_min=0.3):
        self.fs = fs
        self.baud = baud
        self.tones_0 = tuple(tones_0)
        self.tones_1 = tuple(tones_1)
        self.samples_per_symbol = int(fs / baud)
        self.contrast_min = contrast_min

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
        presence = float(np.median(win / np.maximum(lose, 1e-30)))
        if presence < MFSK_PRESENCE_MIN:
            return bit, 0.0

        return bit, contrast

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

    def demodulate(self, samples):
        samples = np.asarray(samples, dtype=np.float64)
        if len(samples):
            self.input_rms = float(np.sqrt(np.mean(np.square(samples))))
            self.input_peak = float(np.max(np.abs(samples)))
        self.buf = np.concatenate((self.buf, samples))

        output = []
        need = self.samples_per_symbol + 2 * self.delta
        while len(self.buf) >= need:
            bit_e, c_e = self._score(0)
            bit_o, c_o = self._score(self.delta)
            bit_l, c_l = self._score(2 * self.delta)

            # Steer toward whichever gate sees the cleanest separation: best
            # contrast means the window sits most fully inside one symbol.
            if c_l > c_o and c_l >= c_e:
                adjust, bit, self.contrast = self.step, bit_l, c_l
            elif c_e > c_o and c_e > c_l:
                adjust, bit, self.contrast = -self.step, bit_e, c_e
            else:
                adjust, bit, self.contrast = 0, bit_o, c_o

            # Steering was once gated on transitions -- freeze the clock
            # through a run of identical symbols, the way a PLL flywheel
            # coasts, since a run carries no timing information. It was
            # reverted: it showed no measurable benefit and cost accuracy on a
            # reverberant channel, where timing genuinely drifts and needs
            # correcting every symbol rather than only at edges.
            self.last_bit = bit
            # Amplitude-independent squelch. An absolute threshold would put
            # back the very dependence this layer exists to remove; contrast is
            # a ratio, so it means the same thing at any volume.
            if self.contrast < self.contrast_min:
                self.state = 'IDLE'
            else:
                self._feed_bit(bit, output)

            self.buf = self.buf[self.samples_per_symbol + adjust:]

        return bytes(output)
