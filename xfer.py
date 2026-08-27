"""File transfer over the acoustic link: packets, CRC, and resynchronisation.

Pure logic -- no serial, no audio, no files opened for us. The modem is a dumb
serial line with no error detection at all, and it does not merely corrupt
bytes, it drops them, which shifts everything after the loss. A byte lost in
the middle of an image is not a wrong pixel, it is every following pixel wrong.
So the payload has to be cut into packets that can each be checked and, when
bad, sent again.

CLAUDE.md puts framing, CRC and ARQ above the modem rather than inside it.
This is that layer. The retransmission policy lives above again, in whoever
drives the link, because only that caller knows about the serial channel the
acknowledgements travel on.
"""

LEAD = bytes([0x55] * 12)   # 8N1 makes this an unbroken bit alternation:
                            # wakes microphone AGC and gives timing recovery
                            # an edge on every symbol before the data starts.
SYNC = 0xFF
PAYLOAD_SIZE = 64
HEADER = 3                  # sync, seq, len
TRAILER = 2                 # crc16


def crc16(data):
    """CRC-16/CCITT-FALSE. Catches every single- and double-bit error and any
    odd number of bit errors, which is what this channel actually produces."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def crc32(data):
    """Whole-file check, so a transfer that passes every packet CRC and is
    still wrong cannot be mistaken for a success."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def split(data, size=PAYLOAD_SIZE):
    return [data[i:i + size] for i in range(0, len(data), size)]


def build(seq, payload):
    """One packet, ready to hand to the modulator."""
    if len(payload) > 255:
        raise ValueError("payload too long for a one-byte length field")
    body = bytes([seq & 0xFF, len(payload)]) + payload
    crc = crc16(body)
    return LEAD + bytes([SYNC]) + body + bytes([crc >> 8, crc & 0xFF])


def parse(stream, want_seq=None):
    """Find a valid packet anywhere in a received byte stream.

    Every 0xFF is a candidate start, because the lead-in is 0x55 bytes and a
    dropped byte can land the real one anywhere. The CRC decides: a candidate
    that checks out is a packet, and nothing else can plausibly be. That makes
    the parser indifferent to leading noise, trailing noise, and to how much of
    the lead-in survived.
    """
    for i, byte in enumerate(stream):
        if byte != SYNC:
            continue
        if i + HEADER > len(stream):
            break
        seq = stream[i + 1]
        length = stream[i + 2]
        end = i + HEADER + length + TRAILER
        if end > len(stream):
            continue
        body = stream[i + 1:i + HEADER + length]
        got = (stream[end - 2] << 8) | stream[end - 1]
        if crc16(body) != got:
            continue
        if want_seq is not None and seq != want_seq:
            continue
        return seq, bytes(stream[i + HEADER:i + HEADER + length])
    return None


def air_seconds(nbytes, baud=100, bits_per_byte=10):
    return nbytes * bits_per_byte / baud
