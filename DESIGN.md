---
name: Visor do Enlace
description: One 1940s bench radio set in two finishes (black crackle bench, khaki projection) whose tuning dial is the frequency axis of an acoustic link.
colors:
  preto: "#232220"
  preto-fundo: "#1b1a18"
  preto-janela: "#161513"
  preto-borda: "#3a3732"
  osso: "#e8dfc8"
  osso-2: "#c9bfa6"
  caqui: "#a89a6e"
  caqui-escuro: "#6f6548"
  vidro: "#ece0bd"
  vidro-2: "#e2d3a8"
  papel: "#efe6cf"
  tinta: "#2e231b"
  tinta-2: "#5b4736"
  tinta-3: "#6a5844"
  envio: "#a6532f"
  envio-claro: "#d39a78"
  envio-botao: "#8a3b22"
  chega: "#4d6b8c"
  chega-claro: "#93abc4"
  chega-botao: "#3d5775"
  ambar: "#f1b24a"
  alarme: "#b8402a"
  olho: "#8fe0a2"
  projecao-preto: "#cfc29a"
  projecao-preto-fundo: "#b5a77b"
  projecao-preto-janela: "#efe7cf"
  projecao-preto-borda: "#5e5438"
  projecao-osso: "#15120d"
  projecao-osso-2: "#231f18"
  projecao-caqui: "#3f3725"
  projecao-envio-claro: "#7a2e14"
  projecao-chega-claro: "#1f3d63"
typography:
  placa:
    fontFamily: "League Gothic, Arial Narrow, sans-serif"
    fontSize: "36px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.14em"
  rotulo:
    fontFamily: "League Gothic, Arial Narrow, sans-serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.12em"
  legenda-campo:
    fontFamily: "League Gothic, Arial Narrow, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.1em"
  body:
    fontFamily: "Jost, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  nota:
    fontFamily: "Jost, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 500
    lineHeight: 1.35
  leitura:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tabular-nums"
  diario:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: "21px"
rounded:
  r: "2px"
  lampada: "50%"
spacing:
  gutter: "16px"
  gap: "12px"
  chapa-pad: "16px 18px 18px"
  comando-w: "340px"
components:
  chapa:
    backgroundColor: "{colors.preto}"
    textColor: "{colors.osso}"
    rounded: "{rounded.r}"
    padding: "16px 18px 18px"
  janela:
    backgroundColor: "{colors.preto-janela}"
    padding: "12px 14px"
  leitura-output:
    backgroundColor: "#0b0a09"
    textColor: "{colors.ambar}"
    typography: "{typography.leitura}"
    padding: "5px 7px"
  botao:
    backgroundColor: "#0d0c0b"
    textColor: "{colors.osso}"
    rounded: "{rounded.r}"
    padding: "11px 14px 10px"
  botao-principal-chamador:
    backgroundColor: "{colors.envio-botao}"
    textColor: "#fff4e4"
    rounded: "{rounded.r}"
    padding: "15px"
  botao-principal-ouvinte:
    backgroundColor: "{colors.chega-botao}"
    textColor: "#f1f5fb"
    rounded: "{rounded.r}"
    padding: "15px"
  botao-alarme:
    backgroundColor: "#8f2e1d"
    textColor: "#fff1e6"
    rounded: "{rounded.r}"
  campo:
    backgroundColor: "{colors.preto-janela}"
    textColor: "{colors.osso}"
    rounded: "0"
    padding: "8px 10px"
  fita:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.diario}"
    padding: "8px 12px"
---

# Design System: Visor do Enlace

## Overview

**Creative North Star: "The Bench Receiver"**

One 1940s radio set, drawn in two finishes. The tuning dial is the frequency axis of the acoustic link: contracts, shadows, sounding margins, the 2-FSK pair and the live spectrum are all read off one glass scale, and the spectrogram falls beneath it as chart paper on the same axis. Everything else is the front panel around that glass.

Panels are black crackle-finish metal with a fine wrinkle texture, square 2px corners, a slotted screw in each corner, and painted bone-white lettering over a khaki hairline, with no nameplates behind the headings. Readouts sit in recessed dark windows with amber digits. The only light surfaces are the amber-lit dial glass and the paper (spectrogram, diary, received text). Text is minimal: explanations live in tooltips, and a pilot lamp replaces a sentence wherever a state is binary.

**Key Characteristics:**
- Two finishes of one object: bench (default) and projection (conference demo, one screen, no scroll).
- Rust means what this station sends; steel blue means what reaches it; amber glow means live.
- Depth comes from recessed windows and a lit glass, not from card shadows.
- Three type voices with fixed jobs: League Gothic engraves, Jost explains, Courier Prime counts.

## Colors

Warm black and bone with khaki trim, two semantic hues, and amber as the only light. The `:root` tokens are the bench finish; `.projecao` overrides them on `<html>`.

