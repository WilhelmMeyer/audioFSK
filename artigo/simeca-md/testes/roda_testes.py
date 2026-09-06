"""Runner de testes do simeca-md, sem framework, so biblioteca padrao.

Roda com `python3 testes/roda_testes.py` a partir da raiz do repositorio.
Cada teste imprime [OK] ou [FALHA] com o motivo; no fim, um resumo N de M.
Tudo que os testes geram vai para um diretorio temporario, nunca no repo.
"""

import contextlib
import io
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from simeca_md.cli import main  # noqa: E402

MODELO_DOCX = RAIZ / "modelos" / "simeca-vii" / "modelo.docx"
EXEMPLO_DIR = RAIZ / "exemplos"
EXEMPLO_MD = EXEMPLO_DIR / "minimo.md"
MAX_AUTORES = 6


def copia_exemplo(destino, texto_md=None):
    """Copia o exemplo minimo (md e figuras) para dentro de destino.

    Se texto_md for dado, grava esse texto no lugar do conteudo original.
    Devolve o caminho do md copiado.
    """
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copytree(EXEMPLO_DIR / "figuras", destino / "figuras")
    md_destino = destino / "minimo.md"
    if texto_md is None:
        shutil.copy(EXEMPLO_MD, md_destino)
    else:
        md_destino.write_text(texto_md, encoding="utf-8")
    return md_destino


def troca_unica(texto, antigo, novo):
    """Substitui uma ocorrencia de antigo por novo, falha se nao for unica."""
    n = texto.count(antigo)
    if n != 1:
        raise AssertionError(f"esperava 1 ocorrencia de {antigo!r}, achei {n}")
    return texto.replace(antigo, novo, 1)


def roda_cli(argv):
    """Chama main() como funcao, capturando stdout/stderr e o codigo de saida."""
    saida = io.StringIO()
    erro = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        codigo = main(argv)
    return codigo, saida.getvalue(), erro.getvalue()


class Resultado:
    def __init__(self):
        self.nomes_ok = []
        self.nomes_falha = []

    def registra(self, nome, ok, motivo=""):
        if ok:
            print(f"[OK] {nome}")
            self.nomes_ok.append(nome)
        else:
            print(f"[FALHA] {nome}: {motivo}")
            self.nomes_falha.append(nome)

    def total(self):
        return len(self.nomes_ok) + len(self.nomes_falha)


def teste_caminho_feliz(r, tmp, cache):
    nome = "caminho feliz gera docx com verificacao 18 de 18"
    md = copia_exemplo(tmp / "feliz")
    codigo, saida, erro = roda_cli(["-m", str(MODELO_DOCX), str(md)])
    cache["feliz_md"] = md
    cache["feliz_saida"] = md.with_suffix(".docx")
    cache["feliz_stdout"] = saida
    ok = (
        codigo == 0
        and "Verificacao: 18 de 18 checagens OK" in saida
        and cache["feliz_saida"].exists()
    )
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


def teste_sem_figuras(r, tmp, cache):
    nome = "--sem-figuras gera docx so com legendas"
    md = copia_exemplo(tmp / "sem_figuras")
    codigo, saida, erro = roda_cli(
        ["-m", str(MODELO_DOCX), "--sem-figuras", str(md)]
    )
    ok = (
        codigo == 0
        and re.search(r"Verificacao: (\d+) de \1 checagens OK", saida) is not None
        and "sem imagens (so legendas)" in saida
    )
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


def teste_verifica(r, tmp, cache):
    nome = "--verifica sobre o docx do caminho feliz"
    md = cache.get("feliz_md")
    if md is None:
        r.registra(nome, False, "teste do caminho feliz nao rodou antes")
        return
    codigo, saida, erro = roda_cli(["-m", str(MODELO_DOCX), "--verifica", str(md)])
    ok = codigo == 0
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


def teste_aviso_orcid(r, tmp, cache):
    nome = "aviso de autor sem ORCID no caminho feliz"
    saida = cache.get("feliz_stdout")
    if saida is None:
        r.registra(nome, False, "teste do caminho feliz nao rodou antes")
        return
    linhas_aviso = [l for l in saida.splitlines() if l.startswith("[AVISO]")]
    ok = any("Segundo Autor" in l for l in linhas_aviso)
    motivo = "" if ok else f"avisos encontrados: {linhas_aviso!r}"
    r.registra(nome, ok, motivo)


def roda_erro(subdir, tmp, texto_md, mensagem_esperada, argv_extra=()):
    md = copia_exemplo(tmp / subdir, texto_md)
    codigo, saida, erro = roda_cli([
        "-m", str(MODELO_DOCX), *argv_extra, str(md),
    ])
    linhas_erro = [l for l in erro.splitlines() if l.startswith("ERRO:")]
    ok = codigo == 1 and any(mensagem_esperada in l for l in linhas_erro)
    motivo = "" if ok else (
        f"codigo={codigo}, stderr={erro!r}, esperava trecho {mensagem_esperada!r}"
    )
    return ok, motivo


