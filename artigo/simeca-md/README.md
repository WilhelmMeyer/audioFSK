# simeca-md

Converte um artigo escrito em markdown para docx no formato de um modelo do Word, e do docx gera o PDF. Nasceu do modelo de artigo do SIMECA, mas o modelo entra como argumento: o programa não conhece nenhum por dentro.

A ideia é escrever o artigo em texto puro, versionável e diffável, e deixar a montagem do docx para uma ferramenta que preserva o modelo do evento byte a byte, alterando só o que precisa mudar.

## Instalação

Requer Python 3.11 ou mais novo, e nada além disso para gerar o docx.

```sh
git clone <este repo> && cd simeca-md
python3 -m simeca_md artigo.md -m modelos/simeca-vii/modelo.docx
```

Para instalar como comando:

```sh
pipx install .        # ou: uv tool install .
simeca-md artigo.md -m modelos/simeca-vii/modelo.docx
```

Funciona igual em Linux e Windows.

### Dependências externas, ambas opcionais até serem necessárias

**pandoc**, só se o artigo tiver equações. É ele que converte o LaTeX em OMML, a matemática nativa do Word, e não há substituto. Se faltar, o programa explica, mostra o comando de instalação do sistema e pergunta se deve rodar. Enter instala.

```
pandoc nao encontrado no PATH.
O pandoc converte o LaTeX das equacoes em OMML e nao tem substituto no projeto.
Instale com:

    sudo apt install pandoc

Instalar agora com o gerenciador do sistema? [S/n]
```

Fora de terminal interativo (CI, script), nunca instala nada: imprime o comando e sai com erro. `--pandoc nunca` desliga a oferta, `--pandoc instalar` dispensa a pergunta.

**LibreOffice** ou **Microsoft Word**, só para `--pdf`. O PDF sai do docx, por um motor de layout de verdade, não de uma segunda conversão a partir do markdown. Sem motor instalado, o docx sai normalmente e o programa avisa que o PDF não saiu.

## Uso

```sh
simeca-md artigo.md -m modelos/simeca-vii/modelo.docx          # gera artigo.docx e confere
simeca-md artigo.md -m ... --pdf                               # gera também artigo.pdf
simeca-md artigo.md -m ... -o entrega.docx                     # outro nome de saída
simeca-md artigo.md -m ... --sem-figuras                       # só as legendas, para revisar texto
simeca-md artigo.md -m ... --verifica                          # só confere o que já foi gerado
```

A saída, docx ou pdf, é sempre regravada por cima de uma existente, como um compilador de LaTeX.

A verificação roda sempre depois de gerar, e sai com código 1 se alguma checagem falhar.

## O markdown aceito

Um parágrafo por linha. Comentários HTML são ignorados.

| No markdown | No docx |
| --- | --- |
| `# Título` | título do artigo, em maiúsculas |
| `**AUTORES:**` seguido de `N. nome \| orcid \| filiação \| e-mail` | tabela de autores, notas de rodapé e link no ícone ORCID |
| `**DOI:** https://doi.org/...` | linha do DOI no bloco de título |
| `## RESUMO` e o parágrafo seguinte | resumo, com o rótulo do próprio modelo |
| `**PALAVRAS-CHAVE:** ...` | palavras-chave |
| `## 1 SEÇÃO` / `### 1.1 SUBSEÇÃO` | títulos numerados pela numeração do modelo |
| `## REFERÊNCIAS` | dali para baixo, cada linha é uma referência |
| `![Figura 1 - legenda](figuras/x.png "0.6")` | figura centralizada, escalada para a coluna, mais a legenda |
| linha `Tabela 1 - legenda` antes de uma tabela em pipes | legenda colada na tabela |
| `$latex$` | matemática no meio da linha |
| `$$latex \tag{1}$$` | equação centralizada com número à direita |
| `*itálico*`, `**negrito**` | itálico e negrito |

O número na legenda é o que vale: o conversor não renumera, só confere que a sequência está inteira.

### Figura vetorial