### Primary
- **Rust, what we send** (`envio` #a6532f; light `envio-claro` #d39a78; key `envio-botao` #8a3b22): the caller role, the outbound contract band on the dial, the sent-bytes bar.
- **Steel, what reaches us** (`chega` #4d6b8c; light `chega-claro` #93abc4; key `chega-botao` #3d5775): the listener role, the inbound contract band, margin ticks, the received-bytes bar.

### Secondary
- **Lamp Amber** (`ambar` #f1b24a): live state only: lit pilot lamps, readout digits, the spectrum trace, the current phase wash, focus ring, pressed toggle.
- **Alarm Red** (`alarme` #b8402a): out-of-range readouts, error line, Parar já and Matar processo keys.
- **Magic Eye Green** (`olho` #8fe0a2): the visor-responds lamp and the level eye.

### Neutral
- **Crackle Black** (`preto` #232220, `preto-fundo` #1b1a18, `preto-janela` #161513, `preto-borda` #3a3732): panel, page ground, recessed window, panel edge. Panels use `preto` under the `--craquelado` turbulence texture.
- **Bone** (`osso` #e8dfc8, `osso-2` #c9bfa6): painted lettering and secondary text.
- **Khaki** (`caqui` #a89a6e, `caqui-escuro` #6f6548): hairlines, notes, hover borders, scrollbars.
- **Dial Glass** (`vidro` #ece0bd, `vidro-2` #e2d3a8) and **Chart Paper** (`papel` #efe6cf) with ink `tinta` #2e231b, `tinta-2` #5b4736, `tinta-3` #6a5844: the light surfaces.

### Projection finish (`.projecao`, applies when key P, the Projeção button, or `?projecao` turns it on; persisted in localStorage `visor-projecao`)
Same roles, re-valued: panel `projecao-preto` #cfc29a (page ground #b5a77b), window #efe7cf, edge #5e5438; lettering becomes black stencil (`osso` #15120d, `osso-2` #231f18); khaki becomes dark (`caqui` #3f3725, `caqui-escuro` #5e5438); the role text colors darken to #7a2e14 (send) and #1f3d63 (receive); the crackle texture drops to 6% opacity. Readouts sit on cream (#f7f1df) in dark ink instead of amber on black. The nameplate stays dark (#1f1c17) with cream lettering. Amber, glass and paper are unchanged.

### Named Rules
**The Two Roles Rule.** Rust is only ever what this station sends; steel is only ever what arrives. Never use either as decoration or as a generic accent.
**The Only Light Rule.** Only the dial glass, the paper surfaces and lit lamps are light on the bench finish. A new light surface needs a physical reason (it is a lamp or a sheet of paper).
**The Lamp Means Live Rule.** Amber glow marks a live state. A lit lamp that is not carrying state is wrong.

## Typography

**Display Font:** League Gothic (with Arial Narrow)
**Body Font:** Jost (with system-ui)
**Label/Mono Font:** Courier Prime (with Courier New), numerals only plus the diary and contract tone lists

**Character:** Condensed painted lettering for everything engraved on the set, a quiet geometric sans for the sentences, and a typewriter face where something is counted or typed out. Fonts are self-hosted in `visor/fontes/`.

### Hierarchy
- **Nameplate** (League Gothic 400, 36px, 1, tracking .14em, uppercase): the page title only.
- **Rótulo** (League Gothic 400, 20px, 1, .12em, uppercase; 22px in projection): panel headings over a khaki hairline.
- **Field legend** (League Gothic 400, 16px, .1em, uppercase): form labels; keys use 18-24px.
- **Body** (Jost 400, 15px, 1.45): UI text. Notes and tooltips-in-view 12.5-13px, weight 500.
- **Readout** (Courier Prime 700, 15-17px, tabular-nums): counters, levels, the needle frequency.
- **Diary** (Courier Prime 400, 13px on a 21px baseline): teletype lines with a 7.5ch hanging indent.

### Named Rules
**The Three Voices Rule.** League Gothic engraves labels, Jost speaks, Courier Prime counts. Do not set sentences in League Gothic or labels in Courier.

## Layout

A single chassis grid, max 1680px, 16px gutter, 12px gaps. Bench: a sticky 340px control column at left (Pausar, Finalizar and Parar já stay reachable while the diary scrolls); the right column stacks the dial, the waterfall on the same axis (both keep a 46px right gutter for the time and unit ticks), the instrument band (level, handshake lamps, counters in three columns) and the diary beside "O que chegou". Below 1180px the grid collapses to one column; below 720px instruments and registro go single-column.

Projection: one 100vh screen, no scroll. Three equal columns plus a 260-330px right column: the dial and waterfall span three columns, the reduced form (role switch, text, Iniciar, Parar já) tops the right column over the handshake phases, and level, counters and received text form the bottom row. Elements marked `so-bancada` (file, mode, timings, peak, waveform, some counters) and the diary are hidden. Type is larger and weightier, dial strokes are 2px, the needle 3px.

### Phone (`android/app/src/main/assets/tela/index.html`)
The same set, bench finish, in one column at about 412px, in a WebView with the tokens and `visor/fontes` of the PC screen: dial, handshake lamps in a row, instruments (magic eye, readouts, sent count with bar, received count with a bar only when the file states its own size), role switch and text, "O que chegou", diary. The main key is fixed at the bottom. While a session runs it becomes dark red and must be held for 0.9 s to stop, so a stray touch cannot end a session of minutes. The waterfall falls under the dial on the same axis, in rust while this station transmits and steel while it listens. Received bytes appear as they arrive: text, or a rolling hex tape, and a BMP opens from its first packet with the rest padded, so the picture rises line by line. No projection finish.

### Percurso (both screens)
The session's path, one vertical line with one lamp per stage (green done, amber blinking now, off to come, red failed): done stages carry one line of values, and the current one adds a single arrow, sending in rust or listening in steel, with the seconds left. No protocol term (signal names, rep, sounding) on the main screen: those live only in the diary. It comes ready from the station (`percurso()` in `enlace2` and `enlace_manual`), the screens only draw it. Rust and steel keep their roles on the values; the chosen speed is an amber tag inside its value; a value never measured is a dash, and a change reads "100 → 33 baud", never overwrites.

## Elevation & Depth

Flat and material. Panels carry one soft drop (`0 4px 12px -4px rgba(0,0,0,.6)`); depth is mostly inset: readout windows and fields are recessed (`--funda: inset 0 1px 3px rgba(0,0,0,.6)`), the dial sits in a dark metal rim, and lamps sit behind a double ring. Keys have a small drop that flattens on press (`0 2px 5px` to `0 1px 2px`, with a 1px move). The dial glass warms with a sepia/brightness filter only while a session is on air.

### Named Rules
**The Recess Rule.** Readings go into recessed dark windows; nothing floats on a card.

## Shapes

Square. One radius (`--r` 2px) on panels and keys; inputs have 0 radius. The only round forms are lamps (14px bulb, double ring), the magic-eye level indicator and the corner screws (10px slotted SVG, one per panel corner). Structure is drawn with 1px khaki hairlines, not boxes.

## Components

### Chapa (panel)
Crackle black with 1px edge, 2px corners, four corner screws, 16/18px padding. The module base for every group.

### Rótulo
Painted League Gothic heading over a khaki hairline, optional small Jost note and a right-aligned pilot (registrador, ao vivo).

### Mostrador (signature)
Amber-lit glass in a dark rim, SVG scale 400-4600 Hz with 25 grid tones (562.5 + 162.5k), rust and steel contract bands, margin ticks (red below 12 dB), live spectrum trace in amber, and a dark-red needle (#8e2414) with a frequency tag. The cascata (waterfall) below is on paper with the same horizontal axis and a time scale in Courier at the right.

### Lâmpada piloto
14px bulb behind a ring. Off is #3b3630; `.acesa` amber, `.verde` green, `.alarme` red, each with glow; `.pisca` pulses at 1.1s. Replaces a sentence for any binary state.

### Janela and leituras
Dark recessed window; each reading is a Courier `output` in an even darker well with amber digits, right-aligned, red fill when `.mal`. Counters add a 4px bar (rust sent, light steel received).

### Fases (handshake)
List of lamp + League Gothic phase name + Jost note. `.agora` gets a 12% amber wash; `.feita` brightens to bone.

### Botões
Dark key, khaki edge, League Gothic legend. `.principal` fills with the role colour (rust for chamador, steel for ouvinte). `.alarme` is red. `.mini` is a toggle that turns amber when pressed. Hover lifts border to khaki; disabled is 40% (projection: dashed outline, no fill).

### Chave (role switch) and campos
Two-position switch in a dark tray; the checked side takes its role colour. Fields are recessed dark with khaki border and amber caret; focus is a 2px amber outline.

### Fita (diary) and O que chegou
Paper with faint ruled lines, Courier ink; event classes use dark ink hues (alert #8c2d16, open #23426a, contract #3b2a1c, local #4f5a2e).

### Motion
Needle slides 250ms with a soft ease; lamps blink; bars ease 400ms; everything stops under `prefers-reduced-motion`.

## Do's and Don'ts

### Do:
- **Do** put any frequency-keyed information on the dial's axis (400-4600 Hz) so it lines up with the waterfall below.
- **Do** keep square corners (2px) and a screw in each panel corner.
- **Do** use a pilot lamp rather than a sentence for a binary state; put explanation in a tooltip.
- **Do** define new colours as tokens that `.projecao` can override, and check both finishes.
- **Do** keep every projection-visible element legible at 1280x720 and 1024x768 without scrolling.

### Don't:
- **Don't** use grey cards, sparklines or soft rounded dashboard widgets.
- **Don't** put rust or steel on anything other than sent or received.
- **Don't** add a light surface that is not glass, paper or a lamp.
- **Don't** put the diary or the bench-only controls (`so-bancada`) in the projection layout.
- **Don't** use Courier Prime for prose or League Gothic for sentences.
