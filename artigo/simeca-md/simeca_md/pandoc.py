"""Localiza o pandoc no sistema e, se faltar, oferece a instalacao."""

import os
import shutil
import subprocess
import sys


GERENCIADORES_LINUX = (
    ("apt", ["sudo", "apt", "install", "pandoc"]),
    ("dnf", ["sudo", "dnf", "install", "pandoc"]),
    ("pacman", ["sudo", "pacman", "-S", "pandoc"]),
    ("zypper", ["sudo", "zypper", "install", "pandoc"]),
)

# O instalador do pandoc no Windows grava em uma destas pastas, por maquina ou
# por usuario, e o winget acrescenta um atalho na pasta de links dele. Nenhuma
# das tres chega ao PATH do processo que chamou a instalacao: a variavel de
# ambiente de um processo ja em execucao nao e' reescrita, entao logo depois de
# instalar o `which` continua devolvendo None e a montagem acusa a ausencia de
# um programa que acabou de ser instalado.
PASTAS_WINDOWS = (
    ("ProgramFiles", "Pandoc"),
    ("ProgramFiles(x86)", "Pandoc"),
    ("LOCALAPPDATA", "Pandoc"),
    ("LOCALAPPDATA", os.path.join("Microsoft", "WinGet", "Links")),
)

URL_MANUAL = "https://pandoc.org/installing.html"


def _no_windows():
    return sys.platform.startswith("win")


def _candidatos_windows():
    """Caminhos de pandoc.exe fora do PATH, nas pastas do instalador."""
    for variavel, subpasta in PASTAS_WINDOWS:
        raiz = os.environ.get(variavel)
        if raiz:
            yield os.path.join(raiz, subpasta, "pandoc.exe")


def caminho_pandoc():
    """Devolve o caminho do executavel pandoc, ou None se nao houver."""
    caminho = shutil.which("pandoc")
    if caminho:
        return caminho
    if _no_windows():
        for caminho in _candidatos_windows():
            if os.path.isfile(caminho):
                return caminho
    return None


def comando_instalacao():
    """Devolve o comando de instalacao do pandoc neste sistema, ou None."""
    if _no_windows():
        if not shutil.which("winget"):
            return None
        # As duas confirmacoes vao na linha de comando porque o winget, sem
        # elas, para em um prompt de licenca que ninguem esta ali para
        # responder quando a instalacao parte da montagem.
        return [
            "winget", "install", "--id", "JohnMacFarlane.Pandoc", "-e",
            "--accept-source-agreements", "--accept-package-agreements",
        ]
    if sys.platform == "darwin":
        if shutil.which("brew"):
            return ["brew", "install", "pandoc"]
        return None
    for gerenciador, comando in GERENCIADORES_LINUX:
        if shutil.which(gerenciador):
            return comando
    return None


def _texto_ausencia(comando):
    """Monta a explicacao da ausencia do pandoc, com o comando sugerido."""
    linhas = [
        "pandoc nao encontrado no PATH.",
        "O pandoc converte o LaTeX das equacoes em OMML e nao tem substituto no projeto.",
    ]
    if comando is None:
        linhas.append("Instale o pandoc manualmente: " + URL_MANUAL)
    else:
        linhas.append("Instale com:")
        linhas.append("")
        linhas.append("    " + " ".join(comando))
    if _no_windows():
        linhas.append("")
        linhas.append(
            "Um terminal ja aberto antes da instalacao nao enxerga o PATH novo; "
            "as pastas do instalador sao procuradas aqui de qualquer modo."
        )
    return "\n".join(linhas)


def _instala(comando):
    """Roda a instalacao herdando a saida do terminal, para o sudo poder pedir senha."""
    resultado = subprocess.run(comando)
    if resultado.returncode != 0:
        raise RuntimeError(
            "instalacao do pandoc falhou com codigo %d" % resultado.returncode
        )


def _confirma(comando):
    """Mostra a explicacao e pergunta ao usuario, com o padrao em sim."""
    print(_texto_ausencia(comando))
    print("")
    try:
        resposta = input("Instalar agora com o gerenciador do sistema? [S/n] ").strip()
    except EOFError:
        # No Windows o isatty() nao separa terminal de ausencia de terminal: o
        # dispositivo NUL e' um dispositivo de caractere e passa no teste, de
        # modo que um processo com a entrada redirecionada chega ate' aqui e so'
        # descobre no input() que nao ha ninguem para responder. Sem este
        # tratamento a montagem morre com um traceback de EOFError em vez da
        # mensagem que diz o que falta instalar.
        print("")
        return False
    return resposta == "" or resposta[:1] in ("s", "S")


def garante_pandoc(modo="auto"):
    """Devolve o caminho do pandoc, instalando-o conforme o modo se ele faltar.

    Modos: "auto" pergunta quando a entrada padrao e um terminal interativo,
    "instalar" instala direto, "nunca" apenas levanta RuntimeError.
    """
    caminho = caminho_pandoc()
    if caminho:
        return caminho

    comando = comando_instalacao()
    texto = _texto_ausencia(comando)

    if modo == "nunca" or comando is None:
        raise RuntimeError(texto)

    if modo == "instalar":
        _instala(comando)
    elif modo == "auto":
        if not sys.stdin.isatty():
            raise RuntimeError(texto)
        if not _confirma(comando):
            raise RuntimeError(texto)
        _instala(comando)
    else:
        raise ValueError("modo desconhecido: %r" % (modo,))

    caminho = caminho_pandoc()
    if not caminho:
        raise RuntimeError(
            "a instalacao terminou, mas o pandoc continua fora do PATH."
        )
    return caminho
