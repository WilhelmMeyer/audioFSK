# Ida e volta do modelo do VII SIMECA

O corpo do `modelo.docx` (o texto de instruções da organização do evento) foi transcrito para `referencia.md`, no dialeto que o conversor aceita, e reconvertido com:

```sh
python3 -m simeca_md modelos/simeca-vii/referencia.md -m modelos/simeca-vii/modelo.docx -o /tmp/referencia.docx
```

Resultado da verificação: **18 de 18 checagens OK**, com um aviso, o DOI ainda é o do próprio modelo (`10.5281/zenodo.XXX`), que é o dado fictício que o modelo traz.

As duas figuras do corpo saíram de `word/media/` do modelo para `figuras/exemplo-figura.png` (Figura 1) e `figuras/ifpr-campus-jacarezinho.jpeg` (Figura 2). O logotipo do cabeçalho, o ícone do ORCID e o ícone do DOI não foram extraídos: não são do corpo, e continuam vindo do modelo.

A comparação abaixo foi feita com um script de leitura direta do `word/document.xml` dos dois pacotes, contando parágrafos por `w:pStyle`, extraindo o texto de `w:t` e `m:t` e normalizando espaços, espaço inquebrável, aspas curvas e traços.

## Parágrafos por estilo

| Estilo | Modelo | Gerado |
| --- | --- | --- |
| (sem estilo) | 61 | 53 |
| Estilo1 | 5 | 0 |
| Legenda | 3 | 3 |
| Palavras-chave | 2 | 2 |
| PargrafodaLista | 6 | 4 |
| Referncias | 9 | 13 |
| Resumo | 1 | 1 |
| Style10ptJustified | 13 | 18 |
| Ttulo | 2 | 2 |
| Ttulo1 | 9 | 9 |
| Ttulo2 | 1 | 1 |
| palavra-resumo | 1 | 1 |
| **total** | **113** | **107** |

## Figuras e tabelas

| Contagem | Modelo | Gerado |
| --- | --- | --- |
| figuras_no_corpo | 9 | 8 |
| tabelas | 3 | 3 |
| media | 11 | 13 |

## Diferenças de texto (parágrafo a parágrafo, espaços normalizados)

Parágrafos com texto: modelo 96, gerado 94.

