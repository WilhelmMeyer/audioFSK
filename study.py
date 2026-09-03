"""Run a measurement campaign and leave behind a folder an article can cite.

`selfcapture.py` records one condition; `align.py` and `bench.py` score what
was recorded. Neither keeps the two together, and for a paper that separation
is the whole problem: a number is only usable if the audio it came from, the
settings that produced it, and the code that read it are all still identifiable
six months later. Reproducing a plot from a bare table of percentages means
running the room again, and the room does not hold still.

So one run of this script produces one directory:

    studies/<when>-<name>/
        HEADER.md        what was measured, on what, with what, and the result
        results.csv      one row per trial -- the numbers behind every figure
        results.json     the same, plus the full per-condition metadata
        recordings/      the wav + json pairs, exactly as recording.py writes
        figures/         spectrograms and the summary chart, as PNG

`HEADER.md` opens with the commit the code was at. That is not bookkeeping: the
demodulator is under active change, and a bit accuracy is a statement about a
decoder as much as about a channel.

    ./venv/bin/python -u study.py --name melhor-caso --trials 12 \\
        --out-device bluez_output.8B:36:58:74:F6:0B --in-device Mic1 \\
        --link bluetooth --sync-chirp --repeat 2 --gain 0.5

    ./venv/bin/python -u study.py --name ganho --sweep gain=0.35,0.45,0.55,0.7

One axis at a time, on purpose. Two swept axes multiply the trials and this
link needs repetitions more than it needs breadth -- with four recordings per
point, block recovery cannot resolve a coin flip.
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import fec
import recording
import spectro
from align import bit_accuracy, soft
from modem import (MaryDemodulator, MFSKDemodulator, MFSK_PAIRS,
                   chirp, find_chirp, find_chirp_pair, SYNC_CHIRP)

FS = 48000
BAUD = 100
PY = sys.executable

# The knobs a condition can vary. Each maps to a selfcapture flag; anything
# not here is held fixed across the campaign and recorded in the header as a
# constant, which is the distinction the header has to make.
AXES = {
    'gain': '--gain',
    'repeat': '--repeat',
    'bytes': '--bytes',
    'gap': '--gap',
    'band': '--band',
}


def git_commit():
    """The commit the code was at, dirty flag included.

    A bit accuracy is a statement about a decoder as much as about a channel,
    and this decoder changes weekly. `-dirty` is not a warning to be tidied
    away either -- it is the honest label for a number produced by code that
    was never committed and so cannot be recovered.
    """
    try:
        head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                              capture_output=True, text=True, check=True)
        dirty = subprocess.run(['git', 'status', '--porcelain'],
                               capture_output=True, text=True, check=True)
        return head.stdout.strip() + ('-dirty' if dirty.stdout.strip() else '')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'desconhecido'


def record_condition(args, value, outdir, label):
    """One condition, recorded by handing selfcapture.py a command line.

    A subprocess rather than an import, and the reason is the Bluetooth sink:
    PortAudio builds its device list once at import and never revisits it, so
    a sink that was not ready when this process started is never ready. A
    fresh process per condition gets a fresh list for free, and a crash in one
    condition costs that condition rather than the campaign.
    """
    cmd = [PY, '-u', 'selfcapture.py',
           '--mode', args.mode, '--trials', str(args.trials),
           '--out', str(outdir), '--label', label,
           '--link', args.link, '--tail', str(args.tail)]
    if args.fec:
        cmd += ['--fec']
    if args.sync_chirp:
        cmd += ['--sync-chirp', '--sync-hush', str(args.sync_hush)]
    if args.in_device:
        cmd += ['--in-device', args.in_device]
    if args.out_device:
        cmd += ['--out-device', args.out_device]
    fixed = {'gain': args.gain, 'repeat': args.repeat, 'bytes': args.bytes,
             'gap': args.gap, 'band': args.band}
    if args.axis:
        fixed[args.axis] = value
    for key, flag in AXES.items():
        if fixed[key] is not None:
            cmd += [flag, str(fixed[key])]
    print(f"[study] {label}: {' '.join(cmd[2:])}", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"[study] {label} falhou (codigo {r.returncode})", file=sys.stderr)
    return r.returncode == 0


def score_gate(samples, payload, meta):
    """What the receiver in the code today gets: the early/late gate."""
    kw = dict(fs=meta['fs'], baud=meta['baud'], gap=meta.get('gap', 0.0),
              band=meta.get('band', 0.0), chord=meta.get('chord', False))
    if meta['mode'] == 'mary':
        d = MaryDemodulator(**kw)
    else:
        d = MFSKDemodulator(fs=meta['fs'], baud=meta['baud'],
                            parallel=meta.get('parallel', False),
                            grouped=meta.get('grouped', False))
    llr = soft(d, samples)
    return llr


def score_sweep(samples, meta, nbytes):
    """What the sweeps get: a frozen clock at a measured period.

    Mirrors `AudioNode._sweep_llr`, which is what actually runs on the link.
    The span is recomputed here from the payload length rather than read from
    the recording's metadata, precisely so a disagreement between the two
    shows up as a period out of range instead of being papered over.
    """
    fs, sps = meta['fs'], meta['fs'] / meta['baud']
    tmpl = chirp(fs, *SYNC_CHIRP)
    hush = int(meta.get('sync_hush', 0.0) * fs)
    pre = fec.preamble_bits('mary', symbol_bits=4)
    nbits = len(fec.frame(bytes(nbytes), repeat=meta['fec_repeat']))
    span = (len(pre) // 4 + -(-nbits // 4) + 6) + 2 * hush / sps
    skip = period = None
    pair = find_chirp_pair(samples, tmpl, min_gap=int(0.5 * span * sps))
    if pair is not None:
        first, second = pair
        p = (second - first) / span
        if 0.98 * sps <= p <= 1.02 * sps:
            skip, period = first + int(round(hush * p / sps)), p
    if skip is None:
        at = find_chirp(samples, tmpl)
        if at is None:
            return None, None
        skip = at + hush
    d = MaryDemodulator(fs=fs, baud=meta['baud'], gap=meta.get('gap', 0.0),
                        band=meta.get('band', 0.0),
                        chord=meta.get('chord', False),
                        steer=False, skip=skip, period=period)
    return soft(d, samples), period


def decodes(llr, payload, meta):
    if llr is None:
        return False
    npairs = len(MFSK_PAIRS)
    if meta.get('parallel'):
        start = fec.find_sync_parallel(llr, npairs)
        if start is None:
            return False
        got = fec.decode_parallel(llr[start:], len(payload), npairs,
                                  repeat=meta['fec_repeat'])
    else:
        start = fec.find_sync(llr)
        if start is None:
            return False
        got = fec.decode(llr[start:], len(payload), repeat=meta['fec_repeat'])
    return got == payload


def score_one(jp):
    """Every number one recording yields, on one ruler.

    Bit accuracy is always taken at the best brute-forced slide, for the gate
    row as well as the sweep row. Scoring the gate where the gate happened to
    land and the sweep where the sweep landed compares two rulers, and that
    inversion once made the worst setting report the best accuracy. Blocks
    recovered stays as the separate honest number -- it is what the link
    actually delivered, and it is noisy with few recordings.
    """
    samples, payload, meta = recording.load(jp)
    samples = np.asarray(samples, dtype=np.float64)
    row = {
        'recording': Path(jp).stem,
        'mode': meta['mode'], 'gain': meta.get('gain'),
        'repeat': meta.get('fec_repeat'), 'bytes': len(payload),
        'gap': meta.get('gap'), 'band': meta.get('band'),
        'link': meta.get('link'), 'label': meta.get('label'),
        'rms': round(float(meta.get('rms', 0.0)), 4),
        'peak': round(float(meta.get('peak', 0.0)), 4),
        'airtime_s': meta.get('airtime_s'),
    }
    gate = score_gate(samples, payload, meta)
    row['gate_bits'] = round(100 * bit_accuracy(gate, payload, meta['fec_repeat']), 2)
    row['gate_block'] = int(decodes(gate, payload, meta))
    row['sweep_bits'] = row['sweep_block'] = row['period'] = None
    if meta.get('sync_chirp') and meta['mode'] == 'mary':
        llr, period = score_sweep(samples, meta, len(payload))
        if llr is not None:
            row['sweep_bits'] = round(100 * bit_accuracy(llr, payload,
                                                         meta['fec_repeat']), 2)
            row['sweep_block'] = int(decodes(llr, payload, meta))
            row['period'] = None if period is None else round(period, 3)
    return row, meta


def chart(rows, axis, path):
    """Blocks recovered and bit accuracy per condition, as a PNG.

    Hand-drawn into an array rather than through a plotting library, because
    the project has no plotting dependency and adding one to draw two bars per
    condition would be the largest dependency in it. `spectro.write_png` and
    `spectro.draw_text` already exist for the spectrograms.
    """
    groups = {}
    for r in rows:
        groups.setdefault(r['group'], []).append(r)
    keys = list(groups)
    w, h = max(420, 120 * len(keys) + 120), 340
    img = np.full((h, w, 3), 250, dtype=np.uint8)
    base, top = h - 60, 50
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = int(base - frac * (base - top))
        img[y, 70:w - 20] = 210
        spectro.draw_text(img, 20, y - 6, f"{int(100 * frac):3d}", (120, 120, 120), 1)
    # Two bars per condition: what the link delivered (blocks whole) and what
    # the bits did (accuracy). They answer different questions and the paper
    # needs both -- blocks is the honest outcome, bits is the stable ruler.
    for i, k in enumerate(keys):
        g = groups[k]
        x0 = 90 + i * 110
        for j, (field, colour) in enumerate((('block', (60, 90, 200)),
                                             ('bits', (200, 110, 40)))):
            if field == 'block':
                v = sum(r['block'] for r in g) / len(g)
            else:
                v = np.mean([r['bits'] for r in g]) / 100.0
            y = int(base - v * (base - top))
            img[y:base, x0 + j * 42:x0 + j * 42 + 34] = colour
            spectro.draw_text(img, x0 + j * 42, y - 14, f"{100 * v:.0f}", colour, 1)
        spectro.draw_text(img, x0, base + 10, str(k)[:12], (40, 40, 40), 1)
        spectro.draw_text(img, x0, base + 26, f"n={len(g)}", (140, 140, 140), 1)
    spectro.draw_text(img, 20, 16, f"{axis or 'condicao'}: blocos inteiros (azul), "
                                   f"bits certos (laranja)", (40, 40, 40), 1)
    spectro.write_png(path, img)


def header(path, args, rows, metas, commit, started, elapsed):
    """The file the article is written from.

    Everything a methods section has to state, in the order it has to state
    it: what was measured, on what hardware, with which settings held fixed,
    over how many trials, and what came out. The caveats are not an appendix
    -- self-capture does not reproduce the real link, and a reader who takes
    these numbers for a two-machine result is being misled by the omission.
    """
    m = metas[0] if metas else {}
    groups = {}
    for r in rows:
        groups.setdefault(r['group'], []).append(r)

    def block(rs, field):
        vals = [r[field] for r in rs if r[field] is not None]
        return f"{sum(vals)}/{len(vals)}" if vals else "--"

    def bits(rs, field):
        vals = [r[field] for r in rs if r[field] is not None]
        return f"{np.mean(vals):.1f}%" if vals else "--"

    lines = [
        f"# {args.name}",
        "",
        f"- **Quando:** {started}  (campanha de {elapsed/60:.1f} min)",
        f"- **Codigo:** commit `{commit}`",
        f"- **Camada:** {args.mode}"
        + (f", FEC rate 1/3 x{args.repeat}" if args.fec else ", sem FEC"),
        f"- **Sincronismo:** {'varredura nas duas pontas' if args.sync_chirp else 'gate early/late'}",
        f"- **Canal:** auto-captura, enlace `{args.link}`",
        f"- **Saida:** `{m.get('out_device', args.out_device)}`",
        f"- **Entrada:** `{m.get('in_device', args.in_device)}`",
        f"- **Amostragem:** {m.get('fs', FS)} Hz, {m.get('baud', BAUD)} baud",
        f"- **Bloco:** {args.bytes} bytes de payload",
        f"- **Repeticoes:** {args.trials} por condicao, {len(rows)} gravacoes ao todo",
    ]
    if args.axis:
        lines.append(f"- **Eixo varrido:** `{args.axis}` = "
                     + ", ".join(str(k) for k in groups))
    else:
        lines.append(f"- **Ganho:** {args.gain}")
    if args.note:
        lines += ["", args.note]
    lines += ["", "## Resultado", ""]
    if args.sync_chirp:
        lines += [f"| {args.axis or 'condicao'} | n | blocos (gate) | blocos (varredura) "
                  "| bits (gate) | bits (varredura) | periodo |",
                  "|---|---|---|---|---|---|---|"]
        for k, rs in groups.items():
            per = [r['period'] for r in rs if r['period']]
            lines.append(
                f"| {k} | {len(rs)} | {block(rs, 'gate_block')} "
                f"| {block(rs, 'sweep_block')} | {bits(rs, 'gate_bits')} "
                f"| {bits(rs, 'sweep_bits')} "
                f"| {f'{np.mean(per):.2f}' if per else '--'} |")
    else:
        lines += [f"| {args.axis or 'condicao'} | n | blocos | bits |",
                  "|---|---|---|---|"]
        for k, rs in groups.items():
            lines.append(f"| {k} | {len(rs)} | {block(rs, 'gate_block')} "
                         f"| {bits(rs, 'gate_bits')} |")
    rms = [r['rms'] for r in rows]
    peak = [r['peak'] for r in rows]
    lines += [
        "",
        f"Nivel recebido: rms {np.mean(rms):.3f}, pico {np.mean(peak):.2f} "
        f"(maior {max(peak):.2f}).",
        "",
        "## Como ler",
        "",
        "Acuracia de bit e sempre medida no melhor deslizamento por forca bruta,",
        "na linha do gate tanto quanto na da varredura. Medir cada uma onde ela",
        "por acaso caiu compara duas reguas, e foi o que uma vez fez a pior",
        "configuracao reportar a maior acuracia. Blocos inteiros fica como o",
        "numero honesto separado: e o que o enlace entregou, e com poucas",
        "gravacoes ele e ruidoso.",
        "",
        "## Ressalvas",
        "",
        "Auto-captura: alto-falante e microfone na mesma maquina, pelo ar. O ar,",
        "o pente da sala, o limitador e o microfone sao reais. O que falta e",
        f"especifico -- com enlace `{args.link}`, "
        + ("a caixa tem cristal proprio e a deriva de taxa de amostragem esta "
           "presente, ao custo de um codec com perda que o enlace real nao tem."
           if args.link == 'bluetooth' else
           "as duas pontas dividem o clock da placa, entao a deriva de taxa de "
           "amostragem -- parte do que o gate existe para corrigir -- esta "
           "ausente e os numeros de sincronismo saem otimistas."),
        "Nao misturar corpora de enlaces diferentes na mesma media.",
        "",
        "## Arquivos",
        "",
        "- `results.csv`, `results.json` -- uma linha por gravacao",
        "- `recordings/` -- wav 32-bit float + json, formato de `recording.py`",
        "- `figures/` -- espectrogramas e o grafico de resumo",
        "",
        "Reproduzir a pontuacao sem gravar de novo:",
        "",
        "```bash",
        f"./venv/bin/python study.py --rescore {path.parent}",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding='utf-8')


def collect(run, args, commit, started, elapsed):
    """Score everything in the run directory and write the three outputs."""
    rows, metas = [], []
    for jp in sorted((run / 'recordings').glob('*.json')):
        row, meta = score_one(str(jp))
        if meta.get('kind') != 'fec':
            continue
        row['group'] = row.get(args.axis) if args.axis else (args.axis or 'unico')
        if args.axis == 'bytes':
            row['group'] = row['bytes']
        # The paper's headline number is whichever path was actually in use.
        row['block'] = (row['sweep_block'] if row['sweep_block'] is not None
                        else row['gate_block'])
        row['bits'] = (row['sweep_bits'] if row['sweep_bits'] is not None
                       else row['gate_bits'])
        rows.append(row)
        metas.append(meta)
        print(f"  {row['recording']}  bits {row['bits']}%  "
              f"bloco {'OK' if row['block'] else 'no'}"
              + (f"  periodo {row['period']}" if row['period'] else ""), flush=True)
    if not rows:
        print("[study] nenhuma gravacao para pontuar", file=sys.stderr)
        return rows

    fields = [k for k in rows[0] if k != 'group'] + ['group']
    with (run / 'results.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (run / 'results.json').write_text(
        json.dumps({'commit': commit, 'started': started,
                    'elapsed_s': round(elapsed, 1),
                    'args': {k: v for k, v in vars(args).items()},
                    'rows': rows}, indent=2, ensure_ascii=False),
        encoding='utf-8')

    figs = run / 'figures'
    figs.mkdir(exist_ok=True)
    chart(rows, args.axis, str(figs / 'resumo.png'))
    # One spectrogram per condition, not one per trial: twelve near-identical
    # pictures of the same burst say nothing twelve times, and each is a
    # megabyte. The first of each group, so the choice is not made by looking
    # at the scores first.
    seen = set()
    for row in rows:
        if row['group'] in seen:
            continue
        seen.add(row['group'])
        jp = run / 'recordings' / (row['recording'] + '.json')
        out = figs / f"espectro-{row['group']}.png"
        subprocess.run([PY, 'spectro.py', str(jp), '-o', str(out),
                        '--ideal'], capture_output=True)
        if out.exists():
            print(f"  figura {out.name}", flush=True)
    header(run / 'HEADER.md', args, rows, metas, commit, started, elapsed)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', default='estudo', help="nome da campanha")
    ap.add_argument('--out', default='studies')
    ap.add_argument('--note', default='', help="paragrafo livre no cabecalho")
    ap.add_argument('--rescore', metavar='DIR',
                    help="pontuar de novo um diretorio ja gravado, sem tocar no audio")

    ap.add_argument('--mode', choices=('fsk', 'mfsk', 'mary'), default='mary')
    ap.add_argument('--fec', action='store_true', default=True)
    ap.add_argument('--no-fec', dest='fec', action='store_false')
    ap.add_argument('--sync-chirp', action='store_true')
    ap.add_argument('--sync-hush', type=float, default=0.03)
    ap.add_argument('--gain', type=float, default=0.5)
    ap.add_argument('--repeat', type=int, default=2)
    ap.add_argument('--bytes', type=int, default=48)
    ap.add_argument('--gap', type=float, default=None)
    ap.add_argument('--band', type=float, default=None)
    ap.add_argument('--trials', type=int, default=8)
    ap.add_argument('--tail', type=float, default=2.0)
    ap.add_argument('--in-device')
    ap.add_argument('--out-device')
    ap.add_argument('--link', default='bluetooth',
                    choices=('bluetooth', 'wired', 'auto'))
    ap.add_argument('--sweep', metavar='EIXO=v1,v2,...',
                    help="uma condicao por valor; eixos: " + ", ".join(AXES))
    args = ap.parse_args()

    if args.rescore:
        run = Path(args.rescore)
        meta = json.loads((run / 'results.json').read_text(encoding='utf-8'))
        saved = argparse.Namespace(**meta['args'])
        saved.rescore = None
        collect(run, saved, git_commit(), meta['started'], meta['elapsed_s'])
        print(f"[study] repontuado: {run}")
        return

    args.axis, values = None, [None]
    if args.sweep:
        key, _, spec = args.sweep.partition('=')
        if key not in AXES:
            sys.exit(f"[study] eixo desconhecido: {key!r} (use {', '.join(AXES)})")
        args.axis = key
        cast = int if key in ('repeat', 'bytes') else float
        values = [cast(v) for v in spec.split(',') if v]

    started = time.strftime('%Y-%m-%d %H:%M:%S')
    run = Path(args.out) / f"{time.strftime('%Y%m%d-%H%M%S')}-{args.name}"
    (run / 'recordings').mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    print(f"[study] {run}  commit {commit}", flush=True)

    t0 = time.time()
    for v in values:
        label = f"{args.axis}{v}" if args.axis else args.name
        record_condition(args, v, run / 'recordings', label)
    elapsed = time.time() - t0

    print(f"[study] pontuando {len(list((run / 'recordings').glob('*.json')))} gravacoes",
          flush=True)
    collect(run, args, commit, started, elapsed)
    print(f"[study] pronto: {run / 'HEADER.md'}")


if __name__ == '__main__':
    main()
