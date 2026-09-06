"""Monta o artigo: markdown para docx e, com --pdf, para PDF.

Ponto unico de logica da montagem. `monta.sh` e `monta.cmd` sao dois
invocadores finos do mesmo arquivo, pela mesma razao que `console.py` tem uma
tabela de comandos so: forkar a logica em dois sistemas e' deixar os dois
divergirem em silencio.

Roda de qualquer pasta, no Linux e no Windows, com o Python do sistema. O
conversor nao tem dependencia de terceiros (`dependencies = []` no
pyproject), entao nao ha venv envolvida aqui.
"""

import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
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


def garante_conversor():
    """Inicializa o submodulo do conversor se a pasta estiver vazia.

    Iniciar um submodulo vazio nao descarta nada, entao aqui e' seguro agir
    em vez de so imprimir o comando. Uma pasta com conteudo mas sem o modulo
    e' outra coisa, e essa so' reporta.
    """
    if (CONVERSOR / "simeca_md" / "__main__.py").is_file():
        return 0

    existente = [p for p in CONVERSOR.glob("*")] if CONVERSOR.is_dir() else []
    if existente:
        return erro(
            "conversor incompleto em %s.\n"
            "Rode: git submodule update --init --recursive -- artigo/simeca-md" % CONVERSOR
        )

    if not (RAIZ / ".gitmodules").is_file():
        return erro(
            "conversor ausente em %s e o repositorio nao tem .gitmodules.\n"
            "Provavelmente o projeto veio de um ZIP do GitHub, que nao traz submodulo.\n"
            "Clone com: git clone --recurse-submodules <url>" % CONVERSOR
        )

    print("conversor ausente, inicializando o submodulo artigo/simeca-md...", flush=True)
    comando = ["git", "submodule", "update", "--init", "--recursive",
               "--", str(CONVERSOR)]
    try:
        codigo = subprocess.call(comando, cwd=str(RAIZ))
    except OSError as e:
        return erro("nao consegui rodar o git (%s). Instale o git e rode: %s"
                    % (e, " ".join(comando)))
    if codigo != 0 or not (CONVERSOR / "simeca_md" / "__main__.py").is_file():
        return erro("a inicializacao do submodulo falhou. Rode a mao: " + " ".join(comando))
    return 0


def main(argv):
    codigo = confere_python() or garante_conversor()
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
