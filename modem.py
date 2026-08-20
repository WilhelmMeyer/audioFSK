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
