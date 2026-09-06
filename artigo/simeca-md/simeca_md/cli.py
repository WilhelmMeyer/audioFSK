"""Linha de comando: markdown mais modelo docx, saida docx e, se pedido, PDF."""

import argparse
import sys
from pathlib import Path

from . import pdf as motor_pdf
from .conversor import monta
from .modelo import Modelo
from .verifica import confere, relata


def analisa_argumentos(argv=None):
    p = argparse.ArgumentParser(
        prog="simeca-md",
        description="Converte um markdown em docx no formato de um modelo do Word.",
    )
    p.add_argument("markdown", help="arquivo .md a converter")
    p.add_argument("-m", "--modelo", required=True, help="docx do modelo a preencher")
    p.add_argument("-d", "--descritor", default=None,
                   help="toml do modelo, se nao estiver ao lado do docx")
    p.add_argument("-o", "--saida", default=None,
                   help="docx de saida, padrao e o nome do markdown")
    p.add_argument("--pdf", action="store_true", help="gera tambem o PDF a partir do docx")
    p.add_argument("--sem-figuras", action="store_true",
                   help="gera so com as legendas, sem embutir imagens")
    p.add_argument("--sem-verifica", action="store_true",
                   help="nao confere o docx logo apos gerar")
    p.add_argument("--verifica", action="store_true",
                   help="so confere o docx ja gerado, nao gera nada")
    p.add_argument("--pandoc", choices=("auto", "instalar", "nunca"), default="auto",
                   help="o que fazer se o pandoc nao estiver instalado")
    return p.parse_args(argv)


def main(argv=None):
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = analisa_argumentos(argv)
    md = Path(args.markdown).resolve()
    saida = Path(args.saida).resolve() if args.saida else md.with_suffix(".docx")
    com_figuras = not args.sem_figuras

    try:
        modelo = Modelo(args.modelo, args.descritor)

        if args.verifica:
            resultados, avisos, legendas = confere(modelo, md, saida, com_figuras)
            return 0 if relata(resultados, avisos, False, legendas) else 1

        est = monta(md, modelo, saida, com_figuras, args.pandoc)
        if est.figuras:
            print(f"Escrito {saida} com {len(est.figuras)} imagens embutidas")
        else:
            print(f"Escrito {saida} sem imagens (so legendas)")

        codigo = 0
        if not args.sem_verifica:
            print()
            resultados, avisos, legendas = confere(modelo, md, saida, com_figuras)
            if not relata(resultados, avisos, resumido=True):
                codigo = 1

        if args.pdf:
            gerado = motor_pdf.gera_pdf(saida)
            if gerado is None:
                print()
                print(motor_pdf.mensagem_sem_motor())
            else:
                print(f"Escrito {gerado}")
        return codigo
    except RuntimeError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
