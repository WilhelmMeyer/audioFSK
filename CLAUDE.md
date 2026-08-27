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
./venv/bin/python app.py --tune tx     # transmit test pattern (link calibration)
./venv/bin/python app.py --tune rx     # meter the incoming signal

# scored two-machine test, synchronized over a serial cable (see linktest.py)
./venv/bin/python linktest.py --check --port /dev/ttyUSB0        # serial wiring only
./venv/bin/python linktest.py --role rx --port /dev/ttyUSB0      # start this side first
./venv/bin/python linktest.py --role tx --port COM4 --trials 5   # other machine

# interactive remote control of both machines' audio (see console.py)
./venv/bin/python console.py --role agent   --port /dev/ttyUSB0  # headless side
./agent.sh                                                       # same, supervised
./venv/bin/python console.py --role console --port COM4          # side with the keyboard
./venv/bin/pip install -r requirements.txt
```

`loopback_test.py` is the whole test suite — one script, no framework, prints `SUCCESS!`/`FAILED`. There is no lint or build step.

Needs PortAudio at the system level (`libportaudio2`) only for `app.py`. `loopback_test.py` runs without it.

## Architecture

Two layers, deliberately separated:

- **`modem.py` — DSP, no I/O.** Does not import `sounddevice`, spawns no threads, touches no files. Takes `np.ndarray` of samples, returns `bytes`, and vice versa. This is why `loopback_test.py` can exercise the exact live-path code with zero hardware. **Keep it that way** — any I/O, threading, or device concern belongs in `app.py`.
- **`app.py` — runtime.** Threads, queues, PortAudio stream, stdio/PTY interfaces.
- **`linktest.py` — runtime, scored test.** Same layering rule as `app.py`: it owns serial, audio, and threads, and imports the modem classes untouched. Cross-platform, so it and `console.py` are the entry points that run on the Windows side (`--pty` is POSIX-only).
- **`console.py` — runtime, interactive.** Remote control of both machines' audio over the serial cable. One `AudioNode` and one `execute()` run on *both* roles; `--role console` has a REPL, `--role agent` does not. Add a command in one place and both sides get it — do not fork the command table.
- **`serial_link.py` — the shared control channel.** `Control` (background line reader) plus `pack`/`unpack`, which escape newlines so a multi-line reply survives a line protocol. Both tools import it, so framing and timeouts cannot drift apart.
- **`updater.py` — git only, no serial and no audio.** Same layering rule as `modem.py`, one level up: it knows how to fetch, reset, and re-exec, and nothing about the wire that asked. `console.py` wires it to the command table.
- **`agent.sh` — supervisor for the follower machine.** Restarts `console.py --role agent` after a crash. A voluntary `restart` execs in place and keeps the PID, so it never reaches this loop; the wrapper is for unplugged adapters and vanishing audio devices.

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

**`--tune` is the first thing to reach for when a real acoustic link misbehaves.** Audio level is almost always the fault, not the DSP. `FSKDemodulator` exposes `input_rms`, `input_peak`, and `level_rms` (post-bandpass) from the last block; the ratio `level_rms / input_rms` separates "carrier present" from "room noise", which is what makes the diagnostics in `tune_rx_loop` distinguishable. Those metrics are computed before squelch and before bit decision, so they show what the sound card actually delivered.

**The squelch is a hard floor on receive level, and it is quadratic.** `mult = x[n]·x[n-D]`, so baseband amplitude goes as the *square* of the input amplitude. With the default `squelch=0.005`, a signal arriving at amplitude 0.05 lands at ~0.0025 baseband and is squelched to silence — zero bytes decoded, on a channel that is otherwise perfect. Measured: 0.05 amplitude decodes 0/256 bytes at `squelch=0.005` and 256/256 at `0.0001`. Received amplitude needs to be roughly ≥ 0.07 for the default. "No bytes at all, but `--tune` shows in-band energy" is this, not a DSP bug; `linktest.py --squelch` exists to test it.

**`linktest.py` uses the serial cable as an out-of-band control channel, never as a data path.** The payload is generated on both sides from a shared seed sent over the wire, so the bytes being scored only ever travel through the air. RX opens and warms the input stream *before* answering `ARMED`, which keeps device startup latency off the critical path so `GO` can act immediately; `GUARD` then only has to cover serial latency. Scoring goes through `difflib.SequenceMatcher` (with `autojunk=False` — above 200 elements it would treat common byte values as junk and destroy the alignment) because this link drops bytes rather than merely corrupting them, and one dropped byte shifts everything after it. An index-by-index compare scores a near-perfect link at ~50%.

**The in-band ratio must be a ratio of sums, never a mean of per-block ratios.** `level_rms / input_rms` per block, averaged, is wrong: a near-silent block has an almost-zero denominator while the bandpass is still ringing from its own `lfilter_zi` initial state, and a single such block throws the window past 100% — observed at 9713% before the fix. Accumulate `input_rms` and `level_rms` separately, divide once, clamp to 1.0. `linktest.py` and `console.py` do this. `tune_rx_loop` in `app.py` still takes the instantaneous single-block ratio and is unclamped, so it can read above 100% on a transient.

**The two machines talk on two layers, and `pull` is the slow one.** The serial command table acts in milliseconds; `pull` moves code, committed to the remote by the leading machine and fetched by the follower. `updater.pull` **hard-resets** rather than merging — the follower's working tree is not where work happens, and a merge conflict on a machine with nobody at the keyboard is a dead end. That makes it destructive, so a dirty tree aborts the pull unless `pull force` is given.

**`pull` follows `updater.DEFAULT_REF` (`origin/main`), never the branch's own tracking ref.** Deriving the default from `@{u}` looks tidier and is a trap: a follower left on an old feature branch resolves it to whatever that branch tracks and hard-resets *backwards*, deleting the files currently serving the link. Observed — it removed `console.py` and took the serial channel down with it. Pass `pull <ref>` for anything else.

**A pull that cannot run must undo itself, because nothing else can.** `updater._broken()` compiles `console.py`, `serial_link.py`, `modem.py`, and `updater.py` after the reset; if any fails, the pull reverts to the previous commit and reports the error over the wire. `request_restart` refuses for the same reason. The asymmetry is the point: on this machine the serial channel is the only way in, and it is made of the same files being replaced — so once a restart lands on code that will not import, the process dies and takes with it the channel that would have carried the fix. Compiling is not proof the code is correct, only proof the machine will still answer.

**`updater.restart` execs with `sys.orig_argv`, not `sys.argv`.** `sys.argv` drops the interpreter's own flags, so a process started as `python -u console.py` came back fully buffered and its log went silent — indistinguishable from a restart that never happened.

**A `pull` never restarts by itself.** Re-exec drops both audio streams, so a pull landing mid-measurement would silently undo the levels the far side just dialed in. `pull` sets `updater.pending_restart` (only when a `.py` actually changed) and says so; the far side sends `restart` when it is ready. Both loops act on that flag *after* the reply is already on the wire — exec never returns, so restarting any earlier would leave the far side timing out on a command that in fact succeeded. `shutdown()` must close the serial port before the exec: file descriptors survive the image swap, and the replacement process would find its own port busy.

**Throughput measured on a continuous `0x55` tone overstates the link.** Framed 8N1, `0x55` is `0` `10101010` `1` — a perfectly periodic square wave at half the baud rate. The start-bit detector looks for a falling edge, and every symbol boundary offers one, so it can lock onto the wrong edge and still produce plausible bytes. Measured over a real acoustic link: a steady tone decoded at up to 100 B/s (of 120 theoretical) while the received bytes alternated between `0x55` and `0x75` — one bit off, the signature of framing on the wrong edge. The same link recovered nothing from an actual message. A periodic signal also reaches acoustic steady state, so it survives room reverberation that smears aperiodic data. Grade a link with `linktest.py` and its random payload; treat tone throughput as "carrier arrives", nothing more.

**`AudioNode.level()` resets its window, and must keep doing so.** It reports the interval since the previous reading, not since the process started. With the accumulators left running the reading is a lifetime average over a peak that never decays, so a tone that stopped seconds ago still reads −25 dBFS and three different microphones return byte-identical numbers. A meter that cannot fall is worse than no meter: it reports a healthy level while you are chasing silence.

**Preamble (`0x55 × 10 + 0xFF`) lives in `app.py`, not `modem.py`.** It's a link-layer concern. Any future framing, CRC, or ARQ belongs at that same level — above the modem, not inside it.

**There is no error detection.** UART framing was chosen so the modem behaves as a dumb serial line and can be plugged into `/dev/pts/N` for the existing serial ecosystem. A corrupted byte arrives corrupted. The preamble is also not stripped on RX — stdio mode does a crude filter (`b < 128 and b != 0xff`), PTY mode passes everything raw.

`pyserial` is in `requirements.txt` but nothing in the project imports it.
