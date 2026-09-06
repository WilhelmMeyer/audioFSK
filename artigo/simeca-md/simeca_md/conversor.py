"""Conversao do markdown em word/document.xml, no formato do modelo.

O markdown aceito e um subconjunto: titulo, secoes, paragrafo, lista, tabela,
figura, equacao de display e referencias, mais os blocos de autores e DOI do
bloco de titulo. O que o modelo define (estilos, numeracao, geometria) vem do
descritor, nunca daqui.
"""

import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree
from pathlib import Path

from . import pandoc as ferramenta_pandoc
from .modelo import CAMINHO_DOC, CAMINHO_RELS, CAMINHO_TIPOS

REL_ID_BASE = 9000
SVG_REL_ID_BASE = 9200
# uri fixa da extensao de imagem vetorial do DrawingML
URI_EXT_SVG = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
ORCID_REL_ID_BASE = 9500
DOC_PR_ID_BASE = 990000

ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")

TOKEN_RE = re.compile(r"\*\*(?P<bold>.+?)\*\*|\*(?P<italic>.+?)\*|\$(?P<math>[^$]+?)\$")
DISPLAY_EQ_RE = re.compile(r"^\$\$(.*)\$\$$")
TAG_RE = re.compile(r"\\tag\{(\d+)\}\s*$")
LEGENDA_RE = re.compile(r"^(Figura|Tabela|Quadro)\s+(\d+)\s*-\s+")

# A ordem dos filhos de w:pPr e fixa no schema: w:spacing antes de w:ind.
SEM_ESPACO_ANTES = '<w:spacing w:before="0" w:after="0"/>'
SEM_RECUO_LISTA = SEM_ESPACO_ANTES + '<w:ind w:left="0" w:firstLine="0"/>'
RECUO_MARCADOR = SEM_ESPACO_ANTES + '<w:ind w:left="227" w:hanging="227"/>'


class Estado:
    """Estado de uma conversao: modelo, equacoes, figuras e avisos."""

    def __init__(self, modelo, base_md, com_figuras=True, modo_pandoc="auto"):
        self.modelo = modelo
        self.base_md = Path(base_md).resolve()
        self.com_figuras = com_figuras
        self.modo_pandoc = modo_pandoc
        self.math = {}
        self.figuras = {}
        self.orcid_rels = []
        self.avisos = []


# ---------------------------------------------------------------------------
# Utilidades de escrita de XML
# ---------------------------------------------------------------------------

def escapa(texto):
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def texto_simples(p_xml):
    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p_xml, re.S))


def run(texto, negrito=False, italico=False):
    if texto == "":
        return ""
    preserva = ' xml:space="preserve"' if (texto[:1].isspace() or texto[-1:].isspace()) else ""
    rpr = ""
    if negrito or italico:
        dentro = ("<w:b/>" if negrito else "") + ("<w:i/>" if italico else "")
        rpr = f"<w:rPr>{dentro}</w:rPr>"
    return f"<w:r>{rpr}<w:t{preserva}>{escapa(texto)}</w:t></w:r>"


def aplica_tamanho(xml, meia_pt):
    xml = re.sub(
        r"<w:rPr>(.*?)</w:rPr>",
        lambda m: f'<w:rPr>{m.group(1)}<w:sz w:val="{meia_pt}"/><w:szCs w:val="{meia_pt}"/></w:rPr>',
        xml, flags=re.S,
    )
    xml = re.sub(
        r"<w:r>(?!<w:rPr>)(<w:t)",
        rf'<w:r><w:rPr><w:sz w:val="{meia_pt}"/><w:szCs w:val="{meia_pt}"/></w:rPr>\1',
        xml,
    )
    return xml


def omath(est, latex):
    if latex not in est.math:
        raise RuntimeError(f"LaTeX nao esta no cache de equacoes: {latex!r}")
    return est.math[latex]


def inline(est, texto):
    partes = []
    pos = 0
    for m in TOKEN_RE.finditer(texto):
        if m.start() > pos:
            partes.append(run(texto[pos:m.start()]))
        if m.group("bold") is not None:
            partes.append(run(m.group("bold"), negrito=True))
        elif m.group("italic") is not None:
            partes.append(run(m.group("italic"), italico=True))
        elif m.group("math") is not None:
            partes.append(omath(est, m.group("math")))
        pos = m.end()
    if pos < len(texto):
        partes.append(run(texto[pos:]))
    return "".join(partes)


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def dimensoes_png(data):
    if data[12:16] != b"IHDR":
        raise RuntimeError("PNG sem bloco IHDR no lugar esperado")
    return struct.unpack(">II", data[16:24])


