"""Interactive two-machine console for the acoustic link, over the serial cable.

Running on both machines, this turns the serial wire into a remote control:
from one keyboard you switch each side's microphone and speaker on and off,
retune gain and squelch, swap audio devices, and watch live level meters from
both ends at once. That is the whole point -- during development the two
things you actually need to change are on opposite sides of the room.

    fsk> mic on           acts on THIS machine
    fsk> r mic on         acts on the OTHER machine, over the serial cable
    fsk> b reset          acts on both

Both roles run the same AudioNode and the same execute(); the only difference
is that the console has a REPL and the agent does not. So any command works
identically whichever side you type it on, and there is one implementation to
keep correct rather than two.

    python console.py --role agent   --port /dev/ttyUSB0     # Linux, headless
    python console.py --role console --port COM4             # Windows, REPL

The serial link carries control only. The audio still goes through the air --
that is still the thing under test.
"""

import argparse
import queue
import sys
import threading
import time

import numpy as np
import sounddevice as sd

import fec
import updater
import xfer
from modem import (FSKModulator, FSKDemodulator,
                   MFSKModulator, MFSKDemodulator, MFSK_PAIRS,
                   MaryModulator, MaryDemodulator, MARY_BITS)
from serial_link import Control, pack, unpack

FS = 48000
BAUD = 1200
BLOCK = 2048
PREAMBLE = bytes([0x55] * 10 + [0xFF])

MFSK_BAUD = 100       # multi-tone layer: slower, but amplitude-independent
FEC_REPEAT = 2        # rate 1/3 x2: holds to 25% of bits wrong, measured
MARY_GAP = 0.0        # silence at the end of each M-ary symbol, as a fraction
                      # (a floor, not a law -- `fecrep` moves it per link)

TONE_CHUNK = 32       # bytes of 0x55 per modulated chunk, ~0.27 s
TONE_DEPTH = 4        # keep ~1 s of tone buffered, no more


def dbfs(rms):
    return -99.0 if rms <= 1e-9 else 20.0 * float(np.log10(rms))


def meter_bar(db, width=20):
    bars = int(np.clip((db + 60.0) / 60.0, 0.0, 1.0) * width)
    return "#" * bars + "." * (width - bars)


def printable(data):
    return "".join(chr(b) if 32 <= b < 127 else "." for b in data)


