"""One folder per test, assembled from recordings that already exist.

`study.py` runs a campaign: it drives the room, records, and scores. This tool
does only the second half, and that separation is the point. A recording made
last week, by another script or on the other machine, is still a fixed channel
-- and the decoder that reads it changes weekly. So the question "what does
today's code make of yesterday's audio" has to be answerable without booking
the room again, and its answer has to be filed somewhere a reader can check.

What it leaves behind is one directory per test:

    resultados/<NOME-TESTE>/
        HEADER.md            commit, date, bench, settings read off the meta
        gravacao/            the wav + json pair, copied, names preserved
        llr/<stem>.csv       the demodulator's soft output, one row per symbol
        bits/<stem>.txt      bits read against bits transmitted
        figuras/<stem>.png   the spectrogram, drawn by spectro.py
        resultado.csv        one row per recording

The header opens with the commit, for the reason `study.py` gives: a bit
accuracy is a statement about a decoder as much as about a channel, and a
percentage with no commit beside it cannot be reproduced or contradicted.

Two decisions are worth stating because both were made the other way first,
elsewhere in this project, and both were wrong there:

*One ruler.* Bit accuracy is taken at the best brute-forced slide, always --
never where `find_sync` happened to land. Mixing the two makes the failures
score higher than the successes, because the best slide is chosen to flatter
and the sync position is not. `bloco_ok` stays as the separate honest number
and goes through the real FEC path, sync word and Viterbi and CRC, because an
approximation of it would be a different quantity wearing the same name.

*The receiver's sync, not the gate's.* A recording made with the two sync
sweeps (`sync_chirp`) is read through `modem.sweep_soft`, the function the
live receiver calls, and the gate's reading stays beside it in the `_gate`
columns. Without this the gate takes the sweep for the first preamble symbols
and the folder reports the hazard the sweeps create, not the benefit.

*Four values per symbol.* `MaryDemodulator.demodulate_soft` returns one
log-likelihood per *bit*, so four per symbol. Reading that array's length as a
symbol count makes a normal burst look six times longer than it is.

Disk only, like `recording.py` and `align.py`: no audio device, no serial port,
no threads. `spectro.py` is invoked as a subprocess rather than imported, so a
broken figure costs the figure and not the collection.

    ./venv/bin/python resultado.py 07-MARY-BASE captures-self/*.json \\
        --bancada "Bluetooth + Mic1" --note "linha de base antes do ganho"
"""

import argparse
import csv
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import fec
import recording
from modem import (MARY_BITS, MaryDemodulator, MFSKDemodulator, MFSK_PAIRS,
                   TONE_LAYERS, chirp, sweep_soft, tone_layer)

BLOCK = 2048          # what the live path hands the demodulator at a time
PY = sys.executable
ROW = 64              # bits per line in bits/<stem>.txt


def git_commit():
    """The commit the code was at, dirty flag included.

    Duplicated from `study.py` rather than imported: that module pulls in
    `selfcapture`'s neighbourhood through `spectro` and `align`, and this tool
    must stay importable on a machine with no audio stack at all. Six lines is
    a cheaper price than the dependency.
    """
    try:
        head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                              capture_output=True, text=True, check=True)
        dirty = subprocess.run(['git', 'status', '--porcelain'],
                               capture_output=True, text=True, check=True)
        return head.stdout.strip() + ('-dirty' if dirty.stdout.strip() else '')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'desconhecido'


def demodulator(meta, **kw):
    """The receiver the recording's own metadata calls for.

    `kw` (steer, skip, period) reaches only the tone layers: it is how the
    sweep reading builds a frozen-clock receiver through the same factory.
    """
    if meta['mode'] == 'mary':
        return MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                               gap=meta.get('gap', 0.0),
                               band=meta.get('band', 0.0),
                               chord=meta.get('chord', False),
                               ifk=bool(meta.get('ifk')), **kw)
    if meta['mode'] in TONE_LAYERS:
        # Any other tone layer (2-FSK): its own alphabet, never IFK or chord.
        return MaryDemodulator(fs=meta['fs'], baud=meta['baud'],
                               gap=meta.get('gap', 0.0),
                               band=meta.get('band', 0.0),
                               **tone_layer(meta['mode']), **kw)
    return MFSKDemodulator(fs=meta['fs'], baud=meta['baud'],
                           parallel=meta.get('parallel', False),
                           grouped=meta.get('grouped', False))


