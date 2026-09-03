# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Acoustic modem. Sends bytes as sound over the soundcard and recovers them on the other side, and exposes the acoustic channel as a virtual serial device.

It started as Bell 202 alone (mark 1200 Hz, space 2200 Hz, 1200 baud, UART 8N1) and now carries **three physical layers plus an error-correcting layer**, because Bell 202 never delivered a message over the real acoustic link. Which one to use is a measured question, not a preference:

| layer | rate | measured on the air |
|---|---|---|
| Bell 202, 1200 baud | 120 B/s on paper | never delivered a message |
| MFSK voted + FEC, 100 baud | ~1.8 B/s | 4 of 4 blocks whole |
| MFSK parallel + FEC | ~5.9 B/s | 5 of 9 blocks |
| **M-ary 16 tones + FEC, gain 0.5** | **~9.4 B/s** | **9 of 11 blocks** |

Whole-file transfer does not work yet: 1 packet of 21 with 81-byte packets, where 24-58 byte blocks decoded 9 of 11 over the same link.

This is a git repository.

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
./venv/bin/python -u console.py --role agent --port /dev/ttyUSB0 # headless side; -u matters, see below
./agent.sh                                                       # same, supervised
./venv/bin/python console.py --role console --port COM4          # side with the keyboard
./venv/bin/pip install -r requirements.txt

# record the far side transmitting a known payload, then score demodulators offline.
# capture.py and recvfile.py own the serial port AND the input audio, so they run on
# the *console* side and record the *agent* transmitting -- point --port at whichever
# machine holds the keyboard, not at the one making the sound.
./venv/bin/python capture.py --port COM4 --mode mary --fec --gain 0.5 --trials 3 --label o-que-mudou
./venv/bin/python capture.py --port COM4 --chirp "400 4200 10" --label varredura
./venv/bin/python bench.py                                    # scores captures/

# one machine only: speaker out, microphone in, no serial cable and no far side
./venv/bin/python selfcapture.py --mode mary --fec --gain 0.5 --trials 3 \
    --in-device 26 --out-device 20 --link bluetooth --out captures-self
./venv/bin/python selfcapture.py --mode mary --fec --sync-chirp --trials 8   # com as varreduras
./venv/bin/python align.py captures-self      # quanto do erro e sincronismo, e quanto e canal
./venv/bin/python channel.py captures/<stem>.json --bins 76   # measured frequency response

# pull a file across the link, stop-and-wait ARQ driven from this end
./venv/bin/python -u recvfile.py --port COM4 --remote-file testcard.bmp --out got.bmp \
    --fec --mode mary --gain 0.5 --packet-size 64 --repeat 1