A figura aceita `.png`, `.jpeg` e `.svg`. Em SVG a imagem entra no docx como vetorial, do jeito que o próprio Word grava: o SVG vai na extensão do blip e um PNG de mesmo nome, ao lado do SVG, entra como reserva para o leitor que não tem suporte a vetorial (Word anterior ao 2016, entre outros). Esse PNG é obrigatório, e o montador para com o comando de exportação na mensagem se ele faltar:

```
inkscape figura.svg -o figura.png --export-background=white --export-width=2400
```

O SVG é conferido como XML na montagem. Um arquivo malformado não para o inkscape, que recupera do erro, mas o LibreOffice desiste e deixa a figura em branco no PDF sem avisar; o caso mais fácil de cometer é o hífen duplo dentro de comentário, que vem de brinde ao anotar o comando de exportação no próprio arquivo.

Vale para desenho de linha, diagrama de blocos e esquemático, que ficam nítidos em qualquer ampliação e mantêm o texto pesquisável no PDF. Gráfico de dados não ganha nada com isso: em SVG fica pesado, e um PNG na largura da coluna com 2400 px já dá 660 dpi.

## O descritor do modelo

Cada modelo mora numa pasta com o docx e um `modelo.toml` ao lado. O toml diz onde estão as coisas, por texto marcador, não por identificador interno:

```toml
[ancoras]
titulo = "^T[ÍI]TULO EM ARIAL"
autor_nome = "^Nome completo do Autor\\s*(\\d+)"
```

Editar o docx no Word (fonte, posição, logotipo, cor) não quebra nada, desde que esses textos marcadores continuem reconhecíveis. Foi por isso que a âncora não é o `w14:paraId`: o Word reescreve esse identificador ao salvar.

Geometria não se declara, se mede: largura de coluna, margens e número de colunas saem do `sectPr` do próprio modelo, e é contra isso que a conferência de espaço compara.

Para um modelo novo, copie a pasta `modelos/simeca-vii/`, troque o docx e ajuste as âncoras e os nomes de estilo. Os nomes de estilo são os que o Word gravou no `styles.xml`, em geral sem acento e sem espaço (`Ttulo1`, `Referncias`).

## O que a verificação confere

18 checagens, todas rodando a cada geração. As principais:

- todo arquivo do modelo, exceto `document.xml` e seu `.rels`, sai idêntico byte a byte;
- todo estilo e toda numeração usados existem no modelo;
- as contagens de seção, subseção e referência batem com o markdown;
- toda legenda está rotulada e numerada em sequência, colada na figura ou na tabela certa;
- cada imagem embutida tem relationship, arquivo em `word/media/` e bytes iguais aos do original;
- nenhum texto marcador do modelo sobreviveu no docx final;
- figura e tabela cabem na largura da coluna.

Avisos, que não reprovam: campo de autor faltando, DOI ainda igual ao do modelo, e equação larga demais para a coluna. Esta última é uma estimativa (não há motor de layout aqui), feita glifo a glifo sobre o OMML, com fração empilhando e expoente reduzido. Serve para pegar a equação que vaza da coluna antes de descobrir isso no PDF.

## Exemplo

`exemplos/minimo.md` exercita tudo de ponta a ponta.

`modelos/simeca-vii/referencia.md` é o próprio conteúdo do modelo transcrito para markdown: convertê-lo de volta é o teste de que a ferramenta reproduz o formato do evento. Ele reprova de propósito na checagem 15, e só nela, porque reproduz o texto de exemplo do modelo, que é exatamente o que aquela checagem existe para pegar. O que sobrevive e o que não sobrevive à ida e volta está em `modelos/simeca-vii/RESULTADO-IDA-E-VOLTA.md`.

Os testes ficam em `testes/roda_testes.py`, sem framework: `python3 testes/roda_testes.py`.

## Licença

MIT. O pandoc e o LibreOffice são programas de terceiros, instalados pelo gerenciador de pacotes do usuário: este projeto não redistribui nenhum dos dois.
