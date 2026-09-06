"""Monta o artigo: markdown para docx e, com --pdf, para PDF.

Ponto unico de logica da montagem. `monta.sh` e `monta.cmd` sao dois
invocadores finos do mesmo arquivo, pela mesma razao que `console.py` tem uma
tabela de comandos so: forkar a logica em dois sistemas e' deixar os dois
divergirem em silencio.

Roda de qualquer pasta, no Linux e no Windows, com o Python do sistema. O
conversor esta em `artigo/simeca-md/`, versionado neste repositorio, e nao usa
biblioteca de terceiros, entao nao ha `pip install` nem venv envolvida aqui.
"""

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CONVERSOR = AQUI / "simeca-md"
FONTE = AQUI / "artigo_modem.md"
MODELO = CONVERSOR / "modelos" / "simeca-vii" / "modelo.docx"
SAIDA = AQUI / "artigo_modem.docx"

MINIMO = (3, 11)


def erro(mensagem):
    print(mensagem, file=sys.stderr)
    return 1


def confere_python():
    if sys.version_info < MINIMO:
        return erro(
            "o conversor exige Python %d.%d ou mais novo, e este e' %s.\n"
            "No Windows instale pela Microsoft Store ou em python.org e rode de novo."
            % (MINIMO[0], MINIMO[1], sys.version.split()[0])
        )
    return 0


def confere_conversor():
    if (CONVERSOR / "simeca_md" / "__main__.py").is_file():
        return 0
    return erro(
        "conversor nao encontrado em %s.\n"
        "Ele e' versionado junto com o projeto; recupere a pasta com:\n"
        "    git checkout -- artigo/simeca-md" % CONVERSOR
    )


def main(argv):
    codigo = confere_python() or confere_conversor()
    if codigo:
        return codigo

    # O conversor entra pelo sys.path, nao por um `cd` para dentro dele: as
    # figuras ja resolvem a partir da pasta do .md (`registra_figura`), e o
    # unico motivo do `cd` era o caminho relativo do modelo, que aqui vai
    # absoluto.
    sys.path.insert(0, str(CONVERSOR))
    from simeca_md.cli import main as conversor_main

    return conversor_main([
        str(FONTE),
        "-m", str(MODELO),
        "-o", str(SAIDA),
        "--pdf",
    ] + list(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