def dimensoes_jpeg(data):
    i = 2
    n = len(data)
    while i < n - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marcador = data[i + 1]
        if marcador in (0xD8, 0xD9, 0x01) or 0xD0 <= marcador <= 0xD7:
            i += 2
            continue
        if i + 4 > n:
            break
        tamanho = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marcador in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            altura, largura = struct.unpack(">HH", data[i + 5:i + 9])
            return largura, altura
        i += 2 + tamanho
    raise RuntimeError("JPEG sem marcador SOF")


UNIDADE_SVG = {"px": 1.0, "pt": 96 / 72, "pc": 16.0, "mm": 96 / 25.4,
               "cm": 96 / 2.54, "in": 96.0}


def _comprimento_svg(texto):
    """Comprimento do SVG em px, ou None se for relativo (porcentagem)."""
    m = re.match(r"^\s*([0-9.]+)\s*([a-z%]*)\s*$", texto)
    if m is None or m.group(2) == "%":
        return None
    return float(m.group(1)) * UNIDADE_SVG.get(m.group(2) or "px", 1.0)


def confere_svg(caminho, data):
    """SVG malformado nao para o inkscape, que recupera do erro, mas o
    LibreOffice desiste e deixa a figura em branco no PDF sem dizer nada. O
    caso mais facil de cometer e o hifen duplo dentro de comentario, que um
    comando de exportacao anotado no arquivo traz de brinde."""
    try:
        ElementTree.fromstring(data)
    except ElementTree.ParseError as e:
        raise RuntimeError(
            f"SVG malformado em {caminho.name}: {e}. Um leitor tolerante ainda "
            "abre, mas o LibreOffice deixa a figura em branco. Atencao ao hifen "
            "duplo dentro de comentario, que XML nao aceita."
        )


def dimensoes_svg(data):
    """Dimensoes nominais do SVG, do width/height ou, na falta, do viewBox.

    Servem so para a razao de aspecto: no docx o SVG e reescalado para a
    largura da coluna e rasterizado na resolucao do visualizador."""
    cabecalho = data[:4096].decode("utf-8", "replace")
    m = re.search(r"<svg\b[^>]*>", cabecalho, re.S)
    if m is None:
        raise RuntimeError("SVG sem elemento <svg> no inicio do arquivo")
    tag = m.group(0)
    atr = dict(re.findall(r'([a-zA-Z:]+)\s*=\s*"([^"]*)"', tag))
    largura = _comprimento_svg(atr.get("width", ""))
    altura = _comprimento_svg(atr.get("height", ""))
    if largura and altura:
        return largura, altura
    caixa = atr.get("viewBox", "").replace(",", " ").split()
    if len(caixa) == 4:
        return float(caixa[2]), float(caixa[3])
    raise RuntimeError("SVG sem width/height nem viewBox utilizaveis")


def dimensoes_imagem(caminho):
    data = caminho.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return dimensoes_png(data)
    if data[:2] == b"\xff\xd8":
        return dimensoes_jpeg(data)
    if caminho.suffix.lower() == ".svg":
        return dimensoes_svg(data)
    raise RuntimeError(f"Formato de imagem nao suportado: {caminho.name}")


def escala_para_coluna(modelo, largura_px, altura_px, escala=1.0):
    cx = round(modelo.largura_coluna_emu * escala)
    cy = round(cx * altura_px / largura_px)
    if cy > modelo.altura_max_emu:
        cy = modelo.altura_max_emu
        cx = round(cy * largura_px / altura_px)
    return cx, cy


def registra_figura(est, caminho_rel, escala=1.0):
    if caminho_rel in est.figuras:
        return est.figuras[caminho_rel]
    origem = (est.base_md.parent / caminho_rel).resolve()
    if not origem.exists():
        raise RuntimeError(f"Imagem da figura nao encontrada: {caminho_rel}")
    largura_px, altura_px = dimensoes_imagem(origem)
    cx, cy = escala_para_coluna(est.modelo, largura_px, altura_px, escala)
    indice = len(est.figuras) + 1
    vetorial = origem.suffix.lower() == ".svg"
    if vetorial:
        confere_svg(origem, origem.read_bytes())
        # O Word so mostra o SVG a partir do 2016; versoes anteriores e boa
        # parte dos leitores caem no PNG irmao, que por isso e obrigatorio.
        reserva = origem.with_suffix(".png")
        if not reserva.exists():
            raise RuntimeError(
                f"Figura em SVG sem o PNG de reserva ao lado: {reserva.name}. "
                f"Gere com: inkscape {origem.name} -o {reserva.name} "
                "--export-background=white --export-width=2400"
            )
    else:
        reserva = origem
    dados = {
        "origem": reserva,
        "origem_svg": origem if vetorial else None,
        "rel_id": f"rId{REL_ID_BASE + indice}",
        "rel_id_svg": f"rId{SVG_REL_ID_BASE + indice}" if vetorial else None,
        "media": f"word/media/figura{indice}{reserva.suffix.lower()}",
        "media_svg": f"word/media/figura{indice}.svg" if vetorial else None,
        "doc_pr_id": DOC_PR_ID_BASE + indice,
        "cx": cx,
        "cy": cy,
    }
    est.figuras[caminho_rel] = dados
    return dados


