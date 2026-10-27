---
version: 1
slug: "visor-index-html"
primary_target: "visor/index.html"
related_targets: ["visor.py"]
---

Scope: visor/index.html served by visor.py, one per machine. Mode: Operate.
Audience: the bench operator at this machine. Task: start a session (role, text/file, data mode), watch the handshake phases, read what each direction heard, see the diary, read what arrived.

## Direction contract

THESIS: the radio's tuning dial is the frequency axis of the link; contracts, shadows, sounding margins, the 2-FSK pair and the live spectrum are all read off one glass scale, and the spectrogram falls beneath it as chart paper on that same axis. Refuses the grey dashboard of cards and sparklines.

OWN-WORLD: two finishes of one 1940s radio set, switched with P / ?projecao. Bench: black crackle-finish front panels (#232220 with a fine wrinkle texture), square corners (2px), slotted screws at panel corners, bone-white painted lettering over a khaki hairline (no plates), readouts in recessed dark windows with amber digits. Projection: the same set in faded light khaki (#cfc29a) with black stencil lettering, dark rules, readouts on cream, a dark nameplate stripe, larger type and heavier dial strokes, one 1280x720 / 1024x768 screen with no scroll. In both, the only light surfaces are the amber-lit dial glass and the paper (spectrogram, diary, received text). Rust (#a6532f) means what this station sends, steel blue (#4d6b8c) what reaches it, amber lamp glow means live. League Gothic lettering, Jost for UI text, Courier Prime only for numerals, the diary and contract tone lists. Text is minimal: explanations live in tooltips, a pilot lamp replaces a sentence wherever a state is binary.

STORY: the operator sees at a glance which phase the link is in, whether the station keeps up with real time, and where in frequency each direction was contracted; then reads the diary for why.

FIRST VIEWPORT: nameplate strip (station, role, phase, station clock); full-width dial with needle, bands and margin ticks; beneath it the waterfall on the same axis; right column phase lamps and drum counters; lower band the control form beside the teletype diary.

FORM: brief-pinned world (1940s radio set); concept roll not run because the user pinned the world and a pinned direction beats the roll (new-work.md §3). Seed key: none (pinned).

TOPOLOGY AS BUILT (cited): bench keeps the control form as a sticky left column, because Pausar / Finalizar / Parar já must stay reachable while the operator scrolls the diary during a session; phase lamps sit in the instrument band under the dial so the dial and spectrogram keep the full frequency-axis width; counters are inset wells in tabular Courier Prime, not drums. Projection is for a conference demo: the form shrinks to role switch + text + Iniciar + Parar já in the top-right, the handshake phases take the right column, the diary is hidden (the phases tell the story to an audience), level / counters / received text form the bottom row. The earlier review's material rebuild (flatten everything) was superseded by the user's own choice of the black crackle finish after seeing the green-enamel build.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