def teste_erro_campos_autor(r, tmp, cache):
    nome = "erro: linha de autor com numero errado de campos"
    texto = EXEMPLO_MD.read_text(encoding="utf-8")
    texto = troca_unica(
        texto,
        "1. Primeira Autora | 0000-0002-1825-0097 | Instituto Federal, Campus Exemplo | primeira.autora@exemplo.br",
        "1. Primeira Autora | 0000-0002-1825-0097 | Instituto Federal, Campus Exemplo",
    )
    ok, motivo = roda_erro(
        "erro_campos_autor", tmp, texto,
        "Linha de autor precisa de 4 campos separados por |",
    )
    r.registra(nome, ok, motivo)


def teste_erro_orcid_invalido(r, tmp, cache):
    nome = "erro: ORCID em formato invalido"
    texto = EXEMPLO_MD.read_text(encoding="utf-8")
    texto = troca_unica(texto, "0000-0002-1825-0097", "0000-0002-1825-XYZ1")
    ok, motivo = roda_erro(
        "erro_orcid_invalido", tmp, texto, "ORCID em formato inesperado",
    )
    r.registra(nome, ok, motivo)


def teste_erro_sem_nome(r, tmp, cache):
    nome = "erro: bloco de autores sem nenhum nome preenchido"
    texto = EXEMPLO_MD.read_text(encoding="utf-8")
    texto = troca_unica(
        texto,
        "1. Primeira Autora | 0000-0002-1825-0097 | Instituto Federal, Campus Exemplo | primeira.autora@exemplo.br",
        "1.  | 0000-0002-1825-0097 | Instituto Federal, Campus Exemplo | primeira.autora@exemplo.br",
    )
    texto = troca_unica(
        texto,
        "2. Segundo Autor | | Instituto Federal, Campus Exemplo | segundo.autor@exemplo.br",
        "2.  | | Instituto Federal, Campus Exemplo | segundo.autor@exemplo.br",
    )
    ok, motivo = roda_erro(
        "erro_sem_nome", tmp, texto, "Bloco AUTORES sem nenhum nome preenchido",
    )
    r.registra(nome, ok, motivo)


def teste_erro_excesso_autores(r, tmp, cache):
    nome = "erro: mais autores do que o modelo comporta"
    texto = EXEMPLO_MD.read_text(encoding="utf-8")
    extras = "\n".join(
        f"{n}. Autor Extra {n} | | Instituto Federal, Campus Exemplo | extra{n}@exemplo.br"
        for n in range(3, 3 + (MAX_AUTORES + 1 - 2))
    )
    texto = troca_unica(
        texto,
        "2. Segundo Autor | | Instituto Federal, Campus Exemplo | segundo.autor@exemplo.br",
        "2. Segundo Autor | | Instituto Federal, Campus Exemplo | segundo.autor@exemplo.br\n" + extras,
    )
    total = MAX_AUTORES + 1
    ok, motivo = roda_erro(
        "erro_excesso_autores", tmp, texto,
        f"O modelo comporta {MAX_AUTORES} autores, o bloco tem {total}",
    )
    r.registra(nome, ok, motivo)


def teste_erro_doi_invalido(r, tmp, cache):
    nome = "erro: DOI em formato invalido"
    texto = EXEMPLO_MD.read_text(encoding="utf-8")
    texto = troca_unica(
        texto,
        "**DOI:** https://doi.org/10.5281/zenodo.1234567",
        "**DOI:** 10.55/algo",
    )
    ok, motivo = roda_erro(
        "erro_doi_invalido", tmp, texto, "DOI em formato inesperado",
    )
    r.registra(nome, ok, motivo)


def teste_erro_modelo_inexistente(r, tmp, cache):
    nome = "erro: modelo inexistente em -m"
    md = copia_exemplo(tmp / "modelo_inexistente")
    modelo_falso = tmp / "nao_existe.docx"
    codigo, saida, erro = roda_cli(["-m", str(modelo_falso), str(md)])
    linhas_erro = [l for l in erro.splitlines() if l.startswith("ERRO:")]
    ok = codigo == 1 and any("nao encontrado" in l for l in linhas_erro)
    motivo = "" if ok else f"codigo={codigo}, stderr={erro!r}"
    r.registra(nome, ok, motivo)


def teste_ida_volta_modelo_reprova_checagem_15(r, tmp, cache):
    nome = "ida e volta do modelo reprova so na checagem 15"
    # referencia.md reproduz o texto do proprio modelo, entao a checagem 15,
    # que reprova quando o texto de exemplo do modelo sobrevive no docx, tem que reprovar.
    codigo, saida, erro = roda_cli([
        str(RAIZ / "modelos/simeca-vii/referencia.md"),
        "-m", str(MODELO_DOCX),
        "-o", str(tmp / "referencia.docx"),
    ])
    ok = (
        codigo == 1
        and "Verificacao: 17 de 18 checagens OK" in saida
        and re.search(r"\[FALHA\] 15\.", saida) is not None
    )
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