def blip_da_figura(f):
    """Blip da imagem. Em figura vetorial o SVG vai na extensao do blip e o
    PNG fica como reserva, que e como o Word grava as proprias."""
    if not f["origem_svg"]:
        return f'<a:blip r:embed="{f["rel_id"]}"/>'
    ns_svg = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
    return (
        f'<a:blip r:embed="{f["rel_id"]}"><a:extLst>'
        f'<a:ext uri="{URI_EXT_SVG}">'
        f'<asvg:svgBlip xmlns:asvg="{ns_svg}" r:embed="{f["rel_id_svg"]}"/>'
        '</a:ext></a:extLst></a:blip>'
    )


def render_imagem(est, caminho_rel, escala=1.0):
    f = registra_figura(est, caminho_rel, escala)
    nome = f["origem_svg"].name if f["origem_svg"] else f["origem"].name
    blip = blip_da_figura(f)
    a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    pic_ns = "http://schemas.openxmlformats.org/drawingml/2006/picture"
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{f["cx"]}" cy="{f["cy"]}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{f["doc_pr_id"]}" name="{escapa(nome)}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{a_ns}" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="{a_ns}"><a:graphicData uri="{pic_ns}">'
        f'<pic:pic xmlns:pic="{pic_ns}">'
        f'<pic:nvPicPr><pic:cNvPr id="0" name="{escapa(nome)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill>{blip}<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{f["cx"]}" cy="{f["cy"]}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )


def tipos_com_svg(tipos_xml, est):
    """Declara a extensao svg no [Content_Types].xml se houver figura vetorial
    e o modelo ainda nao a trouxer."""
    if not any(f["origem_svg"] for f in est.figuras.values()):
        return tipos_xml
    texto = tipos_xml.decode("utf-8")
    if re.search(r'<Default\s+Extension="svg"', texto):
        return tipos_xml
    declaracao = '<Default Extension="svg" ContentType="image/svg+xml"/>'
    return texto.replace("</Types>", declaracao + "</Types>").encode("utf-8")


def rels_com_acrescimos(est, rels_xml):
    tipo_img = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    tipo_link = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
    def relacoes(f):
        yield f["rel_id"], f["media"]
        if f["origem_svg"]:
            yield f["rel_id_svg"], f["media_svg"]

    novas = "".join(
        f'<Relationship Id="{rel_id}" Type="{tipo_img}" '
        f'Target="{media.split("word/", 1)[1]}"/>'
        for f in est.figuras.values()
        for rel_id, media in relacoes(f)
    )
    novas += "".join(
        f'<Relationship Id="{rel_id}" Type="{tipo_link}" '
        f'Target="{alvo}" TargetMode="External"/>'
        for rel_id, alvo in est.orcid_rels
    )
    if not novas:
        return rels_xml
    return rels_xml.replace("</Relationships>", novas + "</Relationships>")


# ---------------------------------------------------------------------------
# Parser do markdown
# ---------------------------------------------------------------------------

def tira_comentarios(texto):
    return re.sub(r"<!--.*?-->", "", texto, flags=re.S)


def parse_tabela(linhas):
    def celulas(linha):
        return tuple(c.strip() for c in linha.strip().strip("|").split("|"))

    cabecalho = celulas(linhas[0])
    corpo = [celulas(l) for l in linhas[2:]]
    return cabecalho, corpo