def soft(demod, samples):
    """Feed a capture through in blocks, as the live path would.

    Block by block and not in one call, because both demodulators carry filter
    and timing state across calls; handing them the whole recording at once
    would exercise a code path the link never runs.
    """
    parts = [demod.demodulate_soft(samples[i:i + BLOCK])
             for i in range(0, len(samples), BLOCK)]
    parts = [p for p in parts if len(p)]
    return np.concatenate(parts) if parts else np.zeros(0)


def symbol_bits(meta):
    """How many log-likelihoods one symbol contributes to the soft stream."""
    if meta['mode'] in TONE_LAYERS:
        return TONE_LAYERS[meta['mode']][1]
    return len(MFSK_PAIRS) if meta.get('parallel') else 1


def frame_bits(payload, meta):
    """The sync word plus the coded block, as the transmitter sent them."""
    rep = meta.get('fec_repeat', 1)
    if meta.get('parallel'):
        return np.asarray(fec.frame_parallel(payload, len(MFSK_PAIRS),
                                             repeat=rep), dtype=np.int8)
    return np.asarray(fec.frame(payload, repeat=rep), dtype=np.int8)


def preamble(meta):
    """The alternating run ahead of the frame, exactly as the sender built it.

    Reconstructed from `fec.preamble_bits`, the same function the transmitter
    calls, in the spirit of `spectro.tx_tone_indices`: the intended signal is
    fully known from the payload the capture stored, so the "expected" column
    is the real transmitted sequence rather than an illustration of one.
    """
    if meta['mode'] in TONE_LAYERS:
        return np.asarray(fec.preamble_bits('mary',
                                            symbol_bits=TONE_LAYERS[meta['mode']][1]),
                          dtype=np.int8)
    return np.asarray(fec.preamble_bits('mfsk', npairs=len(MFSK_PAIRS),
                                        parallel=bool(meta.get('parallel'))),
                      dtype=np.int8)


def swept(meta, payload):
    """Whether this recording carries the two sync sweeps the receiver reads."""
    return bool(meta.get('sync_chirp') and meta['mode'] in TONE_LAYERS
                and meta.get('kind') == 'fec' and payload)


def sweep_llr(samples, payload, meta):
    """The soft stream as the live receiver reads a swept frame.

    Same function `console.AudioNode._sweep_llr` calls -- `modem.sweep_soft`,
    with the span from `fec.sweep_span` -- so the number here is the one the
    link would have produced, not a reimplementation of it. The span is
    computed from the payload length as the receiver computes it, never read
    from `sync_span_symbols` in the JSON: a recorder once stamped that number
    with the rounding the other way, and the receiver never sees the stamp.
    Returns (llr, how, period, span); llr is None when no sweep was found.
    """
    fs, baud = meta['fs'], meta['baud']
    sps = fs / baud
    hush = int(meta.get('sync_hush', 0.0) * fs)
    span = fec.sweep_span(len(payload), meta.get('fec_repeat', 1) or 1,
                          symbol_bits(meta), hush, sps)
    llr, _, period, how = sweep_soft(
        samples, lambda **kw: demodulator(meta, **kw), span, hush, sps,
        block=BLOCK, template=chirp(fs))
    return llr, how, period, span


# What `sincronismo` says, per outcome of `modem.sweep_soft`.
SYNC_NAME = {'pair': 'duas varreduras', 'lead': 'uma varredura',
             None: 'gate (varredura nao encontrada)'}


def best_slide(llr, want):
    """Where the transmitted frame agrees best with what was read.

    Returns (offset, accuracy) or (None, None) when the recording is shorter
    than the frame. Correlating signs is the same arithmetic as
    `align.bit_accuracy`, deliberately: a normalised correlation of +-1 bits
    is 2*accuracy - 1, and every trustworthy number in this project's notes
    was read off this ruler.
    """
    llr = np.asarray(llr, dtype=np.float64)
    if len(llr) < len(want) or not len(want):
        return None, None
    scores = np.correlate(np.sign(llr), 2.0 * want - 1.0, mode='valid') / len(want)
    if not len(scores):
        return None, None
    at = int(np.argmax(scores))
    return at, float(0.5 * (scores[at] + 1.0))