class AudioNode:
    """One machine's audio half: mic in, speaker out, and the knobs.

    Input and output are separate streams, not one duplex stream, precisely
    so the mic and the speaker can be switched independently from the far end.
    """

    def __init__(self, gain=0.8, squelch=0.005, dev_in=None, dev_out=None,
                 on_event=None):
        # Both physical layers live side by side, each with its own stateful
        # pair, so switching modes never carries filter or phase state across.
        # `mode` selects which the feeder and demod threads use.
        self.layers = {
            'fsk': (FSKModulator(fs=FS, baud=BAUD),
                    FSKDemodulator(fs=FS, baud=BAUD, squelch=squelch)),
            'mfsk': (MFSKModulator(fs=FS, baud=MFSK_BAUD),
                     MFSKDemodulator(fs=FS, baud=MFSK_BAUD)),
            # Same tones, same timing recovery, but every pair carries its own
            # bit. Kept as a separate instance pair so no filter or phase state
            # crosses between the two readings of the same frequencies.
            'mfsk-par': (MFSKModulator(fs=FS, baud=MFSK_BAUD, parallel=True),
                         MFSKDemodulator(fs=FS, baud=MFSK_BAUD, parallel=True)),
            # 16 tones, one sounding at a time, four bits per symbol. The
            # chord layers divide their amplitude among five tones and lose
            # 14 dB each; this one spends it all on the tone that carries the
            # symbol.
            'mary': (MaryModulator(fs=FS, baud=MFSK_BAUD, gap=MARY_GAP),
                     MaryDemodulator(fs=FS, baud=MFSK_BAUD, gap=MARY_GAP)),
        }
        self.mode = 'fsk'
        self.gain = gain
        self.dev_in = dev_in
        self.dev_out = dev_out
        self.on_event = on_event or (lambda text: None)

        self.tone = False
        self.echo = False
        self.fec_parallel = False
        self.fec_repeat = FEC_REPEAT
        self.mary_gap = MARY_GAP
        # Receiving an error-corrected block, the mirror of fecsend. Without
        # it only the console side could decode FEC, through capture.py and
        # recvfile.py -- separate programs that own their own audio -- so the
        # good direction followed whoever held the keyboard. It lives in the
        # shared command table precisely so a role swap costs nothing.
        self.fec_rx = False
        self.fec_llr = []
        self.fec_nbytes = 0
        # The raw audio behind that llr, kept so the block can be demodulated
        # again with different settings without asking for another
        # transmission. This is the console side's capture.py, for the machine
        # that has no capture.py: the room does not hold still, so judging a
        # setting by transmitting again measures the setting and the room at
        # once. 30 s at 48 kHz is 11 MB, which is worth it.
        self.fec_audio = []
        self.fec_audio_len = 0
        self.in_stream = None
        self.out_stream = None

        # Every modulation happens on the feeder thread. The modulator carries
        # phase across calls, so touching it from two threads would splice
        # discontinuous phase into the carrier -- audible clicks, and energy
        # smeared outside the passband.
        self.tx_bytes = queue.Queue()
        self.out_queue = queue.Queue()
        self.out_buf = np.zeros(0, dtype=np.float32)

        # Likewise every demodulation happens on the demod thread: bpf/lpf
        # state and the UART state machine are carried across blocks.
        self.in_queue = queue.Queue()
        self.rx_buffer = bytearray()
        # A short tail of raw input, kept so a frequency can be measured on
        # demand. `level` answers in wide band, which cannot tell a tone that
        # arrived from a room that is merely loud -- and the whole M-ary
        # question is per frequency. Two seconds is plenty and costs 384 kB.
        self.tail = []
        self.tail_len = 0

        self.stats_lock = threading.Lock()
        self._reset_stats()

        self.meter_interval = 0.0   # 0 = meter off
        threading.Thread(target=self._feeder, daemon=True).start()
        threading.Thread(target=self._demodder, daemon=True).start()
        threading.Thread(target=self._meter, daemon=True).start()

    @property
    def mod(self):
        return self.layers[self.mode][0]

    @property
    def demod(self):
        return self.layers[self.mode][1]

    @property
    def fec_layer(self):
        """Which instance pair an error-corrected block uses.

        Not always `self.mode`: parallel MFSK is a separate pair. The
        transmitter already picked 'mfsk-par' here while `self.mode` stayed
        'mfsk', so a receiver reading `self.demod` would have listened on a
        different instance than the one that spoke -- harmless only for as
        long as there was no receive path. Both ends read this property now.
        """
        if self.mode == 'mary':
            return 'mary'
        return 'mfsk-par' if self.fec_parallel else 'mfsk'

    def threshold(self, value=None):
        """The two layers gate on different quantities and must not share a
        number: Bell 202 squelches on absolute baseband amplitude, the ratio
        detector on contrast, which is a fraction. Setting 0.005 on the latter
        would be almost no gate at all."""
        attr = 'squelch' if self.mode == 'fsk' else 'contrast_min'
        if value is not None:
            setattr(self.demod, attr, value)
        return attr, getattr(self.demod, attr)

    def set_mary_gap(self, frac):
        """Rebuild the M-ary pair around a new gap.

        Both ends have to agree, and there is no way to detect a disagreement
        from the signal: the receiver simply measures the wrong stretch of each
        symbol and reports confident nonsense. Send it with `b marygap`.
        """
        self.mary_gap = frac
        self.layers['mary'] = (MaryModulator(fs=FS, baud=MFSK_BAUD, gap=frac),
                               MaryDemodulator(fs=FS, baud=MFSK_BAUD, gap=frac))
        if self.mode == 'mary':
            self.mod, self.demod = self.layers['mary']
            self.rx_buffer.clear()

    def set_mode(self, mode):
        if mode not in self.layers:
            return f"modo desconhecido: {mode!r} (use 'fsk', 'mfsk' ou 'mary')"
        self.mode = mode
        self.mod.reset()
        self.demod.reset()
        self.rx_buffer.clear()
        # A half-heard block belongs to the layer that was listening. Keeping
        # it would feed one layer's soft values to the other's decoder.
        self.fec_rx = False
        self.fec_llr = []
        with self.stats_lock:
            self._reset_stats()
        baud = BAUD if mode == 'fsk' else MFSK_BAUD
        bits = MARY_BITS if mode == 'mary' else 1
        return (f"modo = {mode} ({baud} baud"
                + (f", {bits} bits por simbolo)" if bits > 1 else ")"))

    def _reset_stats(self):
        self.peak = 0.0
        self.rms_sum = 0.0
        self.level_sum = 0.0
        self.blocks = 0
        self.bytes_in = 0
        # Real elapsed time, so the byte rate is honest even when the meter
        # thread runs late and when `level` is called ad hoc.
        self.window_start = time.time()

    # --- audio callbacks: these run on PortAudio's real-time thread and
    # --- must only move data. All DSP is on the worker threads below.

    def _out_cb(self, outdata, frames, time_info, status):
        needed, idx = frames, 0
        while needed > 0:
            if len(self.out_buf) == 0:
                try:
                    self.out_buf = self.out_queue.get_nowait()
                except queue.Empty:
                    outdata[idx:, 0] = 0
                    return
            take = min(needed, len(self.out_buf))
            outdata[idx:idx + take, 0] = self.out_buf[:take]
            self.out_buf = self.out_buf[take:]
            idx += take
            needed -= take

    def _in_cb(self, indata, frames, time_info, status):
        self.in_queue.put(indata[:, 0].copy())

    # --- worker threads

    def fec_bits(self, data):
        """The coded bit stream a `fecsend` would put on the air."""
        if self.fec_parallel:
            k = len(MFSK_PAIRS)
            return fec.frame_parallel(data, k, repeat=self.fec_repeat)
        return fec.frame(data, repeat=self.fec_repeat)

    def fec_plan(self, data):
        """How many symbols a fecsend puts on the air, and for how long.

        Mirrors _fec_frame and has to keep mirroring it. The reply used to
        report the coded *bit* count as a symbol count and divide it by the
        baud, which in M-ary -- four bits per symbol, plus a 120-symbol
        preamble and an idle tail -- announced 11.7 s for a burst that lasts
        4.2 s. Not cosmetic: that number is what a caller uses to decide how
        long to listen and how long to record, and being 2.8x high once sent
        me hunting a truncated capture that was never truncated.
        """
        k = len(MFSK_PAIRS)
        if self.mode == 'mary':
            nbits = len(fec.frame(data, repeat=self.fec_repeat))
            symbols = 120 + -(-nbits // MARY_BITS) + 6
        elif self.fec_parallel:
            nbits = len(fec.frame_parallel(data, k, repeat=self.fec_repeat))
            symbols = 80 + -(-nbits // k) + 4
        else:
            nbits = len(fec.frame(data, repeat=self.fec_repeat))
            symbols = 80 + nbits + 4
        return symbols, symbols / MFSK_BAUD

    def _fec_frame(self, data, repeat):
        """Alternating preamble, sync word, coded block, trailing idle.

        The preamble alternates because timing recovery needs transitions and
        learns nothing from a run of identical symbols. The idle tail is not
        optional either: the demodulator keeps just over a symbol buffered, so
        a block that stops dead strands its last symbols there -- and unlike a
        byte stream, a block missing its tail does not decode at all.
        """
        k = len(MFSK_PAIRS)
        if self.mode == 'mary':
            mod = self.layers[self.fec_layer][0]
            bits = fec.frame(data, repeat=repeat)
            # Alternate between the two extreme tones. A preamble that repeats
            # one symbol is a steady tone, and timing recovery learns nothing
            # from it -- it needs transitions to lock onto.
            pre = []
            for i in range(120):
                v = 0 if i % 2 else (1 << MARY_BITS) - 1
                pre += [(v >> j) & 1 for j in range(MARY_BITS)]
            samples = np.concatenate([mod.modulate_bits(pre),
                                      mod.modulate_bits(list(bits)),
                                      mod.idle(6)])
            return (samples * self.gain).astype(np.float32)
        mod = self.layers[self.fec_layer][0]
        bits = self.fec_bits(data)
        # The preamble alternates on every pair at once so timing recovery
        # sees the same thing either way, and so the far side can lock before
        # it knows anything about which pairs are working.
        pre = [0, 1] * 40 * (k if self.fec_parallel else 1)
        samples = np.concatenate([mod.modulate_bits(pre),
                                  mod.modulate_bits(list(bits)),
                                  mod.idle(4)])
        return (samples * self.gain).astype(np.float32)

    def fec_listen(self, on, nbytes=None):
        """Arm or disarm soft-decision accumulation.

        Hard and soft cannot both run over one block: `_symbols` consumes the
        buffer, so whichever call came second would see an empty one. Arming
        therefore switches the thread's path rather than adding to it, and
        resets the demodulator so the block starts on a clean filter state.
        """
        if on:
            if self.mode == 'fsk':
                return "fecrx nao existe em fsk (sem saida soft) -- 'mode mary'"
            if nbytes:
                self.fec_nbytes = nbytes
            if not self.fec_nbytes:
                return "uso: fecrx on <bytes esperados>"
            self.layers[self.fec_layer][1].reset()
            self.fec_llr = []
            self.fec_audio = []
            self.fec_audio_len = 0
            self.fec_rx = True
            return (f"fecrx LIGADO em {self.fec_layer}, esperando "
                    f"{self.fec_nbytes} bytes (rep {self.fec_repeat})")
        self.fec_rx = False
        return f"fecrx desligado ({sum(len(a) for a in self.fec_llr)} valores)"

    def fec_read(self, nbytes=None):
        """Sync, then Viterbi, over everything heard since arming.

        Same two steps as bench.run_fec, and deliberately the same order: the
        sync word is found by correlation over the soft stream because symbol
        counting drifts -- the early/late gate eats a different number of
        samples per symbol as it steers.
        """
        want = nbytes or self.fec_nbytes
        if not want:
            return "uso: fecrx <bytes esperados>"
        if not self.fec_llr:
            return "nada acumulado -- 'fecrx on <bytes>' primeiro"
        llr = np.concatenate(self.fec_llr)
        npairs = len(MFSK_PAIRS)
        if self.fec_layer == 'mfsk-par':
            start = fec.find_sync_parallel(llr, npairs)
            if start is None:
                return f"sync nao encontrado ({len(llr)} valores)"
            data = fec.decode_parallel(llr[start:], want, npairs,
                                       repeat=self.fec_repeat)
        else:
            start = fec.find_sync(llr)
            if start is None:
                return f"sync nao encontrado ({len(llr)} valores)"
            data = fec.decode(llr[start:], want, repeat=self.fec_repeat)
        return f"{len(data)} bytes ({len(llr)} valores): {printable(data)}"

    def measure(self, freq, secs=0.3, bw=45.0):
        """How much of the recent input sits within bw Hz of freq.

        Reported beside the wide-band level of the same window, because the
        number that matters is the difference: a tone that arrived, against
        the room at that same frequency. Both are computed over one window so
        the FFT normalisation is identical -- measuring signal and noise over
        windows of different lengths is exactly what made two sweeps of the
        same room disagree about its shape.
        """
        if not self.tail:
            return "sem audio de entrada (mic desligado?)"
        x = np.concatenate(self.tail)[-int(secs * FS):]
        if len(x) < 256:
            return "audio insuficiente"
        w = np.hanning(len(x))
        power = np.abs(np.fft.rfft(x * w)) ** 2
        freqs = np.fft.rfftfreq(len(x), 1 / FS)
        m = (freqs >= freq - bw) & (freqs <= freq + bw)
        band = float(np.sqrt(power[m].mean())) if m.any() else 0.0
        wide = float(np.sqrt(power.mean()))
        db = lambda v: 20 * np.log10(max(v, 1e-30))
        return (f"meas {freq:.0f} Hz  banda {db(band):7.1f}  "
                f"larga {db(wide):7.1f}  razao {db(band) - db(wide):+6.1f} dB")

    def fec_sweep(self, nbytes=None):
        """Demodulate the block already heard, again, at other settings.

        Sweeping `fecrep` here would be meaningless: each redundancy is a
        physically different transmission with a different bit layout, so the
        only one that can decode this recording is the one that made it. What
        *can* be swept is the demodulator -- the guard interval and how fast
        the per-tone floor adapts -- because those are applied when the stored
        audio is read, not when it was sent.

        That is bench.py's method, on the side that has no bench.py. It
        matters most in the direction where this machine is the receiver,
        because there the only alternative is transmitting again into a room
        that has changed in between.
        """
        want = nbytes or self.fec_nbytes
        if not want:
            return "uso: fecsweep <bytes esperados>"
        if not self.fec_audio:
            return "nada guardado -- 'fecrx on <bytes>' e uma transmissao antes"
        audio = np.concatenate(self.fec_audio)
        lines = [f"{len(audio) / FS:.1f}s guardados, {want} bytes, "
                 f"rep {self.fec_repeat}, camada {self.fec_layer}"]
        npairs = len(MFSK_PAIRS)

        def try_one(demod, label):
            llr = np.concatenate([demod.demodulate_soft(audio[i:i + BLOCK])
                                  for i in range(0, len(audio), BLOCK)])
            if self.fec_layer == 'mfsk-par':
                start = fec.find_sync_parallel(llr, npairs)
                got = (None if start is None else
                       fec.decode_parallel(llr[start:], want, npairs,
                                           repeat=self.fec_repeat))
            else:
                start = fec.find_sync(llr)
                got = (None if start is None else
                       fec.decode(llr[start:], want, repeat=self.fec_repeat))
            lines.append(f"  {label}: " +
                         ("sem sync" if got is None else printable(got)))

        if self.fec_layer == 'mary':
            for guard in (0.10, 0.15, 0.25, 0.35, 0.45):
                for alpha in (0.02, 0.08):
                    try_one(MaryDemodulator(fs=FS, baud=MFSK_BAUD, guard=guard,
                                            floor_alpha=alpha),
                            f"guard {guard:.2f} alpha {alpha:.2f}")
        else:
            par = self.fec_layer == 'mfsk-par'
            for guard in (0.15, 0.25, 0.35, 0.45):
                try_one(MFSKDemodulator(fs=FS, baud=MFSK_BAUD, parallel=par,
                                        guard=guard),
                        f"guard {guard:.2f}")
        return chr(10).join(lines)

    def _chirp(self, f0, f1, secs):
        """Linear sweep, amplitude-flat, with short fades at each end.

        Flat in amplitude so the recording measures the channel and not the
        sweep. The fades are not cosmetic: a sinusoid that starts and stops at
        full amplitude is a step, and a step is broadband -- it would paint
        energy across the whole spectrum being measured.
        """
        n = int(secs * FS)
        t = np.arange(n) / FS
        k = (f1 - f0) / secs
        sig = np.sin(2 * np.pi * (f0 * t + 0.5 * k * t * t))
        fade = int(0.01 * FS)
        if n > 2 * fade:
            ramp = np.linspace(0.0, 1.0, fade)
            sig[:fade] *= ramp
            sig[-fade:] *= ramp[::-1]
        return (sig * self.gain).astype(np.float32)

    def _sine(self, freq, secs):
        """One steady tone, long enough to reach the room's steady state.

        A chirp answers a different question than this one. It excites each
        frequency for a fraction of a second while moving, so nothing settles,
        and it recovers frequency from *time* -- which makes every reading
        depend on knowing exactly when the far side started playing. A stepped
        tone asks the question M-ary actually rests on: send f, and see how
        much arrives at f. Compared against how much arrives at f when nobody
        sent it, that is the whole of what the detector has to work with.

        Same fades as the sweep, for the same reason: a sinusoid that starts
        at full amplitude is a step, and a step is broadband.
        """
        n = int(secs * FS)
        sig = np.sin(2 * np.pi * freq * np.arange(n) / FS)
        fade = int(0.01 * FS)
        if n > 2 * fade:
            ramp = np.linspace(0.0, 1.0, fade)
            sig[:fade] *= ramp
            sig[-fade:] *= ramp[::-1]
        return (sig * self.gain).astype(np.float32)

    def _feeder(self):
        while True:
            try:
                data = self.tx_bytes.get_nowait()
            except queue.Empty:
                data = None
            if data is not None:
                # A raw item already carries its own lead-in and framing, as
                # xfer.build does; prefixing the console's preamble as well
                # would just add a second sync byte for the parser to reject.
                payload, raw = data
                if raw == 'raw-samples':
                    if payload[0] == 'fec':
                        self.out_queue.put(self._fec_frame(*payload[1:]))
                    elif payload[0] == 'sine':
                        self.out_queue.put(self._sine(*payload[1:]))
                    else:
                        self.out_queue.put(self._chirp(*payload[1:]))
                    continue
                samples = self.mod.modulate(payload if raw else PREAMBLE + payload)
                if self.mode != 'fsk':
                    # Every ratio-detecting layer keeps just over a symbol
                    # buffered, so a burst that stops dead leaves its last
                    # byte stranded there -- every send losing its tail,
                    # silently. That is true of M-ary exactly as it is of the
                    # chord layers, and testing for 'mfsk' alone left M-ary
                    # sends short by a byte. Bell 202 needs no such tail and
                    # its modulator offers none.
                    samples = np.concatenate([samples, self.mod.idle(4)])
                self.out_queue.put((samples * self.gain).astype(np.float32))
                continue
            if self.tone and self.out_queue.qsize() < TONE_DEPTH:
                # 0x55 framed 8N1 is an unbroken bit alternation in either
                # layer, which is what timing recovery needs. Scale the chunk
                # by baud so a chunk stays about a quarter second either way.
                n = TONE_CHUNK if self.mode == 'fsk' else max(1, TONE_CHUNK * MFSK_BAUD // BAUD)
                samples = self.mod.modulate(bytes([0x55]) * n)
                self.out_queue.put((samples * self.gain).astype(np.float32))
            else:
                time.sleep(0.02)

    def _demodder(self):
        while True:
            samples = self.in_queue.get()
            self.tail.append(np.asarray(samples, dtype=np.float64))
            self.tail_len += len(samples)
            while self.tail_len > 2 * FS and len(self.tail) > 1:
                self.tail_len -= len(self.tail.pop(0))
            # One instance, named the same way at both ends -- see fec_layer.
            if self.fec_rx:
                d = self.layers[self.fec_layer][1]
                self.fec_llr.append(d.demodulate_soft(samples))
                self.fec_audio.append(np.asarray(samples, dtype=np.float64))
                self.fec_audio_len += len(samples)
                while self.fec_audio_len > 30 * FS and len(self.fec_audio) > 1:
                    self.fec_audio_len -= len(self.fec_audio.pop(0))
                out = b''
            else:
                d = self.demod
                out = d.demodulate(samples)
            with self.stats_lock:
                self.peak = max(self.peak, d.input_peak)
                # Sum the two levels and divide once at the end. Averaging the
                # per-block ratio instead lets a near-silent block, where the
                # denominator is almost zero and the bandpass is still ringing
                # from its own initial state, throw the whole window past 100%.
                self.rms_sum += d.input_rms
                # Each layer reports quality in its own currency: in-band
                # energy for the Bell 202 detector, decision contrast for the
                # ratio detector. Both are fractions of the input, so the
                # meter renders them the same way.
                if self.mode == 'fsk':
                    self.level_sum += d.level_rms
                else:
                    self.level_sum += d.contrast * d.input_rms
                self.blocks += 1
                self.bytes_in += len(out)
            if out:
                self.rx_buffer += out
                del self.rx_buffer[:-4096]
                if self.echo:
                    self.on_event(f"rx: {printable(out)}")

    def _meter(self):
        while True:
            interval = self.meter_interval
            if interval <= 0:
                time.sleep(0.1)
                continue
            time.sleep(interval)
            self.on_event(self.level())

    # --- readings

    def level(self, reset=True):
        """Reading for the window since the last one, not since the process
        started.

        Resetting by default is the whole point: with the accumulators left
        running, `level` reported a lifetime average and a peak that never
        decayed, so a tone that had already stopped still read -25 dBFS
        seconds later. A meter that cannot fall is worse than no meter --
        it says the level is fine while you are chasing silence.
        """
        with self.stats_lock:
            blocks, peak = self.blocks, self.peak
            elapsed = max(1e-3, time.time() - self.window_start)
            rms = self.rms_sum / blocks if blocks else 0.0
            inband = min(1.0, self.level_sum / self.rms_sum) if self.rms_sum > 1e-9 else 0.0
            rate = self.bytes_in / elapsed
            if reset:
                self._reset_stats()
        if not blocks:
            return "sem audio de entrada (mic desligado?)"
        db = dbfs(rms)
        # Name the quantity, because the two layers report different ones and
        # a reader comparing runs has to know which is on screen.
        label = "in-band" if self.mode == 'fsk' else "contrst"
        return (f"[{meter_bar(db)}] {db:6.1f} dBFS  {label} {inband * 100:3.0f}%  "
                f"pico {peak:.2f}  {rate:5.1f} B/s")

    def status(self):
        return "\n".join([
            f"mic     {'ON' if self.in_stream else 'off'}   dev in  {self.dev_in}",
            f"speaker {'ON' if self.out_stream else 'off'}   dev out {self.dev_out}",
            f"tone    {'ON' if self.tone else 'off'}",
            f"echo    {'ON' if self.echo else 'off'}",
            f"meter   {f'{self.meter_interval}s' if self.meter_interval else 'off'}",
            f"gain    {self.gain}",
            f"modo    {self.mode} ({BAUD if self.mode == 'fsk' else MFSK_BAUD} baud)",
            f"squelch {self.threshold()[1]}  ({self.threshold()[0]})",
            # FEC state has to be visible. It is not a mode you can see or
            # hear: `fecsend` is a per-burst verb, and an armed `fecrx` puts
            # the demod thread on the soft path, so the plain rx buffer
            # silently stops filling. A receiver left armed, or a repeat
            # count that no longer matches the transmitter, looks exactly
            # like a dead link -- and neither could be read from here.
            f"fec rep {self.fec_repeat}" + (" paralelo" if self.fec_parallel else ""),
            (f"fecrx   ARMADO em {self.fec_layer}, esperando {self.fec_nbytes} "
             f"bytes ({sum(len(a) for a in self.fec_llr)} valores ouvidos)"
             if self.fec_rx else "fecrx   off"),
            f"rx buf  {len(self.rx_buffer)} bytes",
        ])

    # --- stream control

    def mic(self, on):
        if on:
            if self.in_stream:
                return "mic ja ligado"
            self.demod.reset()
            self.in_stream = sd.InputStream(samplerate=FS, channels=1,
                                            blocksize=BLOCK, device=self.dev_in,
                                            callback=self._in_cb)
            self.in_stream.start()
            return "mic LIGADO"
        if not self.in_stream:
            return "mic ja desligado"
        self.in_stream.stop()
        self.in_stream.close()
        self.in_stream = None
        return "mic desligado"

    def speaker(self, on):
        if on:
            if self.out_stream:
                return "caixa ja ligada"
            self.out_stream = sd.OutputStream(samplerate=FS, channels=1,
                                              blocksize=BLOCK, device=self.dev_out,
                                              callback=self._out_cb)
            self.out_stream.start()
            return "caixa LIGADA"
        if not self.out_stream:
            return "caixa ja desligada"
        self.tone = False
        self.out_stream.stop()
        self.out_stream.close()
        self.out_stream = None
        return "caixa desligada"

    def set_device(self, which, value):
        dev = None if value.lower() in ("default", "none", "auto", "padrao", "-") else (
            int(value) if value.isdigit() else value)
        if which == "in":
            was_on = self.in_stream is not None
            if was_on:
                self.mic(False)
            self.dev_in = dev
            if was_on:
                self.mic(True)
            return f"dev in = {dev}" + (" (mic reiniciado)" if was_on else "")
        was_on = self.out_stream is not None
        tone_was = self.tone
        if was_on:
            self.speaker(False)
        self.dev_out = dev
        if was_on:
            self.speaker(True)
            self.tone = tone_was
        return f"dev out = {dev}" + (" (caixa reiniciada)" if was_on else "")


HELP = """comandos (prefixe com 'r ' para a outra maquina, 'b ' para as duas)
  mic on|off          liga/desliga o microfone
  spk on|off          liga/desliga a caixa de som
  tone on|off         portadora continua 0x55 (precisa da caixa ligada)
  chirp [f0 f1 seg]   varredura de frequencia, para medir a resposta do canal
  tonef <hz> [seg]    um tom puro, para medir o que chega naquela frequencia
  meas <hz> [seg]     mede quanta energia chegou nessa frequencia
  send <texto>        transmite <texto> pelo ar
  fecsend <texto>     transmite com correcao de erro (mfsk ~2 B/s, mary ~9 B/s)
  fecrx on <n>        escuta um bloco corrigido de n bytes (mfsk ou mary)
  fecrx [n]           decodifica o que foi escutado; 'fecrx off' encerra
  fecsweep [n]        redecodifica o mesmo audio com outros ajustes
  fecpar on|off       fec em paralelo: 5 bits por simbolo, ~4x mais rapido
  fecrep <n>          repeticoes de cada bit codificado (padrao 2)
  marygap <fracao>    silencio no fim de cada simbolo mary (ex 0.2); os DOIS lados
  fileinfo <arq>      tamanho, pacotes e crc32 de um arquivo
  sendpkt <arq> <n>   transmite o pacote n do arquivo pelo ar
  fecpkt <arq> <n>    o mesmo, com correcao de erro (mfsk ou mary)
  rx                  mostra e limpa o buffer recebido
  echo on|off         imprime bytes recebidos conforme chegam
  meter on|off|<seg>  medidor de nivel continuo
  level               uma leitura de nivel
  gain <0..1>         amplitude de saida
  mode fsk|mfsk|mary  camada fisica: fsk 1200 baud, mfsk por razao, mary 16 tons
  squelch <valor>     limiar: squelch (fsk) ou contraste 0..1 (mfsk e mary)
  dev in|out <n>      troca o dispositivo de audio (reinicia o stream)
  dev in|out auto     volta ao dispositivo padrao do sistema
  devs                lista dispositivos de audio
  status              estado deste lado
  ping                testa o canal serial
  version             commit que esta maquina esta rodando
  pull [ref] [force]  atualiza o codigo pelo repositorio remoto
  restart             reinicia o processo com o codigo novo
  help / quit"""


def execute(node, cmd):
    """The one command table. Identical on console and agent."""
    parts = cmd.strip().split(None, 1)
    if not parts:
        return ""
    verb = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    def flag(default=True):
        return default if not arg else arg.lower() in ("on", "1", "true", "sim")

    if verb in ("help", "?"):
        return HELP
    if verb == "ping":
        return "pong"
    if verb == "status":
        return node.status()
    if verb == "level":
        return node.level()
    if verb == "devs":
        return str(sd.query_devices())
    if verb == "mic":
        return node.mic(flag())
    if verb in ("spk", "speaker", "caixa"):
        return node.speaker(flag())
    if verb == "tone":
        on = flag()
        if on and not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        node.tone = on
        return f"tone {'ON' if on else 'off'}"
    if verb == "chirp":
        # A measurement, not a modulation: everything else in this table sends
        # bytes and asks what came back, which confounds the code with the
        # channel. A sweep asks only what the room, the speaker and the
        # microphone do to each frequency -- the answer that should have been
        # chosen tone frequencies in the first place, instead of a band
        # assumed from theory.
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        bits = arg.split()
        try:
            f0 = float(bits[0]) if len(bits) > 0 else 300.0
            f1 = float(bits[1]) if len(bits) > 1 else 22000.0
            secs = float(bits[2]) if len(bits) > 2 else 4.0
        except ValueError:
            return "uso: chirp [f0 f1 segundos]"
        f1 = min(f1, FS / 2 - 500)
        secs = max(0.5, min(secs, 20.0))
        node.tx_bytes.put((('chirp', f0, f1, secs), 'raw-samples'))
        return f"chirp {f0:.0f}-{f1:.0f} Hz em {secs:.1f}s"
    if verb == "meas":
        # The receiving half of tonef. With both in this table either machine
        # can play and either can measure, so a frequency map can be made in
        # whichever direction is the one misbehaving.
        bits = arg.split()
        if not bits:
            return "uso: meas <hz> [segundos]"
        try:
            freq = float(bits[0])
            secs = float(bits[1]) if len(bits) > 1 else 0.3
        except ValueError:
            return f"meas invalido: {arg!r}"
        return node.measure(freq, max(0.05, min(secs, 2.0)))
    if verb == "tonef":
        # A steady tone at one frequency, which is what a per-frequency
        # measurement needs and what `tone` is not: `tone` sends 0x55 through
        # the modulator, so it answers about the layer, not about the air.
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        bits = arg.split()
        if not bits:
            return "uso: tonef <hz> [segundos]"
        try:
            freq = float(bits[0])
            secs = float(bits[1]) if len(bits) > 1 else 1.0
        except ValueError:
            return f"tonef invalido: {arg!r}"
        if not 20.0 <= freq <= FS / 2 - 100:
            return f"frequencia fora de faixa: {freq}"
        secs = max(0.1, min(secs, 10.0))
        node.tx_bytes.put((('sine', freq, secs), 'raw-samples'))
        return f"tonef {freq:.0f} Hz por {secs:.1f}s"
    if verb == "echo":
        node.echo = flag()
        return f"echo {'ON' if node.echo else 'off'}"
    if verb == "meter":
        if arg.lower() in ("off", "0", "false"):
            node.meter_interval = 0.0
            return "meter off"
        try:
            node.meter_interval = float(arg) if arg and arg[0].isdigit() else 1.0
        except ValueError:
            return f"intervalo invalido: {arg!r}"
        return f"meter a cada {node.meter_interval}s"
    if verb == "gain":
        try:
            node.gain = max(0.0, min(1.0, float(arg)))
        except ValueError:
            return f"gain invalido: {arg!r}"
        return f"gain = {node.gain}"
    if verb == "squelch":
        try:
            name, val = node.threshold(float(arg))
        except ValueError:
            return f"squelch invalido: {arg!r}"
        return f"{name} = {val}"
    if verb in ("mode", "modo"):
        if not arg:
            return f"modo atual: {node.mode}"
        return node.set_mode(arg.lower())
    if verb == "dev":
        bits = arg.split()
        if len(bits) != 2 or bits[0] not in ("in", "out"):
            return "uso: dev in <n>|auto | dev out <n>|auto"
        # `auto` hands the choice back to the host audio system. A pinned
        # index is the right thing until it is not: device numbering shifts
        # when anything is plugged in or removed, and an index that has gone
        # stale fails with errors that read like broken hardware -- observed,
        # five different PortAudio errors from five indices on a machine whose
        # audio was fine. Without this there is no way to say "use the default
        # again" from the far end, and the only fix is someone walking over to
        # the other machine.
        return node.set_device(bits[0], bits[1])
    if verb == "send":
        if not arg:
            return "uso: send <texto>"
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        node.tx_bytes.put((arg.encode("utf-8", "replace"), False))
        return f"enviando {len(arg)} bytes"
    if verb == "fecsend":
        # The error-corrected path, deliberately a separate verb rather than a
        # mode: it produces a block, not a byte stream, so it does not compose
        # with `tone`, `echo` or anything else that assumes bytes trickling
        # out. Keeping it explicit means a `send` never silently changes
        # meaning depending on hidden state.
        if not arg:
            return "uso: fecsend <texto>"
        if node.mode not in ('mfsk', 'mary'):
            return "fecsend so em mfsk ou mary - rode 'mode mfsk' antes"
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        data = arg.encode("utf-8", "replace")
        node.tx_bytes.put((('fec', data, node.fec_repeat), 'raw-samples'))
        symbols, secs = node.fec_plan(data)
        return (f"fecsend {len(data)} bytes -> {symbols} simbolos "
                f"({secs:.1f}s no ar, rep {node.fec_repeat})")
    if verb == "fecsweep":
        # Re-read what was already heard. The point is that it costs no air
        # time and no room: the same seconds are demodulated again, so two
        # settings can actually be compared instead of being transmitted at
        # different moments into a room that moved in between.
        try:
            want = int(arg.split()[0]) if arg.split() else None
        except ValueError:
            return f"fecsweep: numero invalido: {arg!r}"
        return node.fec_sweep(want)
    if verb == "fecrx":
        # The receiving half of fecsend, and the reason it belongs in this
        # table rather than in a tool: execute() is identical on both roles,
        # so adding it here makes either machine able to receive. Before it,
        # soft decoding lived only in bench.py and recvfile.py -- which own
        # their own audio and so only ever ran on the console side, which is
        # why the working direction followed the keyboard instead of being a
        # property of the link.
        bits = arg.split()
        if bits and bits[0].lower() in ("on", "off", "1", "0", "true", "false", "sim"):
            on = bits[0].lower() in ("on", "1", "true", "sim")
            try:
                want = int(bits[1]) if len(bits) > 1 else None
            except ValueError:
                return f"fecrx: numero invalido: {bits[1]!r}"
            if on and not node.in_stream:
                return "mic desligado - rode 'mic on' antes"
            return node.fec_listen(on, want)
        try:
            want = int(bits[0]) if bits else None
        except ValueError:
            return f"fecrx: numero invalido: {bits[0]!r}"
        return node.fec_read(want)
    if verb == "marygap":
        # Silence transmitted at the end of every M-ary symbol. It is the only
        # timing reference in that layer that does not depend on the data --
        # the clock is otherwise steered by the contrast of the decision
        # itself, which is circular. Measured on a simulated channel with an
        # unknown start offset, symbol accuracy went from 69% to 100% clean and
        # 54% to 72% under reverberation. Both machines must agree on it: the
        # receiver measures only the head of the symbol, so a mismatch means it
        # measures the wrong stretch.
        try:
            frac = float(arg)
        except ValueError:
            return f"marygap invalido: {arg!r}"
        if not 0.0 <= frac < 0.6:
            return "marygap fora de faixa (0 a 0.6)"
        node.set_mary_gap(frac)
        return f"mary gap = {frac} ({int(frac * 100)}% de silencio por simbolo)"
    if verb == "fecrep":
        # How many times each coded bit is sent. The right value is a property
        # of the link, not of the code: what the decoder needs is a number of
        # independent looks at each bit, and how many the air destroys is
        # exactly what changes when a speaker or a room changes.
        try:
            node.fec_repeat = max(1, min(8, int(arg)))
        except ValueError:
            return f"fecrep invalido: {arg!r}"
        return f"fec repeticao = {node.fec_repeat}"
    if verb == "fecpar":
        node.fec_parallel = flag()
        k = len(MFSK_PAIRS)
        return (f"fec paralelo {'ON' if node.fec_parallel else 'off'} "
                f"({k} bits por simbolo)" if node.fec_parallel else "fec paralelo off (voto)")
    if verb == "fileinfo":
        try:
            with open(arg, "rb") as fh:
                data = fh.read()
        except OSError as e:
            return f"nao consegui ler {arg!r}: {e}"
        parts = xfer.split(data)
        return (f"size={len(data)} packets={len(parts)} crc32={xfer.crc32(data):08x} "
                f"air={xfer.air_seconds(sum(len(xfer.build(i, c)) for i, c in enumerate(parts))):.0f}s")
    if verb == "sendpkt":
        bits = arg.split()
        if len(bits) != 2:
            return "uso: sendpkt <arquivo> <seq>"
        try:
            with open(bits[0], "rb") as fh:
                parts = xfer.split(fh.read())
            seq = int(bits[1])
        except (OSError, ValueError) as e:
            return f"sendpkt: {e}"
        if not 0 <= seq < len(parts):
            return f"seq fora de faixa: {seq} (0..{len(parts) - 1})"
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        node.tx_bytes.put((xfer.build(seq, parts[seq]), True))
        return (f"tx {seq + 1}/{len(parts)} ({(seq + 1) * 100 // len(parts)}%) "
                f"{len(parts[seq])} bytes na fila")
    if verb == "fecpkt":
        # The error-corrected twin of `sendpkt`, and stateless in the same
        # way: this side is told which packet to play and plays it. The
        # receiver decides what to ask for and when to ask again, so a lost
        # packet costs one retry rather than the whole file.
        bits = arg.split()
        if not 2 <= len(bits) <= 3:
            return "uso: fecpkt <arquivo> <seq> [tamanho]"
        try:
            size = int(bits[2]) if len(bits) > 2 else xfer.PAYLOAD_SIZE
            with open(bits[0], "rb") as fh:
                parts = xfer.split(fh.read(), size)
            seq = int(bits[1])
        except (OSError, ValueError) as e:
            return f"fecpkt: {e}"
        if not 0 <= seq < len(parts):
            return f"seq fora de faixa: {seq} (0..{len(parts) - 1})"
        if node.mode not in ('mfsk', 'mary'):
            return "fecpkt so em mfsk ou mary"
        if not node.out_stream:
            return "caixa desligada - rode 'spk on' antes"
        packet = xfer.build(seq, parts[seq])
        node.tx_bytes.put((('fec', packet, node.fec_repeat), 'raw-samples'))
        return (f"tx {seq + 1}/{len(parts)} ({(seq + 1) * 100 // len(parts)}%) "
                f"{len(packet)} bytes codificados")
    if verb == "rx":
        data = bytes(node.rx_buffer)
        node.rx_buffer.clear()
        if not data:
            return "buffer vazio"
        return f"{len(data)} bytes: {printable(data)}"
    if verb == "version":
        return updater.version()
    if verb == "pull":
        return updater.pull(arg)
    if verb == "restart":
        return updater.request_restart()
    if verb == "reset":
        node.demod.reset()
        node.rx_buffer.clear()
        node.fec_rx = False
        node.fec_llr = []
        with node.stats_lock:
            node._reset_stats()
        return "demodulador e buffers resetados"
    return f"comando desconhecido: {verb!r} (tente 'help')"


def shutdown(ctl, node):
    """Release the audio devices and the serial port.

    exec keeps file descriptors open across the image swap, so without this
    the replacement process finds its own serial port already busy.
    """
    node.mic(False)
    node.speaker(False)
    time.sleep(0.3)   # let the USB-serial driver drain what was just written
    ctl.close()


def run_agent(args, ctl, node):
    print(f"[agent] pronto em {args.port} @ {args.sync_baud}. Ctrl+C para sair.")
    print("[agent] aceitando comandos da outra maquina.")
    while True:
        line = ctl.recv(timeout=None)
        if line is None:
            continue
        if not line.startswith("CMD "):
            continue
        rest = line[4:]
        seq, _, cmd = rest.partition(" ")
        cmd = unpack(cmd)
        print(f"[agent] <- {cmd}")
        try:
            reply = execute(node, cmd)
        except Exception as e:
            reply = f"ERRO: {e}"
        ctl.send(f"OK {seq} {pack(reply)}")
        if updater.pending_restart:
            # Only after the reply is on the wire: exec never returns, so a
            # restart handled any earlier would leave the far side waiting out
            # its timeout on a command that actually succeeded.
            print("[agent] reiniciando com o codigo novo...")
            updater.restart(cleanup=lambda: shutdown(ctl, node))


def run_console(args, ctl, node):
    replies = queue.Queue()

    def router():
        while True:
            line = ctl.recv(timeout=0.2)
            if line is None:
                continue
            if line.startswith("EVT "):
                for out in unpack(line[4:]).split("\n"):
                    print(f"\n[remoto] {out}")
            elif line.startswith("OK "):
                replies.put(line[3:])

    threading.Thread(target=router, daemon=True).start()

    seq = [0]

    def remote(cmd, timeout=8.0):
        seq[0] += 1
        want = str(seq[0])
        ctl.send(f"CMD {want} {pack(cmd)}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                got = replies.get(timeout=max(0.05, deadline - time.time()))
            except queue.Empty:
                break
            gseq, _, body = got.partition(" ")
            if gseq == want:
                return unpack(body)
        return "(sem resposta da outra maquina -- ela esta rodando --role agent?)"

    print(f"[console] {args.port} @ {args.sync_baud}. 'help' lista os comandos.")
    print("[console] prefixo 'r ' = outra maquina, 'b ' = as duas.\n")

    while True:
        try:
            line = input("fsk> ").strip()
        except EOFError:
            return 0
        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            return 0

        head, _, rest = line.partition(" ")
        target, cmd = "local", line
        if head.lower() in ("r", "remote", "remoto"):
            target, cmd = "remote", rest
        elif head.lower() in ("b", "both", "ambos"):
            target, cmd = "both", rest
        if not cmd.strip():
            print("  (comando vazio)")
            continue

        if target in ("local", "both"):
            try:
                out = execute(node, cmd)
            except Exception as e:
                out = f"ERRO: {e}"
            for row in str(out).split("\n"):
                print(f"  [local]  {row}")
        if target in ("remote", "both"):
            for row in str(remote(cmd)).split("\n"):
                print(f"  [remoto] {row}")
        if updater.pending_restart:
            print("  [local]  reiniciando com o codigo novo...")
            updater.restart(cleanup=lambda: shutdown(ctl, node))


def main():
    p = argparse.ArgumentParser(
        description="Console de controle do link acustico FSK, via porta serial")
    p.add_argument("--role", choices=["console", "agent"], required=True,
                   help="'console' tem o teclado; 'agent' obedece pela serial")
    p.add_argument("--port", required=True, help="porta serial (COM4, /dev/ttyUSB0)")
    p.add_argument("--sync-baud", type=int, default=115200)
    p.add_argument("--gain", type=float, default=0.8)
    p.add_argument("--squelch", type=float, default=0.005)
    p.add_argument("--dev-in", default=None, help="indice do dispositivo de entrada")
    p.add_argument("--dev-out", default=None, help="indice do dispositivo de saida")
    args = p.parse_args()

    for name in ("dev_in", "dev_out"):
        val = getattr(args, name)
        if val is not None and val.isdigit():
            setattr(args, name, int(val))

    try:
        ctl = Control(args.port, args.sync_baud)
    except Exception as e:
        print(f"Nao consegui abrir {args.port}: {e}", file=sys.stderr)
        return 1

    if args.role == "agent":
        emit = lambda text: ctl.send("EVT " + pack(text))
    else:
        emit = lambda text: print(f"\n[local]  {text}")

    node = AudioNode(gain=args.gain, squelch=args.squelch,
                     dev_in=args.dev_in, dev_out=args.dev_out, on_event=emit)

    try:
        if args.role == "agent":
            return run_agent(args, ctl, node)
        return run_console(args, ctl, node)
    except KeyboardInterrupt:
        print("\nSaindo...")
        return 0
    finally:
        shutdown(ctl, node)


if __name__ == "__main__":
    sys.exit(main())
