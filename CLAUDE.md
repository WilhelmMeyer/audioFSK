# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Acoustic FSK modem. Bell 202 tones (mark 1200 Hz, space 2200 Hz), 1200 baud, UART 8N1 framing. Sends bytes as sound over the soundcard and recovers them on the other side. Exposes the acoustic channel as a virtual serial device.

Not a git repository.

## Commands

Interpreter is the venv, not system Python:

```bash
./venv/bin/python loopback_test.py     # end-to-end DSP test, no audio hardware needed
./venv/bin/python app.py               # live modem, stdin/stdout mode
./venv/bin/python app.py --pty         # live modem, virtual serial device
./venv/bin/pip install -r requirements.txt
```

`loopback_test.py` is the whole test suite — one script, no framework, prints `SUCCESS!`/`FAILED`. There is no lint or build step.

Needs PortAudio at the system level (`libportaudio2`) only for `app.py`. `loopback_test.py` runs without it.

## Architecture

Two layers, deliberately separated:

- **`modem.py` — DSP, no I/O.** Does not import `sounddevice`, spawns no threads, touches no files. Takes `np.ndarray` of samples, returns `bytes`, and vice versa. This is why `loopback_test.py` can exercise the exact live-path code with zero hardware. **Keep it that way** — any I/O, threading, or device concern belongs in `app.py`.
- **`app.py` — runtime.** Threads, queues, PortAudio stream, stdio/PTY interfaces.

Data flow:

```
stdin/PTY ──> tx_byte_queue ──> [modulator thread] ──> tx_audio_queue ──┐
                                                            [audio_callback]
stdout/PTY <── rx_byte_queue <── [demodulator thread] <── rx_audio_queue ┘
```

### Things that break if you don't know them

**Both modem classes are stateful and single-stream.** `FSKModulator` carries `self.phase` across calls (continuous-phase FSK — resetting it produces out-of-band clicks). `FSKDemodulator` carries `bpf_state`, `lpf_state`, and `prev_samples` across calls, because audio arrives in 2048-sample blocks and stateless `lfilter` would put a transient at every block boundary and destroy the bits there. One instance per stream; use `reset()` between sessions, never share across threads.

**`audio_callback` runs on PortAudio's real-time thread.** It only moves data between queues. All DSP happens in normal threads. Do not add work there.

**Demodulation is delay-and-multiply, not correlation.** `bandpass → x[n]·x[n-D] → lowpass`, with `D = fs/(4·f_center)` ≈ 90° at 1700 Hz. After the lowpass, mark is positive and space is negative, so bit decision is a sign test. No carrier recovery involved.

**Squelch works on baseband amplitude** (`|baseband| < squelch → force +1.0`), not on a separate energy envelope — `mult` is already proportional to signal energy. This avoids a second stateful filter in the streaming chain. Threshold is hardcoded at `0.005` in `app.py` and does not adapt to ambient noise.

**Preamble (`0x55 × 10 + 0xFF`) lives in `app.py`, not `modem.py`.** It's a link-layer concern. Any future framing, CRC, or ARQ belongs at that same level — above the modem, not inside it.

**There is no error detection.** UART framing was chosen so the modem behaves as a dumb serial line and can be plugged into `/dev/pts/N` for the existing serial ecosystem. A corrupted byte arrives corrupted. The preamble is also not stripped on RX — stdio mode does a crude filter (`b < 128 and b != 0xff`), PTY mode passes everything raw.

`pyserial` is in `requirements.txt` but nothing in the project imports it.
