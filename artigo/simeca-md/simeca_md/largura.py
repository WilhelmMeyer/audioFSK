"""Estimativa da largura ocupada por uma equacao OMML.

Nao ha motor de layout aqui, entao a largura sai de uma soma de larguras
medias por glifo, com as construcoes de matematica tratadas caso a caso
(fracao empilha, expoente reduz, delimitador acrescenta). Serve para avisar
que a equacao passa da coluna, nao para posicionar nada.
"""

from xml.etree import ElementTree as ET

M_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"

TWIPS_POR_PT = 20
TWIPS_POR_MM = 56.7

GLIFO_ESTREITO = "iljft.,;:'|!()[]"
GLIFO_LARGO = "mwMW"
GLIFO_OPERADOR = "+-=<>−±×"

SEM_LARGURA = (
    "dPr", "fPr", "radPr", "naryPr", "ctrlPr", "rPr", "sSupPr", "sSubPr",
    "sSubSupPr", "argPr", "funcPr", "barPr", "accPr", "groupChrPr", "limLowPr",
    "limUppPr", "mPr", "eqArrPr", "boxPr", "borderBoxPr", "phantPr",
)


def largura_texto_em(texto):
    total = 0.0
    for c in texto:
        if c in GLIFO_ESTREITO:
            total += 0.30
        elif c in GLIFO_LARGO:
            total += 0.90
        elif c in GLIFO_OPERADOR:
            total += 0.85
        elif c.isspace():
            total += 0.28
        elif c.isupper():
            total += 0.68
        else:
            total += 0.52
    return total


def largura_omath_em(node):
    tag = node.tag.replace(M_NS, "")

    def filho(nome):
        e = node.find(M_NS + nome)
        return largura_omath_em(e) if e is not None else 0.0

    if tag == "t":
        return largura_texto_em(node.text or "")
    if tag in SEM_LARGURA:
        return 0.0
    if tag == "f":
        return max(filho("num"), filho("den")) + 0.5
    if tag == "sSup":
        return filho("e") + 0.7 * filho("sup")
    if tag == "sSub":
        return filho("e") + 0.7 * filho("sub")
    if tag == "sSubSup":
        return filho("e") + 0.7 * max(filho("sub"), filho("sup"))
    if tag == "rad":
        return 0.8 + filho("e")
    if tag == "d":
        return 1.0 + sum(largura_omath_em(c) for c in node)
    if tag == "nary":
        return 1.2 + 0.7 * (filho("sub") + filho("sup")) + filho("e")
    if tag in ("eqArr", "m"):
        linhas = [largura_omath_em(c) for c in node
                  if c.tag.replace(M_NS, "") not in SEM_LARGURA]
        return max(linhas) if linhas else 0.0
    return sum(largura_omath_em(c) for c in node)


def largura_omath_twips(omath_xml, fonte_pt):
    envelope = (
        '<raiz xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"{omath_xml}</raiz>"
    )
    em = largura_omath_em(ET.fromstring(envelope))
    return round(em * fonte_pt * TWIPS_POR_PT)


def twips_para_mm(twips):
    return twips / TWIPS_POR_MM