def decodes(llr, payload, meta):
    """The real FEC path: correlate the sync word, Viterbi, compare bytes.

    Not an approximation of it. `bloco_ok` is the one number here that says
    what the link actually delivered, so it has to be produced by the code the
    link runs -- including the sync search, which is the only mechanism in the
    project that solves bit alignment.
    """
    rep = meta.get('fec_repeat', 1)
    if llr is None or not len(llr):
        return False
    # An empty payload decodes to an empty block, and `b'' == b''` is True: a
    # recording of a silent room, with nothing transmitted into it, scored as a
    # block delivered whole. This project already knows the shape of that
    # mistake -- a vote is a ratio, so five tones of noise still elect a bit --
    # and it belongs in the scorer as much as in the demodulator. There is
    # nothing to deliver, so nothing was delivered.
    if not payload:
        return False
    if meta.get('parallel'):
        npairs = len(MFSK_PAIRS)
        start = fec.find_sync_parallel(llr, npairs)
        if start is None:
            return False
        got = fec.decode_parallel(llr[start:], len(payload), npairs, repeat=rep)
    else:
        start = fec.find_sync(llr)
        if start is None:
            return False
        got = fec.decode(llr[start:], len(payload), repeat=rep)
    return got == payload


def write_llr(path, llr, per_symbol):
    """The soft stream as a table, one row per symbol.

    The reshape is the whole reason this file exists in the results folder: in
    M-ary the array is four values per symbol, and anyone reading it as one
    per symbol gets a burst four times too long and misreads every timing
    number that follows.
    """
    llr = np.asarray(llr, dtype=np.float64)
    nsym = len(llr) // per_symbol
    body = llr[:nsym * per_symbol].reshape(nsym, per_symbol)
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['simbolo'] + [f'llr{j}' for j in range(per_symbol)])
        for i, row in enumerate(body):
            w.writerow([i] + [f"{v:.4f}" for v in row])
    return nsym


def write_bits(path, llr, want, at, meta, stem, ruler=None):
    """Bits read against bits transmitted, aligned at the best slide.

    `at` is where the *frame* agrees best, so the preamble is drawn ahead of
    it and may run off the front of the recording -- the receiver rarely
    catches the whole lead-in. Missing positions are printed as `.`, which is
    an absence of evidence and not a wrong bit, and they are excluded from the
    difference row for the same reason.
    """
    llr = np.asarray(llr, dtype=np.float64)
    pre = preamble(meta)
    start = at - len(pre)
    got = []
    for i in range(start, start + len(pre) + len(want)):
        got.append('.' if i < 0 or i >= len(llr) else ('1' if llr[i] > 0 else '0'))
    exp = ''.join(str(int(b)) for b in np.concatenate([pre, want]))
    got = ''.join(got)
    lines = [
        f"# {stem}",
        f"# modo {meta['mode']}, fec_repeat {meta.get('fec_repeat')}, "
        f"{len(pre)} bits de preambulo + {len(want)} bits de quadro",
        f"# alinhado no melhor deslizamento: quadro comeca no bit {at} do fluxo",
    ] + ([f"# lido com: {ruler}"] if ruler else []) + [
        "# esp = transmitido, lid = lido, ^ = diferenca, . = fora da gravacao",
        "",
    ]
    for i in range(0, len(exp), ROW):
        e, g = exp[i:i + ROW], got[i:i + ROW]
        mark = ''.join('^' if b != a and b != '.' else ' ' for a, b in zip(e, g))
        lines += [f"{i:6d} esp {e}", f"       lid {g}", f"           {mark}", ""]
    Path(path).write_text("\n".join(lines), encoding='utf-8')


