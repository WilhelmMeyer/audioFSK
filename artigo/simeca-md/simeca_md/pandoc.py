"""Localiza o pandoc no sistema e, se faltar, oferece a instalacao."""

import shutil
import subprocess
import sys


GERENCIADORES_LINUX = (
    ("apt", ["sudo", "apt", "install", "pandoc"]),
    ("dnf", ["sudo", "dnf", "install", "pandoc"]),
    ("pacman", ["sudo", "pacman", "-S", "pandoc"]),
    ("zypper", ["sudo", "zypper", "install", "pandoc"]),
)


def caminho_pandoc():
    """Devolve o caminho do executavel pandoc, ou None se nao estiver no PATH."""
    return shutil.which("pandoc")


def comando_instalacao():
    """Devolve o comando de instalacao do pandoc neste sistema, ou None."""
    if sys.platform.startswith("win"):
        return ["winget", "install", "--id", "JohnMacFarlane.Pandoc"]
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
        linhas.append("Instale o pandoc manualmente.")
    else:
        linhas.append("Instale com:")
        linhas.append("")
        linhas.append("    " + " ".join(comando))
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
    resposta = input("Instalar agora com o gerenciador do sistema? [S/n] ").strip()
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

    caminho = shutil.which("pandoc")
    if not caminho:
        raise RuntimeError(
            "a instalacao terminou, mas o pandoc continua fora do PATH."
        )
    return caminho
