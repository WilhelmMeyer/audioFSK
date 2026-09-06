"""Conferencia do docx gerado, contra o modelo e contra o markdown.

Cada checagem compara o que saiu com o que o markdown pedia ou com o que o
modelo trazia. Falha e defeito no docx, aviso e coisa que o autor ainda tem
que preencher ou decidir.
"""

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from . import conversor
from .largura import largura_omath_twips, twips_para_mm
from .modelo import CAMINHO_DOC, CAMINHO_RELS

LEGENDA_TIPOS = ("Figura", "Tabela", "Quadro")


def texto_dos_runs(doc):
    return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", doc, re.S))


def confere(modelo, md, saida, com_figuras=True):
    """Devolve (resultados, avisos, legendas).

    Resultado e uma tripla (descricao, passou, detalhe).
    """
    resultados = []
    avisos = []

    def check(desc, cond, detalhe=""):
        resultados.append((desc, bool(cond), detalhe))

    saida = Path(saida).resolve()
    if not saida.exists():
        check(f"{saida.name} existe", False, "gere o docx antes de conferir")
        return resultados, avisos, []

    est = conversor.Estado(modelo, md, com_figuras)
    blocos = conversor.parse_markdown(est, Path(md).read_text(encoding="utf-8"))
    avisos.extend(est.avisos)
    for b in blocos:
        if b[0] == "figure" and com_figuras:
            conversor.registra_figura(est, b[2], b[3])

    with zipfile.ZipFile(saida) as z:
        nomes_saida = z.namelist()
        doc = z.read(CAMINHO_DOC).decode("utf-8")
        rels_saida = z.read(CAMINHO_RELS).decode("utf-8")
        extras = [n for n in nomes_saida if n not in modelo.nomes]
        media = {n: z.read(n) for n in extras}
        iguais = all(
            n in nomes_saida and (n in (CAMINHO_DOC, CAMINHO_RELS)
                                  or z.read(n) == modelo.conteudos[n])
            for n in modelo.nomes
        )
        diferentes = [
            n for n in modelo.nomes
            if n not in (CAMINHO_DOC, CAMINHO_RELS)
            and (n not in nomes_saida or z.read(n) != modelo.conteudos[n])
        ]

    cond = nomes_saida[:len(modelo.nomes)] == modelo.nomes and all(
        n.startswith("word/media/") for n in extras
    )
    check("1. entradas do modelo preservadas na ordem, extras so em word/media/", cond,
          "" if cond else f"extras={extras}")
    check("2. todo arquivo exceto document.xml e document.xml.rels identico ao modelo",
          not diferentes, f"diferem: {diferentes}" if diferentes else "")

    try:
        ET.fromstring(doc.encode("utf-8"))
        check("3. document.xml bem formado", True)
    except ET.ParseError as e:
        check("3. document.xml bem formado", False, str(e))

    estilos_docx = set(re.findall(
        r'<w:style\b[^>]*w:styleId="([^"]+)"',
        modelo.conteudos["word/styles.xml"].decode("utf-8"),
    ))
    usados = set(re.findall(r'<w:pStyle w:val="([^"]+)"', doc))
    faltando = usados - estilos_docx
    check("4. todo w:pStyle usado existe no styles.xml do modelo", not faltando,
          f"faltando: {sorted(faltando)}" if faltando else "")

    numbering = modelo.conteudos.get("word/numbering.xml", b"").decode("utf-8")
    num_ids = set(re.findall(r'<w:num w:numId="(\d+)"', numbering))
    usados_num = {n for n in re.findall(r'<w:numId w:val="(\d+)"', doc) if n != "0"}
    faltando_num = usados_num - num_ids
    check("5. todo w:numId usado existe no numbering.xml ou e 0", not faltando_num,
          f"faltando: {sorted(faltando_num)}" if faltando_num else "")

    textos = texto_dos_runs(doc)
    residuos = [t for t in ("$", "\\tag", "**", "<!--", "](") if t in textos]
    check("6. sem marcacao de markdown residual no texto", not residuos,
          f"encontrados: {residuos}" if residuos else "")

    esperado = {
        "titulo_secao_num": sum(1 for b in blocos if b[0] == "h1num"),
        "titulo_secao_sem_num": sum(1 for b in blocos if b[0] == "h1nonum"),
        "subtitulo_secao": sum(1 for b in blocos if b[0] == "h2"),
        "referencia": sum(1 for b in blocos if b[0] == "reference"),
    }
    estilo_h1 = modelo.estilo("titulo_secao")
    h1s = re.findall(rf'<w:pPr><w:pStyle w:val="{estilo_h1}"/>(.*?)</w:pPr>', doc)
    contagem = {
        "titulo_secao_num": sum(1 for b in h1s if 'w:numId w:val="0"' not in b),
        "titulo_secao_sem_num": sum(1 for b in h1s if 'w:numId w:val="0"' in b),
        "subtitulo_secao": doc.count(f'<w:pStyle w:val="{modelo.estilo("subtitulo_secao")}"/>'),
        "referencia": doc.count(f'<w:pStyle w:val="{modelo.estilo("referencia")}"/>'),
    }
    cond = contagem == esperado
    check("7. contagens de estilo batem com o markdown", cond,
          "" if cond else f"docx={contagem}, markdown={esperado}")

    cabecalho, rodape = modelo.separa_cabecalho()
    esperado_sect = len(re.findall(r"<w:sectPr.*?</w:sectPr>", cabecalho, re.S)) + 1
    sect_saida = re.findall(r"<w:sectPr.*?</w:sectPr>", doc, re.S)
    cond = len(sect_saida) == esperado_sect and sect_saida[-1] in rodape
    check("8. quebras de secao do cabecalho do modelo mais a do corpo", cond,
          "" if cond else f"esperado={esperado_sect}, saida={len(sect_saida)}")

    estilo_legenda = modelo.estilo("legenda")
    legenda_re = re.compile(
        rf'<w:p><w:pPr><w:pStyle w:val="{estilo_legenda}"/></w:pPr>(.*?)</w:p>', re.S
    )
    legendas = list(legenda_re.finditer(doc))
    textos_legenda = [texto_dos_runs(m.group(1)) for m in legendas]

    rotulo_re = re.compile(rf"^({'|'.join(LEGENDA_TIPOS)}) (\d+) - ")
    sem_rotulo = [t for t in textos_legenda if not rotulo_re.match(t)]
    numeracao = {}
    for t in textos_legenda:
        m = rotulo_re.match(t)
        if m:
            numeracao.setdefault(m.group(1), []).append(int(m.group(2)))
    fora_de_ordem = {
        tipo: nums for tipo, nums in numeracao.items()
        if nums != list(range(1, len(nums) + 1))
    }
    detalhe = ""
    if sem_rotulo:
        detalhe += f"sem rotulo Tipo N - : {sem_rotulo}"
    if fora_de_ordem:
        detalhe += f" numeracao fora de sequencia: {fora_de_ordem}"
    check("9. toda legenda rotulada e numerada em sequencia por tipo",
          not sem_rotulo and not fora_de_ordem, detalhe.strip())

    corpo = doc.split("</w:tbl>", 1)[-1]
    sem_imagem = []
    for m, t in zip(legendas, textos_legenda):
        if not t.startswith("Figura "):
            continue
        antes = doc[:m.start()]
        ok = antes.endswith("</w:drawing></w:r></w:p>") if com_figuras else antes.endswith("<w:p></w:p>")
        if not ok:
            sem_imagem.append(t[:40])
    check("10. toda legenda de figura precedida pelo paragrafo da imagem",
          not sem_imagem, f"sem imagem antes: {sem_imagem}" if sem_imagem else "")

    soltas = [
        t[:40] for m, t in zip(legendas, textos_legenda)
        if t.startswith("Tabela ") and not doc[m.end():].startswith("<w:tbl>")
    ]
    check("11. toda legenda de tabela seguida pela tabela", not soltas,
          f"sem tabela depois: {soltas}" if soltas else "")

    # Figura vetorial embute dois arquivos, o SVG e o PNG de reserva, e por
    # isso conta dois embeds e dois relationships.
    esperado_figs = sum(
        2 if b[2].lower().endswith(".svg") else 1
        for b in blocos if b[0] == "figure"
    )
    # So os embeds das figuras acrescidas: o modelo traz imagens proprias, com
    # blip e svgBlip iguais aos nossos, e elas nao entram nesta contagem.
    nossos = {
        rel_id
        for f in est.figuras.values()
        for rel_id in (f["rel_id"], f["rel_id_svg"])
        if rel_id
    }
    embeds = [
        e for e in re.findall(r'<a(?:svg)?:(?:blip|svgBlip)\b[^>]*?r:embed="(rId\d+)"', doc)
        if e in nossos
    ]
    rel_alvo = dict(re.findall(r'<Relationship Id="([^"]+)"[^>]*Target="([^"]+)"', rels_saida))
    alvos = {f"word/{rel_alvo[e]}" for e in embeds if e in rel_alvo}
    sem_rel = [e for e in embeds if e not in rel_alvo]
    sem_media = sorted(alvos - set(media))
    orfas = sorted(set(media) - alvos)
    cond = (
        len(embeds) == (esperado_figs if com_figuras else 0)
        and not sem_rel and not sem_media and not orfas
    )
    check("12. cada figura embutida tem relationship e arquivo em word/media/", cond,
          f"embeds={len(embeds)} (esperado {esperado_figs if com_figuras else 0}), "
          f"sem relationship={sem_rel}, sem media={sem_media}, orfas={orfas}")

    cond = modelo.rels_xml.replace("</Relationships>", "") in rels_saida
    check("13. relationships do modelo preservados, so acrescidos os novos", cond,
          "" if cond else "o bloco original de relationships foi alterado")

    if com_figuras:
        divergentes = [
            rel for rel, f in est.figuras.items()
            if media.get(f["media"]) != f["origem"].read_bytes()
            or (f["origem_svg"]
                and media.get(f["media_svg"]) != f["origem_svg"].read_bytes())
        ]
        check("14. imagem embutida identica ao arquivo de origem", not divergentes,
              f"diferem da origem: {divergentes}" if divergentes else "")

    autores = next(b[1] for b in blocos if b[0] == "autores")
    # Texto de exemplo que o modelo traz nos paragrafos do bloco de titulo. Se
    # algum deles sobreviveu inteiro no docx, aquela parte nao foi preenchida.
    exemplos_do_modelo = []
    for papel in ("titulo", "resumo", "palavras_chave"):
        i, f = modelo.acha(cabecalho, papel)
        exemplos_do_modelo.append(conversor.texto_simples(cabecalho[i:f]).strip())
    for papel in ("autor_nome", "autor_filiacao"):
        for i, f in modelo.acha_numerado(cabecalho, papel).values():
            exemplos_do_modelo.append(conversor.texto_simples(cabecalho[i:f]).strip())
    marcadores_do_modelo = [
        t[:40] for t in exemplos_do_modelo if t and t in textos
    ]
    notas = len(re.findall(r"<w:t(?: [^>]*)?>\[\d+\]", doc))
    nomes = len(re.findall(r"<w:t(?: [^>]*)?>[^<]+ \[\d+\]</w:t>", doc))
    cond = not marcadores_do_modelo and notas == len(autores) and nomes == len(autores)
    check(f"15. bloco de titulo preenchido, {len(autores)} autores, sem texto do modelo", cond,
          f"marcadores do modelo ainda presentes={marcadores_do_modelo}, "
          f"notas={notas}, nomes={nomes}")

    for idx, autor in enumerate(autores):
        falta = [
            rotulo for rotulo, campo in
            (("ORCID", "orcid"), ("filiacao", "filiacao"), ("e-mail", "email"))
            if not autor[campo]
        ]
        if falta:
            avisos.append(f"Autor {idx + 1} ({autor['nome']}): falta {', '.join(falta)}")

    com_orcid = sum(1 for a in autores if a["orcid"])
    links = [rel_alvo.get(i) for i in re.findall(r'<w:hyperlink r:id="(rId\d+)">', doc)]
    cond = len(links) == com_orcid and all(
        alvo and alvo.startswith("https://orcid.org/") for alvo in links
    )
    check(f"16. {com_orcid} icone de ORCID com link externo, os demais removidos", cond,
          f"links no docx={links}")

    bloco_doi = next((b for b in blocos if b[0] == "doi"), None)
    if bloco_doi is not None:
        ident = conversor.identificador_doi(bloco_doi[1])
        if ident:
            check(f"17. DOI do markdown no docx ({ident})",
                  f"https://doi.org/{ident}" in textos,
                  "DOI do markdown nao encontrado no docx")
            ini, fim = modelo.acha(modelo.document_xml, "doi")
            doi_modelo = conversor.texto_simples(modelo.document_xml[ini:fim]).strip()
            if ident and ident in doi_modelo:
                avisos.append(
                    f"DOI ainda e o do modelo ({ident}), atualizar **DOI:** no markdown"
                )

    estouros = []
    for cx in re.findall(r'<wp:extent cx="(\d+)"', corpo):
        if int(cx) > modelo.largura_coluna_emu:
            estouros.append(f"figura com cx={cx} EMU, coluna tem {modelo.largura_coluna_emu}")
    for grid in re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", corpo, re.S):
        larguras = [int(g) for g in re.findall(r'<w:gridCol w:w="(\d+)"/>', grid)]
        if sum(larguras) > modelo.largura_coluna_twips:
            estouros.append(
                f"tabela de {sum(larguras)} twips, coluna tem {modelo.largura_coluna_twips}"
            )
    check(f"18. figura e tabela dentro da largura da coluna "
          f"({twips_para_mm(modelo.largura_coluna_twips):.0f} mm)",
          not estouros, "; ".join(estouros))

    limite = modelo.largura_celula_eq_twips
    for tbl in re.findall(r"<w:tbl>.*?</w:tbl>", corpo, re.S):
        eq = re.search(r"<m:oMath>.*?</m:oMath>", tbl, re.S)
        if eq is None or f'<w:gridCol w:w="{limite}"/>' not in tbl:
            continue
        numero = re.search(r"<w:t(?: [^>]*)?>\((\d+)\)</w:t>", tbl)
        rotulo = f"Equacao {numero.group(1)}" if numero else "Equacao sem numero"
        largura = largura_omath_twips(eq.group(0), modelo.fonte_corpo_pt)
        if largura > limite:
            avisos.append(
                f"{rotulo} passa da coluna: cerca de {twips_para_mm(largura):.0f} mm "
                f"contra {twips_para_mm(limite):.0f} mm disponiveis, "
                f"quebrar em duas linhas ou encurtar"
            )

    return resultados, avisos, textos_legenda


def relata(resultados, avisos, resumido=False, legendas=()):
    falhas = [r for r in resultados if not r[1]]
    for desc, passou, detalhe in resultados:
        if resumido and passou:
            continue
        linha = f"[{'OK' if passou else 'FALHA'}] {desc}"
        if detalhe and not passou:
            linha += f"\n       {detalhe}"
        print(linha)
    for aviso in avisos:
        print(f"[AVISO] {aviso}")
    print(f"Verificacao: {len(resultados) - len(falhas)} de {len(resultados)} checagens OK")
    if not resumido and legendas:
        print()
        print("Legendas, na ordem:")
        for t in legendas:
            print(f"  {t}")
    return not falhas