```

`loopback_test.py` covers the Bell 202 and MFSK layers, and judges MFSK against the impairments actually measured on the two-machine link (a −16 dB high-frequency tilt, the output limiter's envelope, 80 ms reverberation) rather than generic AWGN. It is the whole test suite — one script, no framework, prints `SUCCESS!`/`FAILED`. There is no lint or build step.

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
- **`capture.py` — runtime.** Records the far machine transmitting a known payload and saves the audio plus a JSON of what was sent. Owns serial and audio; drives the far side through the `console.py` agent command table, so the Windows side needs nothing new. The local console must be stopped first, since the serial port takes one owner.
- **`selfcapture.py` — runtime, one machine.** Records this machine transmitting to itself through the air. Same on-disk format as `capture.py`, so the offline tools do not distinguish them; no serial port and no far side. For developing an idea when the second machine is not on the desk.
- **`align.py` — offline.** Splits the M-ary error rate into the part synchronisation could fix and the part that is the channel, by brute-forcing the symbol offset and by handing the detector divisors it could not have computed. Answers "is this worth building" before anything is built.
- **`bench.py` — offline.** Scores demodulator variants against the recordings. No audio device, no serial. Adding an idea means adding one entry to its `VARIANTS` list.
- **`recording.py` — disk only.** The on-disk format for a capture: a 32-bit float WAV plus a JSON sidecar sharing a stem. Same layering rule as `modem.py`: no device, no port.
- **`scoring.py` — payload generation and alignment-tolerant scoring**, factored out of `linktest.py` so the offline bench scores a capture exactly the way the live test scores the wire. If these drifted, a gain measured on recordings would not mean the same thing on the link.
- **`fec.py` — error correction, no I/O and no state.** Convolutional K=7 with a soft-decision Viterbi decoder, interleaving, repetition, and the sync word. Same layering rule as `modem.py`: bits and log-likelihoods in, bytes out.
- **`channel.py` — offline.** Turns a `--chirp` capture into a usable-frequency map. Disk only, like `recording.py`.
- **`xfer.py` — packets: split, build, parse, CRC.** Above the modem, below the tools. `recvfile.py` and `console.py` both use it.
- **`recvfile.py` — runtime.** Pulls a file with stop-and-wait ARQ driven entirely from the receiving end; the far side stays stateless and only answers `sendpkt`/`fecpkt`. Owns serial and audio, so the console must be stopped first.

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

**Run anything long with `-u` when its output is redirected.** To a terminal Python line-buffers and all is well; to a file or a pipe it switches to block buffering and the output stays empty for minutes. That applies to the agent, to `recvfile.py` and to `capture.py`, and the damage is not cosmetic: **silent output is indistinguishable from a process that never started**. It has cost this project an afternoon twice, once diagnosed as a failed remote `restart` that had in fact succeeded. `agent.sh` passes it. This is the same failure the next entry describes, arriving by a different route.

**`updater.restart` execs with `sys.orig_argv`, not `sys.argv`.** `sys.argv` drops the interpreter's own flags, so a process started as `python -u console.py` came back fully buffered and its log went silent — indistinguishable from a restart that never happened.

**A `pull` never restarts by itself.** Re-exec drops both audio streams, so a pull landing mid-measurement would silently undo the levels the far side just dialed in. `pull` sets `updater.pending_restart` (only when a `.py` actually changed) and says so; the far side sends `restart` when it is ready. Both loops act on that flag *after* the reply is already on the wire — exec never returns, so restarting any earlier would leave the far side timing out on a command that in fact succeeded. `shutdown()` must close the serial port before the exec: file descriptors survive the image swap, and the replacement process would find its own port busy.

**There are three physical layers in `modem.py`, and they fail differently.** `FSKModulator`/`FSKDemodulator` is Bell 202 at 1200 baud, deciding bits by the *sign* of a delay-and-multiply discriminator — fast, but any channel that weakens one tone relative to the other biases every decision the same way. `MFSKModulator`/`MFSKDemodulator` is multi-tone at 100 baud: five tones sound at once for each bit, and the bit is decided by a vote. Scaling the signal scales both sides, so gain drops out entirely: measured, it decodes identically from ×2 down to ×0.001, on the same tilt where the Bell 202 path loses the whole payload. Twelve times slower, and worth it whenever amplitude cannot be trusted. `MaryModulator`/`MaryDemodulator` is the third: 16 tones, exactly one sounding at a time, four bits per symbol. `console.py mode fsk|mfsk|mary` switches; each layer keeps its own instances so no filter or phase state crosses over.

**The M-ary layer exists for power, and that is the largest lever measured here.** A chord of five tones has to be divided by five to stay inside the same peak amplitude, so every tone leaves the speaker 14 dB down — which is why a transmitted tone arrived only 2 to 7 dB above the same frequency when it was *not* transmitted, and why per-pair error sat at 15-30%. One tone at a time gets that back: received rms went from 0.07-0.09 on the chord layers to 0.14 on the same link, and it is the fastest and most reliable path measured on the air.

**M-ary divides each tone by its own running floor before comparing, and here that is sound.** A tone parked in a null of the room's comb response can never win a comparison. With 16 tones each is silent 15 symbols out of 16, so its long-run average energy *is* the noise floor at that frequency — the estimate is not contaminated by the signal it exists to measure, which is exactly what went wrong when the same idea was tried on the chord layers. `_update_floor` also leaves the winning tone out of each update, for the same reason. Neighbouring tones are Gray-coded so the confusion the channel actually makes costs one bit, not four.

**M-ary is the layer that reverberation hurts most, and the guard interval does not save it.** The previous symbol's tone competes directly with the current one instead of fading both chords together: at 80 ms of simulated tail a third of symbols land wrong, and widening the guard from 0.15 to 0.60 changes nothing — the tone is lingering, not the window straddling a boundary. This matters less than it reads, because the real link has *no* measurable reverberation (see below); the 80 ms case is a property of `loopback_test.py`, not of the room.

**Transmit gain is layer-dependent, and getting it wrong looks like a broken channel.** M-ary puts one tone at full amplitude where a five-tone chord put one fifth, so the far side's output limiter clips it. Measured, same payload and same link: gain 0.8 recovered 5 blocks of 15, gain 0.5 recovered 4 of 4, gain 0.25 recovered 2 of 4. Use `gain 0.5` in `mary`. The symptom of the wrong gain is blocks failing at random with received peak ≥ 0.8, with no relation to block size — which is easy to misread as timing drift, and was.

**MFSK votes, it does not sum.** The ten tones are five pairs (constant `MFSK_PAIRS`), each pair 200 Hz apart so the channel treats both members alike; each pair casts one vote for whichever of its two tones arrived stronger, and the majority is the bit. Summing the two chords' total energy instead — which is what the code did before — lets amplitude buy the answer: measured on a real link, one chord arrived with twice the energy of the other and the detector called almost everything the louder symbol, 27% of bytes right. Under a vote, a tone that is loud for the wrong reason still carries exactly one vote and the other four outrank it. Sounding five frequencies at once exists for this; summing threw it away.

**Polarity alternates along the band: on pairs 0, 2 and 4 the lower tone means 0, on pairs 1 and 3 it means 1.** Both chords therefore land on nearly the same mean frequency (1620 vs 1660 Hz), so a tilted channel favours neither bit. Do not "tidy" this into all-low-means-zero.

**A vote alone decodes an empty room forever.** A vote is a ratio, so five tones of pure noise still elect a bit — observed, 485 bytes decoded out of silence. `MFSK_PRESENCE_MIN` is the second condition: each pair's losing tone is a frequency nobody transmitted, so the median winner/loser energy ratio tells a real symbol from a room. It is 1.3, deliberately low — measured, 1.5 and above starts rejecting genuine symbols under an 80 ms reverberation tail while stopping no additional noise, because the vote margin (`contrast_min`) is what actually rejects noise.

**There is no per-tone equaliser, and one was tried.** Dividing each tone by a running average of its own energy sounds right (it would stop a tone sitting on a room resonance from carrying a permanently louder vote) and it cost the reverberant cases outright: the average absorbs the previous symbol's decaying tail and begins treating it as that tone's normal level. Pairing already does that job and does it without memory. The `_score` docstring once described this equaliser as present while the code summed raw energy — the comment was the only place it ever existed.

**The MFSK tone sets are chosen against *cross*-harmonics, not all harmonics.** Speakers and microphones distort, and distortion manufactures harmonics. A 2nd or 3rd harmonic of one chord's tone landing on the *other* chord is evidence for the wrong symbol; within the same chord it is harmless, since it reinforces the right answer. The current ten tones have zero such collisions, with a 200 Hz minimum separation between any two of them.

**200 Hz within a pair is a measured optimum, not a round number.** Widening it to 250 Hz was tried and packet recovery under the loopback's simulated reverberation fell from 7/8 to 3/8. The symbol window after the guard interval is 8.5 ms, giving roughly 118 Hz of frequency resolution, and pushing the members of a pair apart necessarily pushes the pairs themselves closer together. The loopback packet test is what notices when this goes wrong; re-measure before changing it.

**MFSK needs an alternating preamble and a trailing idle; neither is optional.** Timing recovery is an early/late gate steered by decision contrast, which peaks when the window sits inside one symbol — so it needs *transitions* to lock onto, and a preamble that idles at mark teaches it nothing. At the other end the demodulator keeps just over a symbol buffered, so a burst that stops dead strands its last byte there. `MFSKModulator.idle()` supplies the tail, and `console.py`'s transmit feeder appends `idle(4)` after any non-Bell-202 burst for this reason — without it every `send` silently lost its final byte. **This is true of M-ary too**, and the feeder tested for `mode == 'mfsk'` alone until 5598abc: a ten-byte M-ary send arrived as `ABCDEFGHI` on a channel with no impairment whatsoever. Bell 202 needs no tail and its modulator offers none. The guard interval (35% of each symbol, skipped before measuring) is what makes reverberation survivable: measured, it took accuracy from 76.5% to 100% on a channel with an 80 ms tail.

**The link must work in both directions, and for a long time it only worked in one.** Not for an acoustic reason: `console.py` could *transmit* an error-corrected block but not receive one, because soft decoding lived only in `bench.py` and `recvfile.py` — and both own their own audio, so both only ever run on the **console** side. Swap the roles and the receiver becomes the headless agent, which could only hard-decode. The working direction therefore followed whoever held the keyboard instead of being a property of the link. `fecrx` (5598abc) fixes it in the one place that makes it symmetric: the shared command table, where `execute()` is identical on both roles, so a single entry gives both machines the capability. Anything else that only one side can do belongs there too — and when adding it, check `fec_layer`: parallel MFSK keeps its own instance pair, so naming the layer as `self.mode` puts transmitter and receiver on different objects.

**Redundancy is not a tuning knob here, it is what makes the link work.** Measured over 19 blocks of 23 bytes on M-ary, recovered whole:

| `fecrep` | Windows->Linux | Linux->Windows |
|---|---|---|
| 1 | 0 of 6 | 1 of 6 |
| 2 | 2 of 6 | 5 of 6 |
| 4 | 4 of 7 | not measured |

Rate-1/3 convolutional coding *alone* recovers essentially nothing in either direction, so do not drop to `fecrep 1` to save air time. Failures are almost always "sync found, then garbage" rather than "sync not found": the block is located and the Viterbi cannot repair it, which means symbol error rate, not synchronisation. Three trials is inside the noise — one batch of 3 read 3/3 and the next 4 read 1/4 at identical settings, which is how a lucky run gets mistaken for a fix.

**Grade the link with `fecrx`, never with `rx`.** The hard path in M-ary has no framing at all: four bits per symbol, eight per byte, and nothing to resynchronise on. Start decoding one symbol early or late and every byte comes out with its nibbles swapped. Measured on a *synthetic, near-clean* channel it recovered the payload 4 times in 16, and never once when an odd number of symbols preceded it. That lottery is the whole of the "sometimes readable, sometimes not" behaviour that looks like an unstable room. `0x55` cannot reveal it either — shifted by a nibble it is still `0x55`, so the preamble reads intact in both phases. Picking the phase from the `0xFF` marker was tried and measured *worse* (2 of 16), because the phase can change mid-block when the early/late gate slips a symbol. `fec.find_sync` is the only mechanism here that solves alignment, correlating 31 bits over the soft stream to find the start at the right bit — which is why every trustworthy number in this file comes from the FEC path.

**Calibrate transmit gain on a burst, never on a tone.** An M-ary burst switches tone abruptly every symbol, and those transients carry about 2.5x the peak of a steady tone: measured at one gain, a continuous tone arrived at peak 0.40 while the FEC burst from the same machine arrived at 1.00 — hard clipping, invisible to anyone calibrating with `tone` or `tonef`. Send a real `fecsend` and read the far side's `level` peak, targeting roughly 0.4-0.6.

**Measure a frequency by sending that frequency, not by sweeping past it.** `tonef` plays one tone and `meas` reports what arrived in that band beside the wide-band level of the same window; both are in the shared command table so either machine can play and either can measure. A chirp answers a different question, and answered it wrongly here: it reported half the M-ary tones below the noise floor and 1700 Hz at -27 dB, the worst point in the sweep, where stepped tones put that same tone at +50 dB. Take at least three repetitions and the median — one passing noise in the room lands in a single window and invents a dead tone. Measured this way, all 16 tones arrive with healthy margin in *both* directions, so a nulled tone does not explain why one direction decodes worse than the other.

**`squelch` means a different quantity in each layer.** Bell 202 gates on absolute baseband amplitude (~0.005); MFSK and M-ary gate on `contrast_min`, a ratio in 0–1 (~0.15). They are not interchangeable — setting 0.005 as a contrast threshold is barely a gate at all. `AudioNode.threshold()` routes the console's one `squelch` command to whichever the active mode uses.

**Throughput measured on a continuous `0x55` tone overstates the link.** Framed 8N1, `0x55` is `0` `10101010` `1` — a perfectly periodic square wave at half the baud rate. The start-bit detector looks for a falling edge, and every symbol boundary offers one, so it can lock onto the wrong edge and still produce plausible bytes. Measured over a real acoustic link: a steady tone decoded at up to 100 B/s (of 120 theoretical) while the received bytes alternated between `0x55` and `0x75` — one bit off, the signature of framing on the wrong edge. The same link recovered nothing from an actual message. A periodic signal also reaches acoustic steady state, so it survives room reverberation that smears aperiodic data. Grade a link with `linktest.py` and its random payload; treat tone throughput as "carrier arrives", nothing more.

**`AudioNode.level()` resets its window, and must keep doing so.** It reports the interval since the previous reading, not since the process started. With the accumulators left running the reading is a lifetime average over a peak that never decays, so a tone that stopped seconds ago still reads −25 dBFS and three different microphones return byte-identical numbers. A meter that cannot fall is worse than no meter: it reports a healthy level while you are chasing silence.

**Bits have to be repairable where they land; a CRC only reports the damage.** The link delivers 10-25% of its bits wrong, so almost every block is ruined and retransmission has nothing to fall back on. `fec.py` is convolutional K=7 with soft-decision Viterbi. Measured on 64-byte blocks against simulated bit errors: rate 1/2 hard fails past 8%; rate 1/2 soft holds to 8%; rate 1/3 soft is whole to 13% and 90% at 16%; rate 1/3 repeated twice is whole to 25% and 90% at 30%. Two of those columns cost nothing — soft decision is a number the demodulator already computed and used to throw away, and it alone moves the tolerable error rate from 8% to 13%.

**A coded block carries a 31-bit m-sequence sync word, and it is found by correlation, never by counting symbols.** The early/late gate consumes a different number of samples per symbol as it steers, so the block start drifts over a preamble, and a block beginning one bit late decodes to nothing. Observed: reverberant cases recovered 1 byte of 24 with a counted offset and all 24 with a correlated sync.

**In parallel MFSK the sync word is read by voting, not position by position.** It is the one part of a parallel block where every pair carries the same bit, so average the pairs and correlate one value per symbol. Matching position by position asks every pair to agree, and a pair sitting in a null answers the same way whatever was sent — two such pairs hold the score under any useful threshold. Observed: eight parallel captures out of nine never found their sync word, which read exactly like a decoder too weak for the channel and was not.

**Repetition only buys anything if the copies land on different pairs.** The coded length is a multiple of the pair count, so tiling the block puts every copy of a bit on the *same* pair, and one pair in a null takes all of them down together — rate 1/3 repeated six times still failed where voting succeeded at two. `fec.pair_map` places copy r of coded bit i on pair (i + r) mod npairs. With that, repetition of two clears the same reverberation.

**Parallelism does not create robustness; it creates a dial.** What protects a bit is the number of independent observations of it. Voting at repetition 2 gives ten per bit and spends six symbols; parallel at repetition 10 gives ten per bit and spends the same six. The gain is being able to spend *less* redundancy on a channel with margin — not free reliability. `fecpar on` and `fecrep <n>` are the two knobs, and `fecrep` in particular is a property of the link, not of the code.

**`fecrep` must be sent to the far side, never assumed.** A mismatch is undetectable at the decoder: it produces garbage that fails the CRC, which reads exactly like a bad channel. Observed — the sender coding at repeat 2 against a receiver assuming 1, every packet retried to exhaustion on a link that was working. `recvfile.py` sends it during setup for this reason.

**`MaryDemodulator.demodulate_soft` returns four values per symbol, not one.** Four bits per symbol means four log-likelihoods. A length in that array is not a count of symbols, and reading it as one makes a normal 9-second window look like 37 seconds of backlogged audio — which was diagnosed, wrongly, as a starved capture queue.

**Drain the capture queue before the request goes out, never after.** The far side starts playing the moment it is asked, so audio arriving during the serial round trip is already the head of the burst. Draining afterwards throws the preamble away, and with no preamble there is no symbol clock to lock: every packet then fails on a link that is working.

**The measured channel, which supersedes anything assumed about it.** Band 550-3500 Hz is usable. Above 4 kHz SNR collapses (12 dB at 4000, 8 dB at 4500, ~0 at 5000) and above 6 kHz it is negative, with the level pinned at the noise floor — so **ultrasound is not viable on this hardware**; the argument for it is right (rooms are quiet up there) and the transducers simply do not reach. The response is a *comb*, not a curve: at 50 Hz resolution neighbouring bins differ by 13-18 dB, and two of the original ten MFSK tones sat in nulls and voted like coins. And there is **no measurable reverberation** — the tail after a burst does not decay, it stops at the noise floor. Re-measure with `capture.py --chirp` plus `channel.py` before choosing any frequency.

**A pinned audio device index rots, and the failure reads like broken hardware.** Numbering shifts when anything is plugged in or removed. Observed on a machine whose audio was fine: five indices gave `Invalid device`, `Device unavailable`, `Invalid sample rate` and a `DirectSound error` — four *different* errors, which is the tell, since a genuinely wrong device fails the same way every time. `dev out auto` hands the choice back to the host and fixed it. Ask whether the far machine plays any sound at all before suspecting the code.

**`os.execv` does not mean the same thing on Windows.** On POSIX it replaces the process image and the PID survives; on Windows the C runtime spawns a new process, terminates the caller, and the replacement loses its console — so the agent went silent on `restart` and never answered again, twice, reading exactly like a pull that landed on code that would not import. `updater.restart` spawns explicitly and exits there, after a pause for the serial port to actually come free.

**`pack` escapes CR as well as LF.** The line reader splits on both, so a bare carriage return in a reply truncated it and discarded the rest silently. Windows device names carry CRs, so `devs` from that side stopped mid-list at exactly the entry being looked for.

**Two sync sweeps bracketing a frame beat the early/late gate, and the second one is what makes it worth doing.** `modem.chirp` puts an 80 ms swept tone at each end of a coded frame and `find_chirp_pair` recovers both by matched filter. The first peak gives the frame's start as an absolute sample index; the interval between the two, divided by the symbols it spans, gives the *measured* samples per symbol -- 479.96 with a spread of 0.07 where the nominal is 480. Scored on eight recordings of the same link:

| alignment | bits right | blocks whole |
|---|---|---|
| early/late gate | 87.7% | 5 of 8 |
| brute-forced best offset (knows the answer) | 89.3% | 7 of 8 |
| leading sweep only | 88.4% | 8 of 8 |
| both sweeps, period measured | 89.0% | 8 of 8 |

Two sweeps land within 0.3 points of an oracle that was handed the correct offset, for 220 ms on a 6.4 s frame. The gate is not bad on average -- it sits about a point below the best offset eight times in nine -- it *collapses*: on one recording it read 49.0% of bits where a frozen clock at the right offset read 84.9%. Insurance against that collapse, not a better average, is what this buys.

**Swept, not clicked, and ordered by position, not by height.** A click has the same detectability and a far worse crest factor, and this layer already runs at `gain 0.5` because of the far side's limiter. Worse: the two sweeps are identical and the channel decides which arrives louder -- measured, the *trailing* one won four times in eight, by margins under 2%. Taking the strongest peak as the leading one therefore reversed the pair half the time, and a reversed pair is not a weak detection but a confident wrong answer: both peaks stood at 44-52x the noise floor while the frame could not be found at all. Sort the peaks by index.

**The sweeps are a runtime switch, `syncsweep`, and they default off — the default is the safety.** They change the frame, so both machines must agree: a receiver expecting them that finds none falls back to the gate and only loses the improvement, but a transmitter sending them to a receiver that is not looking puts 80 ms of swept tone where the first preamble symbols should be. The hazard is not the mismatch itself, it is how the mismatch arrives — `pull` reaches one machine at a time, and on the follower the serial channel is made of the files being replaced. Defaulting off means a pull that lands on one end only changes nothing; `b syncsweep on` then turns both on in one command. Scored through `console.py`'s own `fec_read` over the eight `captures-chirp` recordings: the gate recovered 5 blocks of 8, the sweeps 8 of 8, with the period measured between 479.87 and 480.11 samples per symbol.

**The receiver reads the sweeps off the stored audio, not off the accumulated soft values, and it has no choice.** The streaming path demodulates each block as it arrives and steers as it goes, so an offset found afterwards cannot be applied to decisions already made. `AudioNode._sweep_llr` re-demodulates `fec_audio` — kept for exactly this kind of second reading — with `steer=False`, the sweep-derived `skip`, and the measured `period`. Transmitter and receiver both get the frame's symbol count from `AudioNode.mary_frame_symbols`, one function called by both, because a span wrong by one symbol is a period wrong by a fifth of a sample and the receiver does not have the payload to derive it any other way — only its length, which `fecrx on <n>` already gave it.

**`fecpkt` goes through the same `_fec_frame` as `fecsend`, so `recvfile.py` sends `syncsweep off` at setup.** It sends `fecrep` for the same reason and the failure has the same shape: the far side keeps its own value, a mismatch is undetectable at the decoder, and the packets that then fail read as a channel that got worse. One serial round trip at setup buys that away. Teaching `recvfile.py` to use the sweeps is worth doing and has not been measured.

**A per-tone pilot is measured and dead, and the reason generalises.** The obvious use for a known symbol is to learn each tone's channel gain and divide by it. Measured against a *perfect* such divisor, computed offline from the known payload: 80.9% of bits, against 88.4% for the blind running floor already in the code. Dividing by the gain is the wrong operation -- the decision "is this tone present" wants energy over the *noise* at that frequency, not over the signal. And a perfect noise-floor divisor scores 88.4% against the blind estimate's 88.3%, so the blind estimate is already at its ceiling: with 16 tones each is silent 15 symbols in 16, and a pilot would offer far fewer samples of the same quantity. Nothing to teach it. The residual ~12% of bits wrong survives perfect timing *and* a perfect floor, and is the channel itself.

**An inter-symbol silence helps the bits and does not pay for itself.** `marygap` measured over twelve recordings: gap 0 gave 86.7% of bits, 0.15 gave 88.0%, 0.30 gave 88.9%. Monotonic, and still a bad trade -- 30% of the air time for two points, where the same 30% spent on redundancy buys more. Block recovery disagreed with the bit trend (3/4, 4/4, 1/4) because at `fecrep 1` this link sits exactly on the rate-1/3 cliff, where four recordings per point cannot resolve a coin flip.

**Bit accuracy has to be measured against one ruler.** The first version of `align.py` scored at the position `find_sync` chose when sync was found and at the best slide when it was not. The best slide is chosen to flatter and the sync position is not, so the *failures* scored higher than the successes: the setting with the worst block recovery reported the highest bit accuracy, which read as a paradox about the channel and was two rulers. Always take the best slide, for every row, and keep blocks recovered as the separate honest number.

**`loopback_test.py` cannot see a timing-acquisition regression.** Its frame opens with a bit-level alternating preamble that hands the gate a lock before the payload starts, so symbol timing never has to be *acquired*. A change that broke acquisition outright — recovery on the real link fell to 6% while brute-forcing the correct offset over the same audio gave 87-94% of bits right — passed the suite without complaint. Anything touching timing must also be scored against `captures/`.

**With few recordings, byte recovery is a noisy way to choose a parameter.** Neighbouring settings scored 8% and 22% with no trend, purely from which blocks happened to land. To decide a fine adjustment, measure *bit* accuracy at a brute-forced alignment, which is stable, or record far more.

**Recordings exist because judging an idea by transmitting it measures the idea and the room at once, and the room does not hold still** — two runs of identical code disagree. A recording is a fixed channel, so ten variants in `bench.py`'s `VARIANTS` list can be scored against the same seconds of real reverberation and the numbers are comparable. It also drops the cost of testing a one-line change from a two-machine round trip to seconds.

**Preamble (`0x55 × 10 + 0xFF`) lives in `app.py`, not `modem.py`.** It's a link-layer concern. Any future framing, CRC, or ARQ belongs at that same level — above the modem, not inside it.

**The 8N1 path still has no error detection, and that is deliberate.** UART framing was chosen so the modem behaves as a dumb serial line and can be plugged into `/dev/pts/N` for the existing serial ecosystem. On that path a corrupted byte arrives corrupted, and the preamble is not stripped on RX either — stdio mode does a crude filter (`b < 128 and b != 0xff`), PTY mode passes everything raw. Error detection and correction live *above* it, in `xfer.py` (CRC, packets) and `fec.py` (correction), reached through `fecsend`/`fecpkt`/`fecrx` and `recvfile.py --fec`. Do not push either down into `modem.py`.

**Dropping 8N1 framing inside a coded block removes a failure mode rather than mitigating it.** Under 8N1 a single corrupted start or stop bit shifts every byte after it, so one bad bit destroys the remainder. A fixed-length block has nothing to shift. This is a large part of why the coded path works where the byte-stream path never did.

**A single machine can record a real acoustic link, and what it cannot reproduce is specific.** `selfcapture.py` plays through the speaker and records through the microphone on the same soundcard, writing the same `recording.py` pair `capture.py` writes, so `bench.py` and `align.py` score it without knowing the difference. The air, the room's comb, the limiter and the microphone are all real. What is missing: with a *wired* speaker both ends share the soundcard's clock, so sample-rate drift -- part of what the early/late gate exists to correct -- is absent and timing results come out optimistic. A *Bluetooth* speaker has its own crystal and puts the drift back, at the cost of a lossy codec the real link does not have. `--link` records which, and the two must not be averaged together.

**A Bluetooth sink is not ready the moment the previous process lets go of it.** For a second or two it is present and advertises zero output channels, and an open in that window fails with `Invalid number of channels` -- which does not sound like a stale device and cost two gain sweeps their last setting before it was recognised. Retrying does not help; waiting does. `selfcapture.wait_ready` polls until the sink declares a channel, re-initialising PortAudio between tries because its device list is built once at import and never revisited. Devices travel as names, not indices, for the same reason.

`pyserial` is in `requirements.txt` but nothing in the project imports it.