def figura(json_path, out_png):
    """Draw the spectrogram with spectro.py. Returns None, or the error text.

    A subprocess, not an import: this tool's job is to collect numbers, and a
    figure that fails -- a missing option, a module mid-edit -- must cost the
    figure alone. The failure is recorded in the header instead of being
    swallowed, because a results folder silently missing a picture invites the
    conclusion that the recording was bad.
    """
    cmd = [PY, 'spectro.py', str(json_path), '--fundido', '--win', '480',
           '-o', str(out_png)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as e:
        return f"{' '.join(cmd)}: {e}"
    if r.returncode != 0 or not Path(out_png).exists():
        tail = (r.stderr or r.stdout or '').strip().splitlines()
        return f"codigo {r.returncode}: " + (tail[-1] if tail else "sem saida")
    return None


def score_one(json_path, run):
    """Everything one recording yields, plus its three per-recording files."""
    samples, payload, meta = recording.load(json_path)
    samples = np.asarray(samples, dtype=np.float64)
    stem = Path(json_path).name[:-len('.json')]

    # `.flac` as well as `.wav`: a clone carries only the archived format, and
    # a campaign assembled there must still end up holding its own audio.
    # Copying neither would leave a folder whose numbers cannot be rechecked,
    # which is the one thing `resultados/` exists to prevent.
    for suffix in ('.json', '.wav', '.flac'):
        src = Path(json_path).with_name(stem + suffix)
        if src.exists():
            shutil.copy2(src, run / 'gravacao' / src.name)

    llr = soft(demodulator(meta), samples)
    want = frame_bits(payload, meta)
    # A swept recording is read the way the receiver reads it: the sweeps
    # give the start and the clock. The gate's reading is kept beside it,
    # computed exactly as before, so old and new can be compared row by row.
    sweep = None
    if swept(meta, payload):
        gate_llr = llr
        s_llr, how, period, span = sweep_llr(samples, payload, meta)
        if s_llr is not None:
            llr = s_llr
        sweep = (gate_llr, how, period, span)
    at, acc = best_slide(llr, want)
    # A capture with no payload -- a noise floor, a tone, a sweep -- has no bit
    # accuracy to report. Without this the sync word alone is the whole of
    # `want`, and correlating 31 bits against noise returned 71-78% for four
    # recordings of a silent room. A number that high, printed beside a real
    # one, is worse than no number.
    if not payload:
        at, acc = None, None
    nsym = write_llr(run / 'llr' / f'{stem}.csv', llr, symbol_bits(meta))
    if at is not None:
        write_bits(run / 'bits' / f'{stem}.txt', llr, want, at, meta, stem,
                   ruler=SYNC_NAME[sweep[1]] if sweep else None)
    err = figura(run / 'gravacao' / f'{stem}.json', run / 'figuras' / f'{stem}.png')

    row = {
        'stem': stem,
        'modo': meta['mode'],
        'baud': meta.get('baud'),
        'gain': meta.get('gain'),
        'fec_repeat': meta.get('fec_repeat'),
        'bytes': len(payload),
        'acerto_bits': None if acc is None else round(100 * acc, 2),
        'bloco_ok': int(decodes(llr, payload, meta)) if payload else None,
        # Measured off the samples, not copied from the metadata: the level
        # that matters is the one in the file being scored.
        'pico_rx': round(float(np.max(np.abs(samples))) if len(samples) else 0.0, 4),
        'rms_rx': round(float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0, 4),
    }
    if sweep is not None:
        # Only swept rows carry these keys, so a folder with no sweeps writes
        # exactly the csv it wrote before they existed.
        gate_llr, how, period, span = sweep
        _, gacc = best_slide(gate_llr, want)
        stamped = meta.get('sync_span_symbols')
        row.update({
            'sincronismo': SYNC_NAME[how],
            'periodo': None if period is None else round(period, 3),
            'span_simbolos': round(span, 3),
            'span_json': None if stamped is None else round(float(stamped), 3),
            'acerto_bits_gate': None if gacc is None else round(100 * gacc, 2),
            'bloco_ok_gate': int(decodes(gate_llr, payload, meta)),
        })
    return row, meta, nsym, err


def header(path, name, rows, metas, args, commit, errors):
    """The file someone writing this up reads first."""
    m = metas[0] if metas else {}
    ok = [r for r in rows if r['acerto_bits'] is not None]
    # Recordings with no payload -- floor, tone, sweep -- are collected and
    # filed, but they are not blocks and must not appear in the denominator.
    scored = [r for r in rows if r['bloco_ok'] is not None]
    lines = [
        f"# {name}",
        "",
        f"- **Codigo:** commit `{commit}`",
        f"- **Quando:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Bancada:** {args.bancada or 'nao informada'}",
        f"- **Camada:** {m.get('mode', '?')}"
        + (f", FEC rate 1/3 x{m.get('fec_repeat')}" if m.get('kind') == 'fec'
           else ", sem FEC"),
        f"- **Amostragem:** {m.get('fs', '?')} Hz, {m.get('baud', '?')} baud",
        f"- **Ganho de transmissao:** {m.get('gain', '?')}",
        f"- **Bloco:** {rows[0]['bytes'] if rows else '?'} bytes de payload",
        f"- **Canal:** {'auto-captura' if m.get('self_capture') else 'duas maquinas'}"
        + (f", enlace `{m['link']}`" if m.get('link') else ""),
        f"- **Entrada / saida:** `{m.get('in_device', '?')}` / `{m.get('out_device', '?')}`",
        f"- **Trials:** {len(rows)} gravacoes",
    ]
    if args.note:
        lines += ["", args.note]
    sw = [r for r in rows if 'sincronismo' in r]
    pct = lambda v: '--' if v is None else f"{v:.2f}%"
    okn = lambda v: '--' if v is None else ('OK' if v else 'nao')
    if sw:
        lines += ["", "## Resultado", "",
                  "| gravacao | ganho | rep | bytes | sincronismo | bits | bloco "
                  "| bits gate | bloco gate | pico | rms |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            lines.append(
                f"| `{r['stem']}` | {r['gain']} | {r['fec_repeat']} | {r['bytes']} "
                f"| {r.get('sincronismo', 'gate')} | {pct(r['acerto_bits'])} "
                f"| {okn(r['bloco_ok'])} | {pct(r.get('acerto_bits_gate'))} "
                f"| {okn(r.get('bloco_ok_gate'))} | {r['pico_rx']:.2f} | {r['rms_rx']:.3f} |")
    else:
        lines += ["", "## Resultado", "",
                  "| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            bits = '--' if r['acerto_bits'] is None else f"{r['acerto_bits']:.2f}%"
            lines.append(
                f"| `{r['stem']}` | {r['gain']} | {r['fec_repeat']} | {r['bytes']} "
                f"| {bits} | {'--' if r['bloco_ok'] is None else ('OK' if r['bloco_ok'] else 'nao')} "
                f"| {r['pico_rx']:.2f} | {r['rms_rx']:.3f} |")
    if ok and scored:
        lines += ["",
                  f"Media de bits certos: {np.mean([r['acerto_bits'] for r in ok]):.2f}%. "
                  f"Blocos inteiros: {sum(r['bloco_ok'] for r in scored)} de {len(scored)}."]
        if sw:
            g_ok = [r for r in sw if r['acerto_bits_gate'] is not None]
            lines += [f"So o gate, nas {len(sw)} gravacoes com varredura: "
                      + (f"{np.mean([r['acerto_bits_gate'] for r in g_ok]):.2f}% de bits, "
                         if g_ok else "")
                      + f"{sum(r['bloco_ok_gate'] for r in sw)} de {len(sw)} blocos."]
    lines += [
        "",
        "## Como ler",
        "",
        "`acerto_bits` e medido no melhor deslizamento por forca bruta, sempre,",
        "e nunca na posicao que o `find_sync` escolheu -- misturar as duas reguas",
        "faz as falhas pontuarem mais alto que os acertos. `bloco_ok` e o numero",
        "honesto separado: passa pelo caminho FEC de verdade (sync por correlacao,",
        "Viterbi soft, comparacao dos bytes) e e o que o enlace de fato entregou.",
        "Com poucas gravacoes ele e ruidoso; nao ajuste parametro por ele.",
        "",
    ]
    if sw:
        lines += [
            "**Duas reguas de sincronismo.** Nas gravacoes com `sync_chirp`,",
            "`acerto_bits` e `bloco_ok` saem do audio relido como o receptor ao",
            "vivo o rele (`modem.sweep_soft`, o mesmo de `console.py`): relogio",
            "congelado, inicio na varredura de abertura e periodo medido entre as",
            "duas (`sincronismo` = duas varreduras). Se o par nao serve, so a de",
            "abertura com relogio nominal (uma varredura); se nenhuma aparece, o",
            "gate, e a coluna diz. `acerto_bits_gate` e `bloco_ok_gate` sao a",
            "leitura pelo gate early/late, como esta ferramenta fazia antes --",
            "pessimista nessas gravacoes, porque o gate toma a varredura pelos",
            "primeiros simbolos do preambulo. Gravacoes sem varredura so tem a",
            "regua do gate, nas colunas sem sufixo. `span_simbolos` e o vao entre",
            "as varreduras calculado como o receptor calcula (`fec.sweep_span`);",
            "`span_json` e o que o gravador carimbou, so para conferencia.",
            "`llr/` e `bits/` saem da regua principal.",
            "",
        ]
    lines += [
        "`llr/*.csv` tem uma linha por simbolo. Em M-aria sao quatro colunas,",
        "porque sao quatro bits por simbolo: o tamanho do vetor soft nao e uma",
        "contagem de simbolos.",
        "",
        "## Arquivos",
        "",
        "- `gravacao/` -- wav 32-bit float + json, formato de `recording.py`",
        "- `llr/` -- saida soft do demodulador, uma linha por simbolo",
        "- `bits/` -- bits lidos contra bits transmitidos, alinhados",
        "- `figuras/` -- espectrograma por gravacao",
        "- `resultado.csv` -- uma linha por gravacao",
        "",
    ]
    if errors:
        lines += ["## Figuras que falharam", "",
                  "Uma figura quebrada nao derruba a coleta; fica registrada aqui.",
                  ""]
        lines += [f"- `{stem}`: {err}" for stem, err in errors]
        lines.append("")
    path.write_text("\n".join(lines), encoding='utf-8')


def captures(paths):
    """Accept .json files or directories holding them, in a stable order."""
    out = []
    for p in paths:
        p = Path(p)
        out += sorted(p.glob('*.json')) if p.is_dir() else [p]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nome', help="nome do teste; vira o nome da pasta")
    ap.add_argument('capturas', nargs='+',
                    help="arquivos .json de captura, ou diretorios com eles")
    ap.add_argument('--out', default='resultados')
    ap.add_argument('--note', default='', help="paragrafo livre no cabecalho")
    ap.add_argument('--bancada', default='', help="hardware e sala do teste")
    args = ap.parse_args()

    jsons = captures(args.capturas)
    if not jsons:
        sys.exit("[resultado] nenhuma captura encontrada")

    run = Path(args.out) / args.nome
    for sub in ('gravacao', 'llr', 'bits', 'figuras'):
        (run / sub).mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    print(f"[resultado] {run}  commit {commit}", flush=True)

    rows, metas, errors = [], [], []
    for jp in jsons:
        try:
            row, meta, nsym, err = score_one(jp, run)
        except (OSError, ValueError, KeyError) as e:
            print(f"[resultado] {jp}: {e}", file=sys.stderr)
            continue
        rows.append(row)
        metas.append(meta)
        if err:
            errors.append((row['stem'], err))
        bits = '--' if row['acerto_bits'] is None else f"{row['acerto_bits']:.2f}%"
        extra = ''
        if 'sincronismo' in row:
            g = row['acerto_bits_gate']
            extra = (f"  [{row['sincronismo']}; gate "
                     f"{'--' if g is None else f'{g:.2f}%'} "
                     f"{'OK' if row['bloco_ok_gate'] else 'nao'}]")
        print(f"  {row['stem']}  {nsym} simbolos  bits {bits}  "
              f"bloco {'--' if row['bloco_ok'] is None else ('OK' if row['bloco_ok'] else 'nao')}  "
              f"pico {row['pico_rx']:.2f}" + extra + ("  [figura falhou]" if err else ""),
              flush=True)

    if not rows:
        sys.exit("[resultado] nenhuma gravacao pontuada")

    # The union of every row's keys, in first-seen order: swept rows carry
    # extra columns, and a folder mixing both must not fail on the second kind.
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (run / 'resultado.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, restval='')
        w.writeheader()
        w.writerows(rows)
    header(run / 'HEADER.md', args.nome, rows, metas, args, commit, errors)
    print(f"[resultado] pronto: {run / 'HEADER.md'}")


if __name__ == '__main__':
    main()