def parse_autores(est, linhas, i, n):
    autores = []
    maximo = est.modelo.max_autores
    while i < n:
        bruta = linhas[i].strip()
        if not bruta:
            if autores:
                break
            i += 1
            continue
        m = re.match(r"^\d+\.\s*(.*)$", bruta)
        if not m:
            break
        campos = [c.strip() for c in m.group(1).split("|")]
        if len(campos) != 4:
            raise RuntimeError(
                f"Linha de autor precisa de 4 campos separados por |: {bruta!r}"
            )
        nome, orcid, filiacao, email = campos
        if not nome:
            if any(campos):
                est.avisos.append(
                    f"Linha de autor sem nome, ignorada, mas tem dado preenchido: {bruta!r}"
                )
            else:
                est.avisos.append(f"Linha de autor vazia, ignorada: {bruta!r}")
        else:
            if orcid and not ORCID_RE.match(orcid):
                raise RuntimeError(f"ORCID em formato inesperado: {orcid!r}")
            autores.append(
                {"nome": nome, "orcid": orcid, "filiacao": filiacao, "email": email}
            )
        i += 1
    if not autores:
        raise RuntimeError("Bloco AUTORES sem nenhum nome preenchido")
    if len(autores) > maximo:
        raise RuntimeError(f"O modelo comporta {maximo} autores, o bloco tem {len(autores)}")
    return autores, i


def parse_markdown(est, texto):
    texto = tira_comentarios(texto)
    linhas = texto.splitlines()
    blocos = []
    em_referencias = False
    legenda_pendente = None
    i = 0
    n = len(linhas)
    while i < n:
        linha = linhas[i].strip()
        if not linha:
            i += 1
            continue

        if em_referencias:
            blocos.append(("reference", linha))
            i += 1
            continue

        if linha.startswith("**DOI:**"):
            blocos.append(("doi", linha[len("**DOI:**"):].strip()))
            i += 1
            continue

        if linha.startswith("**AUTORES:**"):
            autores, i = parse_autores(est, linhas, i + 1, n)
            blocos.append(("autores", autores))
            continue

        if linha.startswith("**PALAVRAS-CHAVE:**"):
            blocos.append(("keywords", linha))
            i += 1
            continue

        if linha.startswith("# "):
            blocos.append(("title", linha[2:].strip()))
            i += 1
            continue

        if linha.startswith("## "):
            titulo = linha[3:].strip()
            if titulo.upper() == "RESUMO":
                i += 1
                while i < n and not linhas[i].strip():
                    i += 1
                blocos.append(("resumo", linhas[i].strip()))
                i += 1
                continue
            if titulo.upper().startswith("REFER"):
                blocos.append(("refheading", titulo))
                em_referencias = True
                i += 1
                continue
            m = re.match(r"^(\d+)\s+(.*)$", titulo)
            blocos.append(("h1num", m.group(2)) if m else ("h1nonum", titulo))
            i += 1
            continue

        if linha.startswith("### "):
            titulo = linha[4:].strip()
            m = re.match(r"^(\d+\.\d+)\s+(.*)$", titulo)
            blocos.append(("h2", m.group(2) if m else titulo))
            i += 1
            continue

        if linha.startswith("!["):
            m = re.match(r'^!\[(.*)\]\((\S+)(?:\s+"([^"]*)")?\)$', linha)
            if not m:
                raise RuntimeError(f"Linha de figura em formato inesperado: {linha!r}")
            legenda = m.group(1).strip()
            if not legenda:
                proxima = linhas[i + 1].strip() if i + 1 < n else ""
                if LEGENDA_RE.match(proxima):
                    legenda = proxima
                    i += 1
                else:
                    raise RuntimeError(
                        f"Figura sem legenda, escreva ![Figura N - texto](caminho): {linha!r}"
                    )
            escala = float(m.group(3)) if m.group(3) else 1.0
            if not 0 < escala <= 1.0:
                raise RuntimeError(f"Escala de figura fora de (0, 1]: {linha!r}")
            blocos.append(("figure", legenda, m.group(2), escala))
            i += 1
            continue

        if linha.startswith("|"):
            linhas_tabela = []
            while i < n and linhas[i].strip().startswith("|"):
                linhas_tabela.append(linhas[i].strip())
                i += 1
            cabecalho, corpo = parse_tabela(linhas_tabela)
            blocos.append(("table", cabecalho, corpo, legenda_pendente))
            legenda_pendente = None
            continue

        m = DISPLAY_EQ_RE.match(linha)
        if m:
            dentro = m.group(1)
            tag = TAG_RE.search(dentro)
            if tag:
                blocos.append(("displayeq", dentro[:tag.start()].rstrip(), tag.group(1)))
            else:
                blocos.append(("displayeq", dentro.strip(), None))
            i += 1
            continue

        if LEGENDA_RE.match(linha):
            proxima = next((l.strip() for l in linhas[i + 1:] if l.strip()), "")
            if proxima.startswith("|"):
                legenda_pendente = linha
            else:
                blocos.append(("legenda", linha))
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s(.*)$", linha)
        if m:
            blocos.append(("listnum", m.group(1), m.group(2)))
            i += 1
            continue

        if linha.startswith("- "):
            blocos.append(("listbullet", linha[2:].strip()))
            i += 1
            continue

        blocos.append(("para", linha))
        i += 1

    return blocos


