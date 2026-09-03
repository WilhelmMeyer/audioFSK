"""On-disk format for captured audio, and the index over a directory of it.

A capture is two files sharing a stem: a `.wav` holding exactly what the
microphone delivered, and a `.json` holding what was transmitted and under
what conditions. The pair is the point -- audio without the payload it was
supposed to carry cannot score anything, and a score without the audio cannot
be re-examined when the next idea comes along.

Samples are stored as 32-bit float, the same dtype the demodulators consume,
so a capture goes back into the DSP bit-identical to what the live path saw.
16-bit would be inaudibly different and still a lie: the whole purpose here is
that the recording *is* the measurement.

No audio device and no serial port. This module is disk only, so the offline
bench runs on a machine with neither.
"""

import json
import struct
import time
from pathlib import Path

import numpy as np

FS = 48000


def _wav_bytes(samples, fs=FS):
    """Minimal 32-bit float mono WAV. `wave` in the stdlib cannot write these."""
    data = np.asarray(samples, dtype='<f4').tobytes()
    fmt = struct.pack('<HHIIHH', 3, 1, fs, fs * 4, 4, 32)   # IEEE float, mono
    chunks = (b'fmt ' + struct.pack('<I', len(fmt)) + fmt
              + b'data' + struct.pack('<I', len(data)) + data)
    return b'RIFF' + struct.pack('<I', 4 + len(chunks)) + b'WAVE' + chunks


def _read_wav(path):
    raw = Path(path).read_bytes()
    i = raw.find(b'data')
    if i < 0:
        raise ValueError(f"{path}: no data chunk")
    size = struct.unpack('<I', raw[i + 4:i + 8])[0]
    return np.frombuffer(raw[i + 8:i + 8 + size], dtype='<f4').astype(np.float64)


def save(directory, samples, payload, **meta):
    """Write one capture. Returns the stem both files share.

    The name carries the label and the timestamp, so a directory listing is
    already a readable log of what was tried and when.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    label = meta.get('label') or meta.get('mode') or 'capture'
    # A dot in the label is not a file extension. `with_suffix` cannot tell
    # the difference and silently ate one: a capture labelled `g0.4` was
    # written as `...-g0.wav`, so the gain it was recorded at -- the whole
    # point of the label -- vanished from the name, and `g0.4` and `g0.2`
    # collided. Build the names by concatenation instead.
    stem = directory / f"{stamp}-{label}"

    stem.with_name(stem.name + '.wav').write_bytes(
        _wav_bytes(samples, meta.get('fs', FS)))
    info = dict(meta)
    info.update(payload_hex=payload.hex(), payload_len=len(payload),
                samples=len(samples), recorded=stamp)
    stem.with_name(stem.name + '.json').write_text(json.dumps(info, indent=2) + "\n")
    return stem


def load(json_path):
    """One capture back as (samples, payload, meta)."""
    json_path = Path(json_path)
    meta = json.loads(json_path.read_text())
    payload = bytes.fromhex(meta['payload_hex'])
    wav = json_path.with_name(json_path.name[:-len('.json')] + '.wav')
    return _read_wav(wav), payload, meta


def load_all(directory):
    """Every capture in a directory, oldest first."""
    return [load(p) for p in sorted(Path(directory).glob('*.json'))]
