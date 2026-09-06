"""Leitura do modelo docx e do descritor que diz onde ficam suas partes.

Tudo que e especifico de um modelo (texto marcador dos paragrafos do bloco de
titulo, nomes de estilo, listas de numeracao, geometria da pagina) sai daqui,
lido do arquivo .toml ao lado do docx. O resto do conversor nao conhece
modelo nenhum por dentro.
"""

import re
import tomllib
import zipfile
from pathlib import Path

CAMINHO_DOC = "word/document.xml"
CAMINHO_RELS = "word/_rels/document.xml.rels"
CAMINHO_TIPOS = "[Content_Types].xml"

EMU_POR_TWIP = 635


def texto_simples(p_xml):
    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p_xml, re.S))


def paragrafos(xml_text):
    """Posicoes e texto de cada w:p do trecho, na ordem do documento."""
    saida = []
    for m in re.finditer(r"<w:p\b[^>]*>.*?</w:p>", xml_text, re.S):
        saida.append((m.start(), m.end(), m.group(0)))
    return saida


class Modelo:
    def __init__(self, caminho_docx, caminho_descritor=None):
        self.docx = Path(caminho_docx).resolve()
        if not self.docx.exists():
            raise RuntimeError(f"Modelo nao encontrado: {self.docx}")
        if caminho_descritor is None:
            candidatos = [self.docx.with_suffix(".toml"), self.docx.parent / "modelo.toml"]
            caminho_descritor = next((c for c in candidatos if c.exists()), None)
            if caminho_descritor is None:
                raise RuntimeError(
                    f"Descritor do modelo nao encontrado ao lado de {self.docx.name}, "
                    f"esperado {candidatos[0].name} ou modelo.toml"
                )
        self.descritor = Path(caminho_descritor).resolve()
        self.cfg = tomllib.loads(self.descritor.read_text(encoding="utf-8"))

        with zipfile.ZipFile(self.docx) as z:
            self.nomes = z.namelist()
            self.conteudos = {n: z.read(n) for n in self.nomes}
            self.infos = {n: z.getinfo(n) for n in self.nomes}
        self.document_xml = self.conteudos[CAMINHO_DOC].decode("utf-8")
        self.rels_xml = self.conteudos[CAMINHO_RELS].decode("utf-8")

        self._mede_pagina()

    # -- descritor ----------------------------------------------------------

    @property
    def nome(self):
        return self.cfg.get("nome", self.docx.stem)

    @property
    def max_autores(self):
        return int(self.cfg.get("max_autores", 6))

    def estilo(self, papel):
        try:
            return self.cfg["estilos"][papel]
        except KeyError:
            raise RuntimeError(f"Descritor sem estilos.{papel}")

    def num_id(self, papel):
        try:
            return int(self.cfg["numeracao"][papel])
        except KeyError:
            raise RuntimeError(f"Descritor sem numeracao.{papel}")

    def ancora(self, papel):
        try:
            return re.compile(self.cfg["ancoras"][papel])
        except KeyError:
            raise RuntimeError(f"Descritor sem ancoras.{papel}")

    @property
    def fonte_corpo_pt(self):
        return float(self.cfg["fonte"]["corpo_pt"])

    @property
    def fonte_tabela_meia_pt(self):
        return str(self.cfg["fonte"]["tabela_meia_pt"])

    # -- geometria ----------------------------------------------------------

    def _mede_pagina(self):
        sectprs = re.findall(r"<w:sectPr.*?</w:sectPr>", self.document_xml, re.S)
        if not sectprs:
            raise RuntimeError("Modelo sem w:sectPr, impossivel medir a pagina")
        corpo = sectprs[-1]

        def atributo(padrao, onde, obrigatorio=True):
            m = re.search(padrao, onde)
            if m is None:
                if obrigatorio:
                    raise RuntimeError(f"Modelo sem {padrao} no sectPr do corpo")
                return 0
            return int(m.group(1))

        largura_pagina = atributo(r'<w:pgSz[^>]*\bw:w="(\d+)"', corpo)
        margem_esq = atributo(r'<w:pgMar[^>]*\bw:left="(\d+)"', corpo)
        margem_dir = atributo(r'<w:pgMar[^>]*\bw:right="(\d+)"', corpo)
        colunas = atributo(r'<w:cols[^>]*\bw:num="(\d+)"', corpo, obrigatorio=False) or 1
        espaco = atributo(r'<w:cols[^>]*\bw:space="(\d+)"', corpo, obrigatorio=False)

        util = largura_pagina - margem_esq - margem_dir - espaco * (colunas - 1)
        self.colunas = colunas
        self.largura_coluna_twips = util // colunas
        self.largura_coluna_emu = self.largura_coluna_twips * EMU_POR_TWIP
        self.altura_max_emu = int(self.cfg["figura"]["altura_max_twips"]) * EMU_POR_TWIP
        self.largura_numero_eq_twips = int(self.cfg["equacao"]["largura_numero_twips"])
        self.largura_celula_eq_twips = (
            self.largura_coluna_twips - self.largura_numero_eq_twips
        )

    # -- corte do documento -------------------------------------------------

    def separa_cabecalho(self):
        """Devolve (cabecalho, rodape) do document.xml do modelo.

        O cabecalho vai ate o paragrafo seguinte a tabela do bloco de titulo,
        que carrega o sectPr de uma coluna. O rodape e o sectPr final, de duas
        colunas. Entre os dois entra o corpo gerado a partir do markdown.
        """
        doc = self.document_xml
        fim_tbl = doc.find("</w:tbl>")
        if fim_tbl == -1:
            raise RuntimeError("Tabela do bloco de titulo nao encontrada no modelo")
        fim_tbl += len("</w:tbl>")
        ini_p = doc.find("<w:p", fim_tbl)
        fim_p = doc.find("</w:p>", ini_p) + len("</w:p>")
        cabecalho = doc[:fim_p]

        ini_sect = doc.rfind("<w:sectPr")
        if ini_sect == -1 or ini_sect < fim_p:
            raise RuntimeError("sectPr final nao encontrado no modelo")
        return cabecalho, doc[ini_sect:]

    # -- localizacao de paragrafos por texto marcador -----------------------

    def acha(self, xml_text, papel, ocorrencia=1):
        """Posicao (inicio, fim) do paragrafo cujo texto casa com a ancora."""
        alvo = self.ancora(papel)
        vistos = 0
        for ini, fim, p_xml in paragrafos(xml_text):
            if alvo.search(texto_simples(p_xml)):
                vistos += 1
                if vistos == ocorrencia:
                    return ini, fim
        raise RuntimeError(
            f"Paragrafo de {papel} (ocorrencia {ocorrencia}) nao encontrado no modelo"
        )

    def acha_numerado(self, xml_text, papel, obrigatorio=True):
        """Paragrafos de ancora numerada, indexados pelo numero capturado."""
        alvo = self.ancora(papel)
        achados = {}
        for ini, fim, p_xml in paragrafos(xml_text):
            m = alvo.search(texto_simples(p_xml))
            if m:
                achados[int(m.group(1))] = (ini, fim)
        if not achados and obrigatorio:
            raise RuntimeError(f"Nenhum paragrafo de {papel} encontrado no modelo")
        return achados

    def acha_linha(self, xml_text, posicao):
        """Intervalo da w:tr que contem a posicao dada."""
        ini = xml_text.rfind("<w:tr ", 0, posicao)
        if ini == -1:
            ini = xml_text.rfind("<w:tr>", 0, posicao)
        fim = xml_text.find("</w:tr>", posicao)
        if ini == -1 or fim == -1:
            raise RuntimeError("Linha de tabela nao delimitada no modelo")
        return ini, fim + len("</w:tr>")

    def acha_icone_anterior(self, xml_text, posicao):
        """Paragrafo com imagem imediatamente antes da posicao dada.

        E assim que se acha o icone de ORCID de cada autor, sem depender de
        identificador de paragrafo, que o Word reescreve ao salvar.
        """
        anterior = None
        for ini, fim, p_xml in paragrafos(xml_text):
            if ini >= posicao:
                break
            if "<w:drawing>" in p_xml:
                anterior = (ini, fim)
        if anterior is None:
            raise RuntimeError("Icone de ORCID nao encontrado antes do nome do autor")
        return anterior