# ---------------------------------------------------------------------------
# Equacoes (pandoc, uma unica chamada por conversao)
# ---------------------------------------------------------------------------

def coleta_latex(blocos):
    ordem = {}

    def varre(texto):
        for m in TOKEN_RE.finditer(texto):
            if m.group("math") is not None:
                ordem.setdefault(m.group("math"), True)

    for b in blocos:
        tipo = b[0]
        if tipo in ("para", "listbullet", "reference", "h1num", "h1nonum", "h2",
                    "resumo", "keywords", "title", "legenda", "figure"):
            varre(b[1])
        elif tipo == "listnum":
            varre(b[2])
        elif tipo == "table":
            for linha in (b[1],) + tuple(b[2]):
                for celula in linha:
                    varre(celula)
        elif tipo == "displayeq":
            ordem.setdefault(b[1], True)
    return list(ordem.keys())


def converte_latex(lista, modo_pandoc="auto"):
    if not lista:
        return {}
    executavel = ferramenta_pandoc.garante_pandoc(modo_pandoc)
    with tempfile.TemporaryDirectory(prefix="simeca_md_") as tmp:
        tmp = Path(tmp)
        md = tmp / "equacoes.md"
        md.write_text("\n\n".join(f"${l}$" for l in lista), encoding="utf-8")
        docx = tmp / "equacoes.docx"
        proc = subprocess.run(
            [executavel, "-f", "markdown", "-t", "docx", str(md), "-o", str(docx)],
            capture_output=True, text=True, encoding="utf-8",
        )
        if proc.returncode != 0:
            raise RuntimeError(f"pandoc falhou ao converter equacoes:\n{proc.stderr}")
        if re.search(r"[Cc]ould not convert", proc.stderr):
            raise RuntimeError(
                f"pandoc nao converteu alguma equacao para OMML:\n{proc.stderr}"
            )
        with zipfile.ZipFile(docx) as z:
            doc = z.read(CAMINHO_DOC).decode("utf-8")
    blocos = re.findall(r"<m:oMath>.*?</m:oMath>", doc, re.S)
    if len(blocos) != len(lista):
        raise RuntimeError(
            f"{len(lista)} expressoes de LaTeX enviadas ao pandoc, "
            f"{len(blocos)} blocos m:oMath recebidos de volta"
        )
    return dict(zip(lista, blocos))


# ---------------------------------------------------------------------------
# Renderizacao dos blocos
# ---------------------------------------------------------------------------

def render_titulo(est, estilo, texto, extra_ppr=""):
    ppr = f'<w:pPr><w:pStyle w:val="{estilo}"/>{extra_ppr}</w:pPr>'
    return f"<w:p>{ppr}{inline(est, texto)}</w:p>"


def render_legenda(est, texto):
    estilo = est.modelo.estilo("legenda")
    return f'<w:p><w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>{inline(est, texto)}</w:p>'


def render_figura(est, legenda, caminho_rel, escala=1.0):
    imagem = render_imagem(est, caminho_rel, escala) if est.com_figuras else "<w:p></w:p>"
    return imagem + render_legenda(est, legenda)


def larguras_tabela(modelo, cabecalho, corpo):
    """Reparte a largura da coluna entre as colunas da tabela, pelo tamanho
    do maior texto de cada uma."""
    n = len(cabecalho)
    pesos = []
    for j in range(n):
        textos = [cabecalho[j]] + [l[j] for l in corpo if j < len(l)]
        pesos.append(max(max(len(t) for t in textos), 4))
    total = modelo.largura_coluna_twips
    larguras = [round(total * p / sum(pesos)) for p in pesos]
    larguras[-1] += total - sum(larguras)
    return larguras