```
--- modelo
+++ gerado
@@ -1,2 +1,2 @@
-TÍTULO EM ARIAL 12, CENTRALIZADO, NEGRITO E MAIÚSCULAS: SUBTÍTULO TAMBÉM TODO EM ARIAL 12, NEGRITO E MAIÚSCULAS, SENDO A EXTENSÃO MÁXIMA DO CONJUNTO DE TRÊS LINHAS
-Nome completo do Autor 1 [1]
+TÍTULO DO ARTIGO EM ARIAL 12, CENTRALIZADO, NEGRITO E MAIÚSCULAS: SUBTÍTULO TAMBÉM TODO EM ARIAL 12, NEGRITO E MAIÚSCULAS, SENDO A EXTENSÃO MÁXIMA DO CONJUNTO DE TRÊS LINHAS
+Nome Completo do Autor 1 [1]
@@ -6,11 +6,9 @@
-Nome completo do Autor 2 [2]
-Nome completo do Autor 3 [3]
-Nome completo do Autor 4 [4]
-Nome completo do Autor 5 [5]
-Nome completo do Autor 6 [6]
-[1] Instituição do Autor 1. E-mail: email.autor1@email.com.
-[2] Instituição do Autor 2. E-mail: email.autor2@email.com.
-[3] Instituição do Autor 3. E-mail: email.autor3@email.com.
-[4] Instituição do Autor 4. E-mail: email.autor4@email.com.
-[5] Instituição do Autor 5. E-mail: email.autor5@email.com.
-[6] Instituição do Autor 6. E-mail: email.autor6@email.com.
+Nome Completo do Autor 2 [2]
+Nome Completo do Autor 3 [3]
+Nome Completo do Autor 4 [4]
+Nome Completo do Autor 5 [5]
+[1] Instituição do autor 1. E-mail: email.autor1@email.com.
+[2] Instituição do autor 2. E-mail: email.autor2@email.com.
+[3] Instituição do autor 3. E-mail: email.autor3@email.com.
+[4] Instituição do autor 4. E-mail: email.autor4@email.com.
+[5] Instituição do autor 5. E-mail: email.autor5@email.com.
@@ -32 +30 @@
-u t =K p e t + K i 0 t e t dt + K d de t dt .
+u ( t ) = K p e ( t ) + K i 0 t e ( t ) d t + K d d e ( t ) d t .
@@ -52 +50 @@
-L cp
+L c p
@@ -55 +53 @@
-m cp
+m c p
@@ -71 +69 @@
-Elencar as agências de fomento que financiaram o trabalho reportado no artigo, por exemplo, "Este estudo contou com apoio financeiro do Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq), Brasil - Bolsa nº xxxxxx/yyyy ". Caso não haja financiamento, escrever algo como "Esta pesquisa não recebeu financiamento externo específico para o seu desenvolvimento".
+Elencar as agências de fomento que financiaram o trabalho reportado no artigo, por exemplo, "Este estudo contou com apoio financeiro do Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq), Brasil, Bolsa nº xxxxxx/yyyy ". Caso não haja financiamento, escrever algo como "Esta pesquisa não recebeu financiamento externo específico para o seu desenvolvimento".
@@ -79 +77 @@
-"Declaramos que a ferramenta [nome e versão, ex.: ChatGPT - OpenAI, GPT-4o] foi utilizada como apoio nas fases de concepção e redação desta pesquisa, com as seguintes finalidades: (i) mapeamento preliminar da literatura e sugestão de referências bibliográficas, posteriormente verificadas pelos autores nas bases originais; e (ii) revisão gramatical e aprimoramento estilístico de trechos previament
+"Declaramos que a ferramenta [nome e versão, ex.: ChatGPT, OpenAI, GPT-4o] foi utilizada como apoio nas fases de concepção e redação desta pesquisa, com as seguintes finalidades: (i) mapeamento preliminar da literatura e sugestão de referências bibliográficas, posteriormente verificadas pelos autores nas bases originais; e (ii) revisão gramatical e aprimoramento estilístico de trechos previamente
@@ -90 +88 @@
-ABREU, I. S. Controle Inteligente LQR Neuro-Genético para Alocação de Autoestrutura em Sistemas Dinâmicos Multivariáveis. 2008. Tese (Doutorado em Engenharia Elétrica) - Universidade Federal do Pará, Belém, 2008.
+ABREU, I. S. Controle Inteligente LQR Neuro-Genético para Alocação de Autoestrutura em Sistemas Dinâmicos Multivariáveis. 2008. Tese (Doutorado em Engenharia Elétrica), Universidade Federal do Pará, Belém, 2008.
@@ -93 +91 @@
-NOGUEIRA, L. G. M. Projeto de Controle via LMIs Considerando Saturação no Atuador para uma Suspensão Ativa de Bancada. 80 f. Trabalho de Conclusão de Curso (TCC), Universidade Estadual Paulista "Júlio de Mesquita Filho" - UNESP, Ilha Solteira, 2016.
+NOGUEIRA, L. G. M. Projeto de Controle via LMIs Considerando Saturação no Atuador para uma Suspensão Ativa de Bancada. 80 f. Trabalho de Conclusão de Curso (TCC), Universidade Estadual Paulista "Júlio de Mesquita Filho", UNESP, Ilha Solteira, 2016.
@@ -95 +93 @@
-YAMANAKA, Hugo F.; BISPO, Carlos A. S.; BREGANON, Ricardo; RIBEIRO, Fernando S. F.; ALMEIDA, João P. L. S.; ALVES, Uiliam N. L. T. Construção e Controle Seguidor via LQR de um Sistema Aeropêndulo. Anais do XXIV Congresso Brasileiro de Automática. Fortaleza - CE: Sociedade Brasileira Automática - SBA, 2022.
+YAMANAKA, Hugo F.; BISPO, Carlos A. S.; BREGANON, Ricardo; RIBEIRO, Fernando S. F.; ALMEIDA, João P. L. S.; ALVES, Uiliam N. L. T. Construção e Controle Seguidor via LQR de um Sistema Aeropêndulo. Anais do XXIV Congresso Brasileiro de Automática. Fortaleza, CE: Sociedade Brasileira Automática, SBA, 2022.
```

## O que sobrevive à ida e volta

