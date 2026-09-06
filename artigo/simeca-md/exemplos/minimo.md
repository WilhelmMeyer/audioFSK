# Título do artigo em uma linha, que o conversor coloca em maiúsculas no docx

**AUTORES:**

<!--
Um autor por linha, campos separados por |, nesta ordem: nome | ORCID | filiacao | e-mail. Linha com nome vazio nao entra. O maximo e o que o modelo comporta, declarado em max_autores no descritor. O conversor conta as linhas preenchidas, apaga as linhas de autor sobrando na tabela do modelo e as notas de filiacao correspondentes. ORCID no formato 0000-0000-0000-0000 vira link no icone; ORCID vazio remove o icone daquela linha.
-->

1. Primeira Autora | 0000-0002-1825-0097 | Instituto Federal, Campus Exemplo | primeira.autora@exemplo.br
2. Segundo Autor | | Instituto Federal, Campus Exemplo | segundo.autor@exemplo.br

**DOI:** https://doi.org/10.5281/zenodo.1234567

## RESUMO

Este exemplo existe para exercitar o conversor de ponta a ponta: bloco de título, autores, resumo, palavras-chave, seções numeradas, lista, tabela, figura, equação de display e referências.

**PALAVRAS-CHAVE:** conversor, docx, markdown, OOXML.

## 1 INTRODUÇÃO

Parágrafo comum, com *termo em itálico*, **trecho em negrito** e uma equação no meio da linha, $\omega_0^2 = mgd/I$, que o pandoc converte em OMML.

### 1.1 Subseção

Itens numerados aparecem na margem do texto:

1. primeiro item;
2. segundo item.

Itens com marcador:

- um item;
- outro item.

## 2 DESENVOLVIMENTO

A equação de display sai centralizada, com o número à direita:

$$J\dot{\omega}_r = \frac{K_t}{R}\left(uV_s - K_v\omega_r\right) - T_r \tag{1}$$

![Figura 1 - Imagem de teste, gerada em código, ocupando a coluna inteira.](figuras/exemplo.png)

Tabela 1 - Parâmetros do exemplo.

| Grandeza | Símbolo | Valor |
| --- | --- | --- |
| Massa desbalanceada | $m$ | 0,42 kg |
| Distância ao pivô | $d$ | 0,15 m |
| Inércia da haste | $I$ | 0,031 kg m² |

## REFERÊNCIAS

SOBRENOME, Nome. Título do trabalho de referência. Cidade: Editora, 2026.