def render_tabela(est, cabecalho, corpo, legenda):
    modelo = est.modelo
    larguras = larguras_tabela(modelo, cabecalho, corpo)
    estilo = modelo.estilo("tabela_dados")
    tamanho = modelo.fonte_tabela_meia_pt

    def celula(largura, conteudo, jc):
        ppr = (
            f'<w:pPr><w:pStyle w:val="{estilo}"/>'
            '<w:spacing w:before="0" w:after="0"/>'
            f'<w:jc w:val="{jc}"/></w:pPr>'
        )
        conteudo = aplica_tamanho(conteudo, tamanho)
        return (
            f'<w:tc><w:tcPr><w:tcW w:w="{largura}" w:type="dxa"/></w:tcPr>'
            f"<w:p>{ppr}{conteudo}</w:p></w:tc>"
        )

    def alinhamento(j):
        return "left" if j == 0 else "center"

    linhas_xml = ["<w:tr>" + "".join(
        celula(larguras[j], run(cabecalho[j], negrito=True), alinhamento(j))
        for j in range(len(cabecalho))
    ) + "</w:tr>"]
    for linha in corpo:
        linhas_xml.append("<w:tr>" + "".join(
            celula(larguras[j], inline(est, linha[j]) if linha[j] else "", alinhamento(j))
            for j in range(len(cabecalho))
        ) + "</w:tr>")

    tblpr = (
        f'<w:tblPr><w:tblW w:w="{sum(larguras)}" w:type="dxa"/><w:jc w:val="center"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="7F7F7F"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="7F7F7F"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" '
        'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
    )
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{l}"/>' for l in larguras) + "</w:tblGrid>"
    tbl = f"<w:tbl>{tblpr}{grid}" + "".join(linhas_xml) + "</w:tbl>"
    legenda_xml = render_legenda(est, legenda) if legenda else ""
    return legenda_xml + tbl


def render_equacao(est, latex, numero):
    modelo = est.modelo
    largura_eq = modelo.largura_celula_eq_twips
    largura_num = modelo.largura_numero_eq_twips
    celula_eq = (
        f'<w:tc><w:tcPr><w:tcW w:w="{largura_eq}" w:type="dxa"/></w:tcPr>'
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>'
        f'{omath(est, latex)}</m:oMathPara></w:p></w:tc>'
    )
    celula_num = (
        f'<w:tc><w:tcPr><w:tcW w:w="{largura_num}" w:type="dxa"/>'
        '<w:vAlign w:val="center"/></w:tcPr>'
        '<w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
        f'{run(f"({numero})") if numero else ""}</w:p></w:tc>'
    )
    sem_borda = "".join(
        f'<w:{lado} w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        for lado in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    tblpr = (
        f'<w:tblPr><w:tblStyle w:val="{modelo.estilo("tabela_grade")}"/>'
        f'<w:tblW w:w="{largura_eq + largura_num}" w:type="dxa"/>'
        f"<w:tblBorders>{sem_borda}</w:tblBorders>"
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" '
        'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
    )
    grid = f'<w:tblGrid><w:gridCol w:w="{largura_eq}"/><w:gridCol w:w="{largura_num}"/></w:tblGrid>'
    return f"<w:tbl>{tblpr}{grid}<w:tr>{celula_eq}{celula_num}</w:tr></w:tbl>"


def render_bloco(est, bloco):
    modelo = est.modelo
    tipo = bloco[0]
    if tipo == "h1num":
        return render_titulo(est, modelo.estilo("titulo_secao"), bloco[1])
    if tipo == "h1nonum":
        return render_titulo(
            est, modelo.estilo("titulo_secao"), bloco[1],
            '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>',
        )
    if tipo == "refheading":
        return render_titulo(
            est, modelo.estilo("titulo_referencias"), bloco[1], '<w:jc w:val="left"/>'
        )
    if tipo == "h2":
        numpr = f'<w:numPr><w:ilvl w:val="1"/><w:numId w:val="{modelo.num_id("secao")}"/></w:numPr>'
        return render_titulo(est, modelo.estilo("subtitulo_secao"), bloco[1], numpr)
    if tipo == "para":
        return f"<w:p>{inline(est, bloco[1])}</w:p>"
    if tipo == "legenda":
        return render_legenda(est, bloco[1])
    if tipo == "listnum":
        ppr = f'<w:pPr><w:pStyle w:val="{modelo.estilo("lista")}"/>{SEM_RECUO_LISTA}</w:pPr>'
        return f"<w:p>{ppr}{inline(est, bloco[1] + '. ' + bloco[2])}</w:p>"
    if tipo == "listbullet":
        ppr = (
            f'<w:pPr><w:pStyle w:val="{modelo.estilo("lista")}"/>'
            f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{modelo.num_id("marcador")}"/></w:numPr>'
            f"{RECUO_MARCADOR}</w:pPr>"
        )
        return f"<w:p>{ppr}{inline(est, bloco[1])}</w:p>"
    if tipo == "reference":
        return f'<w:p><w:pPr><w:pStyle w:val="{modelo.estilo("referencia")}"/></w:pPr>{inline(est, bloco[1])}</w:p>'
    if tipo == "figure":
        return render_figura(est, bloco[1], bloco[2], bloco[3])
    if tipo == "table":
        return render_tabela(est, bloco[1], bloco[2], bloco[3])
    if tipo == "displayeq":
        return render_equacao(est, bloco[1], bloco[2])
    raise RuntimeError(f"Bloco desconhecido: {bloco!r}")


