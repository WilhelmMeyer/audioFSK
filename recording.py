"""On-disk format for captured audio, and the index over a directory of it.

A capture is two files sharing a stem: a `.wav` holding exactly what the
microphone delivered, and a `.json` holding what was transmitted and under
what conditions. The pair is the point -- audio without the payload it was
supposed to carry cannot score anything, and a score without the audio cannot
be re-examined when the next idea comes along.

Samples are *written* as 32-bit float, the same dtype the demodulators
consume, so a capture goes back into the DSP bit-identical to what the live
path saw. Recording never depends on a codec: a capture that fails to save is
a lost measurement, and `_wav_bytes` is three lines of `struct` that cannot
fail for want of a library.

For the archive there is a second format, and which one is safe was measured
rather than assumed -- because the recording *is* the measurement, and a
storage format that changes it is not a smaller file but a different
experiment. Round-tripping the whole `resultados/` corpus (120 recordings
with a payload to score) through each:

    FLAC 24 bit   error <= 1 ULP of float32   0 blocks changed, bit accuracy
                                              identical in 113 of 120, and
                                              off by at most 0.55 pp in 2
    FLAC 16 bit   error ~ 1.5e-05             *loses a block* -- 08-MARY-GAIN
                                              goes from 11 of 12 to 10 of 12,
                                              8 of 12 decode different bits

So 24 bit is the archive format and 16 bit is not, and the reason 16 bit
fails is worth keeping: the SNR arithmetic says its quantisation sits 47 dB
below the quietest recording and is therefore harmless, and that argument is
wrong. A soft Viterbi at the edge of the rate-1/3 cliff needs only half a
quantisation step to send a block the other way. Re-measure before changing
this; do not reason about it.

`read` takes either format, preferring the `.wav` when both are present since
that one is exact. Writing FLAC needs `soundfile`; reading a `.wav` does not,
so a machine with neither codec nor library still scores a fresh capture.

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


def read_wav(path):
    raw = Path(path).read_bytes()
    i = raw.find(b'data')
    if i < 0:
        raise ValueError(f"{path}: no data chunk")
    size = struct.unpack('<I', raw[i + 4:i + 8])[0]
    return np.frombuffer(raw[i + 8:i + 8 + size], dtype='<f4').astype(np.float64)


# The name it had while this module was private. Kept because `channel.py`
# and the campaign scripts import it.
_read_wav = read_wav


def read_flac(path):
    """A FLAC capture back as float64, in the same scale `read_wav` returns."""
    import soundfile                      # optional: only the archive needs it
    samples, _ = soundfile.read(str(path), dtype='float64', always_2d=False)
    return np.asarray(samples, dtype=np.float64)


def write_flac(path, samples, fs=FS):
    """Archive a capture as 24-bit FLAC. See the module docstring for why 24."""
    import soundfile
    soundfile.write(str(path), np.asarray(samples, dtype=np.float64), fs,
                    format='FLAC', subtype='PCM_24')
    return Path(path)


def audio_path(stem):
    """The audio file belonging to `stem`, whichever format it is stored in.

    A clone of this repository carries the FLAC and not the WAV -- the WAV is
    233 MB against 107 MB and is `.gitignore`d -- while the machine that made
    the recording has both. Preferring the WAV means the bench reads the exact
    samples the microphone delivered whenever they are still on disk, and the
    archive otherwise. The two were measured to score the same (module
    docstring), which is what makes the fallback safe rather than a second
    ruler.
    """
    stem = Path(stem)
    for suffix in ('.wav', '.flac'):
        candidate = stem.with_name(stem.name + suffix)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{stem}: no .wav and no .flac")


def read(path):
    """One capture's audio, from a `.wav` or a `.flac`."""
    path = Path(path)
    return read_flac(path) if path.suffix == '.flac' else read_wav(path)


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
    return save_as(stem, samples, payload, recorded=stamp, **meta)


def save_as(stem, samples, payload, **meta):
    """Write one capture under a name the caller chose.

    `save` picks the name from the clock and the label; this one takes it, so
    a capture that arrives from the *other* machine over the serial cable can
    keep the name it was recorded under. A recording renamed in transit is a
    recording whose number can no longer be traced back to the machine and the
    moment that produced it, which is the whole reason the pair exists.
    """
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_name(stem.name + '.wav').write_bytes(
        _wav_bytes(samples, meta.get('fs', FS)))
    info = dict(meta)
    info.setdefault('recorded', time.strftime("%Y%m%d-%H%M%S"))
    info.update(payload_hex=payload.hex(), payload_len=len(payload),
                samples=len(samples))
    stem.with_name(stem.name + '.json').write_text(json.dumps(info, indent=2) + "\n")
    return stem


def as_int16(samples):
    """Samples as 16-bit PCM bytes, for the serial cable.

    On disk this project keeps 32-bit float, because a capture *is* the
    measurement and the demodulators consume floats. On the wire that is
    format rather than information: the samples came from an ADC of 16 bits or
    fewer, so the low half of every float carries nothing the microphone ever
    said. It halves a 2 MB capture, which at 115200 baud is the difference
    between three minutes and ninety seconds.
    """
    x = np.clip(np.asarray(samples, dtype=np.float64), -1.0, 1.0)
    return np.round(x * 32767.0).astype('<i2').tobytes()


def from_int16(blob):
    """The inverse. Exact for audio that was 16-bit to begin with."""
    return np.frombuffer(blob, dtype='<i2').astype(np.float64) / 32767.0


def load(json_path):
    """One capture back as (samples, payload, meta)."""
    json_path = Path(json_path)
    meta = json.loads(json_path.read_text())
    payload = bytes.fromhex(meta['payload_hex'])
    stem = json_path.with_name(json_path.name[:-len('.json')])
    return read(audio_path(stem)), payload, meta


def load_all(directory):
    """Every capture in a directory, oldest first."""
    return [load(p) for p in sorted(Path(directory).glob('*.json'))]