def teste_sobrescreve_saida_existente(r, tmp, cache):
    nome = "escreve por cima de uma saida ja existente, sem pedir nada"
    md = copia_exemplo(tmp / "sobrescreve")
    saida = tmp / "sobrescreve" / "artigo_final.docx"
    argv = ["-m", str(MODELO_DOCX), "-o", str(saida), str(md)]
    codigo1, saida1, erro1 = roda_cli(argv)
    codigo2, saida2, erro2 = roda_cli(argv)
    ok = codigo1 == 0 and codigo2 == 0 and saida.exists()
    motivo = "" if ok else (
        f"codigo1={codigo1}, codigo2={codigo2}, erro1={erro1!r}, erro2={erro2!r}"
    )
    r.registra(nome, ok, motivo)


def teste_figura_svg(r, tmp, cache):
    nome = "figura em svg entra vetorial, com o png de reserva"
    texto = EXEMPLO_MD.read_text(encoding="utf-8").replace(
        "figuras/exemplo.png", "figuras/exemplo.svg"
    )
    md = copia_exemplo(tmp / "svg", texto)
    codigo, saida, erro = roda_cli(["-m", str(MODELO_DOCX), str(md)])
    docx = md.with_suffix(".docx")
    tem_svg = tem_blip = False
    if docx.exists():
        with zipfile.ZipFile(docx) as z:
            nomes = z.namelist()
            doc = z.read("word/document.xml").decode("utf-8")
        tem_svg = "word/media/figura1.svg" in nomes and "word/media/figura1.png" in nomes
        tem_blip = "svgBlip" in doc
    ok = (
        codigo == 0
        and "Verificacao: 18 de 18 checagens OK" in saida
        and tem_svg
        and tem_blip
    )
    motivo = "" if ok else (
        f"codigo={codigo}, media_svg={tem_svg}, svgBlip={tem_blip}, erro={erro!r}"
    )
    r.registra(nome, ok, motivo)


def teste_erro_svg_sem_png(r, tmp, cache):
    nome = "erro: figura em svg sem o png de reserva ao lado"
    texto = EXEMPLO_MD.read_text(encoding="utf-8").replace(
        "figuras/exemplo.png", "figuras/exemplo.svg"
    )
    md = copia_exemplo(tmp / "svg_sem_png", texto)
    (md.parent / "figuras" / "exemplo.png").unlink()
    codigo, saida, erro = roda_cli(["-m", str(MODELO_DOCX), str(md)])
    ok = codigo != 0 and "PNG de reserva" in (erro + saida)
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


def teste_erro_svg_malformado(r, tmp, cache):
    nome = "erro: figura em svg com xml malformado"
    texto = EXEMPLO_MD.read_text(encoding="utf-8").replace(
        "figuras/exemplo.png", "figuras/exemplo.svg"
    )
    md = copia_exemplo(tmp / "svg_malformado", texto)
    svg = md.parent / "figuras" / "exemplo.svg"
    # Hifen duplo dentro de comentario, que XML nao aceita.
    svg.write_text(
        svg.read_text(encoding="utf-8").replace(
            "reserva.", "reserva, exportado com --export-width=2400."
        ),
        encoding="utf-8",
    )
    codigo, saida, erro = roda_cli(["-m", str(MODELO_DOCX), str(md)])
    ok = codigo != 0 and "SVG malformado" in (erro + saida)
    motivo = "" if ok else f"codigo={codigo}, saida={saida!r}, erro={erro!r}"
    r.registra(nome, ok, motivo)


TESTES = [
    teste_caminho_feliz,
    teste_figura_svg,
    teste_erro_svg_malformado,
    teste_erro_svg_sem_png,
    teste_sem_figuras,
    teste_verifica,
    teste_aviso_orcid,
    teste_erro_campos_autor,
    teste_erro_orcid_invalido,
    teste_erro_sem_nome,
    teste_erro_excesso_autores,
    teste_erro_doi_invalido,
    teste_erro_modelo_inexistente,
    teste_ida_volta_modelo_reprova_checagem_15,
    teste_sobrescreve_saida_existente,
]


def main_testes():
    r = Resultado()
    cache = {}
    with tempfile.TemporaryDirectory(prefix="simeca_md_testes_") as tmp_str:
        tmp = Path(tmp_str)
        for teste in TESTES:
            teste(r, tmp, cache)
    print(f"{len(r.nomes_ok)} de {r.total()} testes OK")
    return 0 if not r.nomes_falha else 1


if __name__ == "__main__":
    sys.exit(main_testes())