# ---------------------------------------------------------------------------
# Preenchimento do bloco de titulo
# ---------------------------------------------------------------------------

def substitui_paragrafo(xml, ini, fim, conteudo):
    antigo = xml[ini:fim]
    ppr = re.search(r"(<w:pPr>.*?</w:pPr>)", antigo, re.S)
    return xml[:ini] + f"<w:p>{ppr.group(1) if ppr else ''}{conteudo}</w:p>" + xml[fim:]


def paragrafo_com_ppr(antigo, conteudo):
    """Reescreve o paragrafo mantendo o w:pPr que ele ja tinha."""
    ppr = re.search(r"(<w:pPr>.*?</w:pPr>)", antigo, re.S)
    return f"<w:p>{ppr.group(1) if ppr else ''}{conteudo}</w:p>"


def icone_orcid(est, p_xml, orcid):
    """Paragrafo do icone: com link para o ORCID, ou sem o icone."""
    imagem = next(
        (m for m in re.finditer(r"<w:r\b[^>]*>.*?</w:r>", p_xml, re.S)
         if "<w:drawing>" in m.group(0)),
        None,
    )
    if imagem is None:
        raise RuntimeError("Icone de ORCID nao encontrado no paragrafo do autor")
    if not orcid:
        return p_xml[:imagem.start()] + p_xml[imagem.end():]
    rel_id = f"rId{ORCID_REL_ID_BASE + len(est.orcid_rels) + 1}"
    est.orcid_rels.append((rel_id, f"https://orcid.org/{orcid}"))
    return (
        p_xml[:imagem.start()]
        + f'<w:hyperlink r:id="{rel_id}">{imagem.group(0)}</w:hyperlink>'
        + p_xml[imagem.end():]
    )


def identificador_doi(doi):
    ident = doi.strip()
    for prefixo in ("https://doi.org/", "http://doi.org/", "doi:"):
        if ident.lower().startswith(prefixo):
            return ident[len(prefixo):]
    return ident


def aplica_doi(est, cab, doi):
    ident = identificador_doi(doi)
    if not ident:
        return cab
    if not DOI_RE.match(ident):
        raise RuntimeError(f"DOI em formato inesperado: {doi!r}")
    ini, fim = est.modelo.acha(cab, "doi")
    return substitui_paragrafo(cab, ini, fim, run(" ") + run(f"https://doi.org/{ident}"))


def aplica_autores(est, cab, autores):
    """Preenche as linhas de autor do modelo e apaga as que sobrarem.

    Todas as posicoes sao localizadas antes de qualquer escrita, e as edicoes
    sao aplicadas de baixo para cima. Assim o texto ja escrito nunca e
    reprocurado, nem quando o dado do autor parece marcador do modelo, e a
    primeira linha da tabela, que faz a mesclagem vertical do resumo, nunca e
    tocada.
    """
    modelo = est.modelo
    nomes = modelo.acha_numerado(cab, "autor_nome")
    filiacoes = modelo.acha_numerado(cab, "autor_filiacao")
    faltando = sorted(set(nomes) - set(filiacoes)) + sorted(set(filiacoes) - set(nomes))
    if faltando:
        raise RuntimeError(
            f"Modelo com linha de autor incompleta, sem par nome e filiacao: {faltando}"
        )
    if len(autores) > len(nomes):
        raise RuntimeError(
            f"O modelo comporta {len(nomes)} autores, o markdown tem {len(autores)}"
        )

    edicoes = []
    for numero in sorted(nomes):
        ini_nome, fim_nome = nomes[numero]
        ini_fil, fim_fil = filiacoes[numero]
        if numero > len(autores):
            edicoes.append((*modelo.acha_linha(cab, ini_nome), None))
            edicoes.append((ini_fil, fim_fil, None))
            continue

        autor = autores[numero - 1]
        ini_icone, fim_icone = modelo.acha_icone_anterior(cab, ini_nome)
        edicoes.append((ini_icone, fim_icone, icone_orcid(est, cab[ini_icone:fim_icone], autor["orcid"])))
        edicoes.append((ini_nome, fim_nome, paragrafo_com_ppr(
            cab[ini_nome:fim_nome], run(f"{autor['nome']} [{numero}]", negrito=True)
        )))
        partes = []
        if autor["filiacao"]:
            partes.append(f"{autor['filiacao']}.")
        if autor["email"]:
            partes.append(f"E-mail: {autor['email']}.")
        nota = (f"[{numero}] " + " ".join(partes)).strip()
        edicoes.append((ini_fil, fim_fil, paragrafo_com_ppr(
            cab[ini_fil:fim_fil], inline(est, nota)
        )))

    for inicio, final, texto in sorted(edicoes, reverse=True):
        cab = cab[:inicio] + (texto or "") + cab[final:]
    return cab


