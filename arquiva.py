"""Archive captured audio as FLAC, so a recording can live in the repository.

A capture is written as 32-bit float WAV, because recording must not depend on
a codec. That format is 233 MB across `resultados/`, and float32 does not
compress: gzip -- which is all git would apply -- takes 7% off, because the
mantissa of room noise is incompressible by a general-purpose coder. FLAC
predicts the waveform and codes the residual, and takes 54% off the same
bytes. 107 MB is a repository a colleague can clone; 233 MB is one that wants
LFS and its bandwidth quota.

24 bit, and that number was measured rather than chosen. See the table in
`recording.py`'s docstring: at 16 bit the corpus loses a block, because a soft
Viterbi sitting on the rate-1/3 cliff needs only half a quantisation step to
decide the other way. The SNR argument for 16 bit is arithmetically correct
and predicts the wrong answer.

This tool never deletes the WAV. The machine that made the recording keeps the
exact samples; `.gitignore` keeps them out of the repository, and
`recording.audio_path` prefers them whenever they are still on disk. What
ships is the archive, and the two were measured to score the same.

    ./venv/bin/python arquiva.py resultados          # tudo que ainda falta
    ./venv/bin/python arquiva.py resultados --verifica   # so confere
"""

import argparse
import sys
from pathlib import Path

import numpy as np

import recording

# One ULP of float32 at 1.0, taken from numpy rather than typed as a literal:
# written out by hand as 1.19e-07 it lands just *below* the true
# 1.1920928955e-07, and six recordings then failed a check they had passed.
#
# Most samples round to half of this, because a 24-bit grid is finer than
# float32 over most of the range. Full scale is the exception and costs a
# whole ULP: signed 24-bit reaches 8388607/8388608 = 0.99999988, so a sample
# sitting at exactly 1.0 comes back one step down. That is not a fault in the
# archive, it is a fault in the recording -- `07-MARY-BASE` was captured at
# gain 1.0 and 9.4% of its samples are pinned at full scale, which is the
# saturation this project spent a bench correcting. Anything above one ULP
# would mean the write went out at the wrong depth, and the archive would be
# a different experiment from the recording.
TOLERANCIA = float(np.spacing(np.float32(1.0)))


def pares(root):
    """Every capture under `root`, as (wav, flac) paths, oldest name first."""
    return [(w, w.with_suffix('.flac')) for w in sorted(Path(root).rglob('*.wav'))]


def arquiva_um(wav, flac):
    """Write one FLAC and read it back. Returns (amostras, erro maximo)."""
    original = recording.read_wav(wav)
    if original.size == 0:
        # A capture that recorded nothing: 44 bytes of header and no samples.
        # `resultados/08-MARY-GAIN/gravacao/vazias/` holds one. There is
        # nothing to archive and nothing to check, and refusing to write an
        # empty FLAC keeps it visible as the failed capture it is.
        return 0, 0.0
    recording.write_flac(flac, original)
    volta = recording.read_flac(flac)
    if len(volta) != len(original):
        raise ValueError(f"{flac.name}: {len(volta)} amostras contra "
                         f"{len(original)} do original")
    return len(original), float(np.abs(original - volta).max())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('raiz', nargs='?', default='resultados',
                    help="diretorio a varrer, recursivamente")
    ap.add_argument('--verifica', action='store_true',
                    help="so confere os FLAC que ja existem; nao escreve nada")
    ap.add_argument('--refaz', action='store_true',
                    help="reescreve mesmo o FLAC que ja existe")
    args = ap.parse_args()

    todos = pares(args.raiz)
    if not todos:
        sys.exit(f"[arquiva] nenhum .wav em {args.raiz}")

    feitos = pulados = vazios = 0
    erro_max = 0.0
    falhas = []
    bytes_wav = bytes_flac = 0

    for wav, flac in todos:
        existe = flac.exists()
        if args.verifica and not existe:
            # A capture with no samples has no FLAC on purpose, so its absence
            # is the expected state and not a gap in the archive. Reporting it
            # as a failure trains the reader to ignore this tool's last line.
            if recording.read_wav(wav).size == 0:
                vazios += 1
            else:
                falhas.append((flac, "nao arquivado"))
            continue
        if existe and not (args.refaz or args.verifica):
            pulados += 1
            bytes_wav += wav.stat().st_size
            bytes_flac += flac.stat().st_size
            continue
        try:
            if args.verifica:
                original = recording.read_wav(wav)
                volta = recording.read_flac(flac)
                if len(volta) != len(original):
                    raise ValueError(f"{len(volta)} amostras contra {len(original)}")
                n, erro = len(original), float(np.abs(original - volta).max())
            else:
                n, erro = arquiva_um(wav, flac)
            if n == 0:
                vazios += 1
                continue
            if erro > TOLERANCIA:
                falhas.append((flac, f"erro {erro:.2e} acima da tolerancia"))
                continue
            erro_max = max(erro_max, erro)
            feitos += 1
            bytes_wav += wav.stat().st_size
            bytes_flac += flac.stat().st_size
            print(f"  {flac.name}  {n} amostras  erro {erro:.2e}", flush=True)
        except Exception as exc:                        # noqa: BLE001
            falhas.append((flac, f"{type(exc).__name__}: {exc}"))

    verbo = "conferidos" if args.verifica else "arquivados"
    print(f"\n[arquiva] {feitos} {verbo}, {pulados} ja existiam, "
          f"{vazios} sem amostras, {len(falhas)} com problema")
    if erro_max:
        print(f"[arquiva] erro maximo {erro_max:.2e} "
              f"(tolerancia {TOLERANCIA:.2e}, 1 ULP do float32)")
    if bytes_wav:
        print(f"[arquiva] {bytes_wav / 2**20:.1f} MB em WAV "
              f"-> {bytes_flac / 2**20:.1f} MB em FLAC "
              f"({100 * bytes_flac / bytes_wav:.0f}%)")
    for path, motivo in falhas:
        print(f"[arquiva] FALHOU {path}: {motivo}")
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main())
