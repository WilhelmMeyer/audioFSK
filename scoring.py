"""Payload generation and alignment-aware scoring, shared by the test tools.

Pulled out of linktest.py so the offline bench scores a capture exactly the
way the live two-machine test scores the wire. If these drifted apart, an
improvement measured on the recordings would not mean the same thing on the
link -- which is the entire value of keeping recordings.

No audio, no serial: this is arithmetic over bytes, and both the live tool and
the offline one import it untouched.
"""

import difflib
import random


def make_payload(seed, n):
    """Deterministic from the seed, so both sides build it independently."""
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(n))


def find_payload_start(rx):
    """Cut the lead-in and preamble off at the 0xFF marker that ends them.

    A fixed offset will not do: everything ahead of the payload is 0x55 bytes,
    but how many depends on --lead and on how much of the lead-in the receiver
    actually caught. So find the run instead -- the longest stretch of
    {0x55, 0xFF} near the head -- and take the last 0xFF inside it. A random
    payload almost never produces four such bytes in a row, and leading garbage
    from a cold microphone is skipped rather than fatal.
    """
    head = rx[:96]
    best_run = best_marker = None
    i = 0
    while i < len(head):
        if head[i] not in (0x55, 0xFF):
            i += 1
            continue
        start, marker = i, None
        while i < len(head) and head[i] in (0x55, 0xFF):
            if head[i] == 0xFF:
                marker = i
            i += 1
        run = i - start
        if marker is not None and run >= 4 and (best_run is None or run > best_run):
            best_run, best_marker = run, marker
    return (best_marker + 1, True) if best_marker is not None else (0, False)


def score(expected, received):
    """Match with alignment, because bytes get dropped, not just corrupted.

    A dropped byte shifts everything after it, so an index-by-index compare
    would score a nearly perfect link as total garbage. SequenceMatcher
    tolerates insertions and deletions. autojunk must stay off: above 200
    elements it treats common byte values as noise and wrecks the alignment.
    """
    start, found = find_payload_start(received)
    payload_rx = received[start:]
    sm = difflib.SequenceMatcher(None, expected, payload_rx, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    return matched, payload_rx, found