def aplica_bloco_titulo(est, cab, titulo, resumo, palavras_chave):
    modelo = est.modelo

    ini, fim = modelo.acha(cab, "titulo")
    cab = substitui_paragrafo(cab, ini, fim, inline(est, titulo.upper()))

    ini, fim = modelo.acha(cab, "resumo")
    rotulo = texto_simples(cab[ini:fim]).split(":", 1)[0] + ":"
    conteudo = (
        f"<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>{escapa(rotulo)}</w:t></w:r>"
        '<w:r><w:t xml:space="preserve"> </w:t></w:r>'
        + inline(est, resumo)
    )
    cab = substitui_paragrafo(cab, ini, fim, conteudo)

    ini, fim = modelo.acha(cab, "palavras_chave")
    return substitui_paragrafo(cab, ini, fim, inline(est, palavras_chave))


# ---------------------------------------------------------------------------
# Montagem do docx
# ---------------------------------------------------------------------------

CABECALHO_BLOCOS = ("title", "resumo", "keywords", "autores", "doi")


def monta_documento(est, md_texto):
    blocos = parse_markdown(est, md_texto)
    est.math = converte_latex(coleta_latex(blocos), est.modo_pandoc)

    def unico(tipo, obrigatorio=True):
        b = next((b for b in blocos if b[0] == tipo), None)
        if b is None and obrigatorio:
            raise RuntimeError(f"Markdown sem bloco de {tipo}")
        return b

    cab, rodape = est.modelo.separa_cabecalho()
    cab = aplica_bloco_titulo(
        est, cab, unico("title")[1], unico("resumo")[1], unico("keywords")[1]
    )
    cab = aplica_autores(est, cab, unico("autores")[1])
    doi = unico("doi", obrigatorio=False)
    if doi is not None:
        cab = aplica_doi(est, cab, doi[1])

    corpo = "".join(
        render_bloco(est, b) for b in blocos if b[0] not in CABECALHO_BLOCOS
    )
    return cab + corpo + rodape, blocos


def monta(md, modelo, saida, com_figuras=True, modo_pandoc="auto"):
    """Gera o docx a partir do markdown e do modelo. Devolve o Estado."""
    md = Path(md).resolve()
    if not md.exists():
        raise RuntimeError(f"Markdown nao encontrado: {md}")
    saida = Path(saida).resolve()

    est = Estado(modelo, md, com_figuras, modo_pandoc)
    doc_xml, _ = monta_documento(est, md.read_text(encoding="utf-8"))
    rels_xml = rels_com_acrescimos(est, modelo.rels_xml)
    extras = []
    for f in est.figuras.values():
        extras.append((f["media"], f["origem"].read_bytes()))
        if f["origem_svg"]:
            extras.append((f["media_svg"], f["origem_svg"].read_bytes()))

    try:
        zsaida = zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED)
    except PermissionError:
        raise RuntimeError(
            f"{saida.name} esta bloqueado, provavelmente aberto no Word. "
            "Feche o arquivo e rode de novo."
        )
    with zsaida:
        for nome in modelo.nomes:
            if nome == CAMINHO_DOC:
                dados = doc_xml.encode("utf-8")
            elif nome == CAMINHO_RELS:
                dados = rels_xml.encode("utf-8")
            elif nome == CAMINHO_TIPOS:
                dados = tipos_com_svg(modelo.conteudos[nome], est)
            else:
                dados = modelo.conteudos[nome]
            origem = modelo.infos[nome]
            info = zipfile.ZipInfo(nome, date_time=origem.date_time)
            info.compress_type = origem.compress_type
            info.external_attr = origem.external_attr
            zsaida.writestr(info, dados)
        referencia = modelo.infos[CAMINHO_DOC]
        for nome, dados in extras:
            info = zipfile.ZipInfo(nome, date_time=referencia.date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = referencia.external_attr
            zsaida.writestr(info, dados)
    return est
