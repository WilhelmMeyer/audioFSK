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
# 0x33, not 0xFF. Framed 8N1 the marker is the one byte that cannot be
# scrambled -- the receiver has to recognise it to find anything at all -- so
# it must be the most robust byte in the packet, and 0xFF is the least: nine
# identical bits in a row, the exact pattern that starves timing recovery.
# Measured on the wire, the sync byte was dropped outright and the parser was
# left with no candidate to test. 0x33 frames as 0-1-1-0-0-1-1-0-0-1: never
# more than two identical bits together.
SYNC = 0x33
# 32, not something larger. There is no forward error correction here, so a
# single bad byte costs the whole packet, and the failure rate climbs with
# length: measured over a reverberant channel, 16-24 byte payloads recovered
# 91% of packets where 64-byte ones managed 50%. On the real link a ~45 byte
# transmission succeeded three times out of three while 81-byte packets failed
# four out of four. The cost is a fixed 17 bytes of framing per packet, so
# smaller still would spend more air on overhead than on the file.
PAYLOAD_SIZE = 32
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


def _keystream(n, _cache={}):
    """Fixed pseudorandom bytes, xorshift32 -- deterministic and identical on
    both machines without depending on any library's RNG staying stable.

    Position-keyed, not packet-keyed, deliberately: the receiver has to
    descramble the length field before it knows how long the packet is, so the
    stream cannot depend on anything carried inside it.
    """
    if n <= _cache.get('n', 0):
        return _cache['ks'][:n]
    x, out = 0x1F123BB5, bytearray()
    for _ in range(max(n, 512)):
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        out.append(x & 0xFF)
    _cache['n'], _cache['ks'] = len(out), bytes(out)
    return _cache['ks'][:n]


def _scramble(data):
    return bytes(b ^ k for b, k in zip(data, _keystream(len(data))))


def split(data, size=PAYLOAD_SIZE):
    return [data[i:i + size] for i in range(0, len(data), size)]


def build(seq, payload):
    """One packet, ready to hand to the modulator.

    Everything after the sync byte is scrambled, and that is not cosmetic.
    Timing recovery in the multi-tone demodulator is an early/late gate steered
    by decision contrast, so it learns the symbol clock from *transitions*.
    Framed 8N1, a 0x00 byte is nine identical bits in a row and teaches it
    nothing; a run of them makes it drift. Measured on this link, a BMP header
    lost 33 consecutive bytes -- almost all 0x00 -- in one stretch. Scrambling
    makes every payload look random, so the transitions are there whatever the
    file happens to contain.
    """
    if len(payload) > 255:
        raise ValueError("payload too long for a one-byte length field")
    body = bytes([seq & 0xFF, len(payload)]) + payload
    crc = crc16(body)
    return LEAD + bytes([SYNC]) + _scramble(body + bytes([crc >> 8, crc & 0xFF]))


def parse(stream, want_seq=None):
    """Find a valid packet anywhere in a received byte stream.

    Every 0xFF is a candidate start, because the lead-in is 0x55 bytes and a
    dropped byte can land the real one anywhere. The CRC decides: a candidate
    that checks out is a packet, and nothing else can plausibly be. That makes
    the parser indifferent to leading noise, trailing noise, and to how much of
    the lead-in survived.
    """
    ks = _keystream(256 + HEADER + TRAILER)
    for i, byte in enumerate(stream):
        if byte != SYNC:
            continue
        if i + HEADER > len(stream):
            break
        # Descramble positionally, so the length can be read before the rest
        # of the packet is even known to be there.
        seq = stream[i + 1] ^ ks[0]
        length = stream[i + 2] ^ ks[1]
        end = i + HEADER + length + TRAILER
        if end > len(stream):
            continue
        full = bytes(stream[i + 1 + k] ^ ks[k] for k in range(2 + length + TRAILER))
        body = full[:2 + length]
        got = (full[-2] << 8) | full[-1]
        if crc16(body) != got:
            continue
        if want_seq is not None and seq != want_seq:
            continue
        return seq, body[2:]
    return None


def air_seconds(nbytes, baud=100, bits_per_byte=10):
    return nbytes * bits_per_byte / baud