- Toda a estrutura de seções: 9 títulos de seção (`Ttulo1`), 1 subtítulo (`Ttulo2`) e o título de REFERÊNCIAS (`palavra-resumo`), nos dois arquivos, na mesma ordem.
- O bloco de título: título, resumo (`Resumo`), palavras-chave (`Palavras-chave`), nomes dos autores em negrito com o número entre colchetes, notas de filiação e e-mail, ícone do ORCID com link e linha do DOI.
- As três legendas (`Legenda`), com o mesmo texto, a mesma numeração e a mesma posição, abaixo da figura e acima da tabela.
- As duas figuras do corpo, byte a byte iguais às do modelo (checagem 14), e as duas tabelas de conteúdo mais a tabela da equação: 3 tabelas nos dois.
- O texto corrido de todos os parágrafos de instrução, palavra por palavra.
- A equação (1), o número à direita e a matemática no meio da linha das referências e das células de símbolo, todas em OMML.

## O que não sobrevive

- **Título.** O texto do título do modelo começa por "TÍTULO EM ARIAL", que é a âncora `titulo` do descritor. Mantido tal e qual, a checagem 15 acusa marcador do modelo remanescente. O markdown usa "TÍTULO DO ARTIGO EM ARIAL 12, ...".
- **Sexto autor.** O modelo traz 6 linhas de autor, o máximo declarado. O markdown traz 5, por defeito do conversor descrito adiante. Daí as diferenças de contagem: um ícone de ORCID a menos (8 imagens no corpo contra 9) e uma linha de tabela a menos.
- **Nome e filiação dos autores.** "Nome completo do Autor N" e "[N] Instituição do Autor N" são as âncoras `autor_nome` e `autor_filiacao`. O markdown usa "Nome Completo do Autor N" e "Instituição do autor N", que diferem só na caixa de uma letra.
- **Estilos dentro das tabelas.** O modelo usa `Estilo1` nas 5 células de símbolo e `Style10ptJustified` nas demais; o conversor usa `Style10ptJustified` em todas as células (13 contra 18 parágrafos nesse estilo, 5 contra 0 em `Estilo1`).
- **Estilos dentro de REFERÊNCIAS.** No modelo, essa seção mistura parágrafo comum, `PargrafodaLista` e `Referncias`. No conversor, toda linha depois de `## REFERÊNCIAS` vira `Referncias` (9 contra 13), e os 2 itens de lista da seção deixam de ser lista (6 contra 4 em `PargrafodaLista`).
- **Quebras de seção de uma coluna.** A Figura 2 do modelo fica em uma faixa de uma só coluna, com quebras de seção antes e depois, e o parágrafo que a cerca é partido em duas metades. O conversor não tem sintaxe para isso: a figura sai na coluna, e as duas metades do parágrafo continuam partidas.
- **Parágrafos vazios.** O modelo tem parágrafos vazios de espaçamento manual (61 contra 53 parágrafos sem estilo, contando também as linhas de autor removidas). O markdown não os representa.
- **Travessão e meia-risca.** O repositório proíbe travessão na prosa em português, então as ocorrências de "–" e "—" do modelo viraram vírgula em 5 parágrafos (FINANCIAMENTO, a declaração de IAG e três referências). É diferença de conteúdo deliberada, não perda do conversor.
- **Espaço inquebrável.** O modelo usa `\xa0` em "1. INTRODUÇÃO", nos nomes dos autores e em "5 ed."; o markdown usa espaço comum.
- **Unidades da Tabela 1.** No modelo os valores ("205 mm") estão em ambiente matemático; no markdown são texto comum, e só os símbolos ($L_1$, $L_{cp}$) ficam em matemática.

## Defeitos do conversor encontrados, e corrigidos

1. **Número máximo de autores inatingível.** Com 6 autores no markdown e 6 linhas no modelo, `aplica_autores` ainda procurava linha sobrando para apagar e falhava.
2. **Dado de autor que casa com a âncora do modelo.** O nome e a filiação já escritos continuavam sendo procurados pelas âncoras, e o conversor os tomava por linha não preenchida.

Os dois tinham a mesma causa: reprocurar as âncoras depois de já ter escrito por cima delas. Agora `aplica_autores` localiza todas as posições antes de qualquer escrita e aplica as edições de baixo para cima. Com isso o `referencia.md` voltou a usar os dados fictícios do modelo, exatos, e as 6 linhas de autor.

## A checagem 15 reprova de propósito

Esta ida e volta reproduz o texto de exemplo do modelo (título, resumo, palavras-chave e as notas de filiação). A checagem 15 existe justamente para reprovar quando esse texto sobrevive no docx final, então ela reprova aqui, e só ela: 17 de 18. Num artigo de verdade, esse texto foi substituído e a checagem passa. O runner de testes fixa essa expectativa.
