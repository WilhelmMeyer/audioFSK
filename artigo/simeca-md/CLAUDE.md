# simeca-md

## O que é

Conversor de markdown para docx no formato de um modelo do Word, e do docx para PDF. O modelo entra como argumento (`-m modelo.docx`) com um descritor `modelo.toml` ao lado: o código não conhece nenhum modelo por dentro. Nasceu do montador de artigo do projeto roda-reacao, generalizado.

## Regras de projeto

- Só biblioteca padrão do Python, versão mínima 3.11 (por causa do `tomllib`). Exceção: `win32com`, opcional, importado dentro de `try`, só para gerar PDF via Word.
- pandoc e LibreOffice são externos e opcionais: detectados em tempo de execução, nunca embarcados no repositório (tamanho e licença GPL). Instalação sempre pelo gerenciador de pacotes do usuário, com confirmação.
- Âncora de parágrafo é o texto marcador do modelo, nunca `w14:paraId`: o Word reescreve esse identificador ao salvar, e o modelo é editado no Word.
- Geometria (largura de coluna, margens, colunas) é medida do `sectPr` do modelo, nunca constante no código.
- A saída preserva o pacote docx do modelo byte a byte, exceto `word/document.xml`, `word/_rels/document.xml.rels` e as imagens acrescentadas em `word/media/`.

## Estilo obrigatório

- Nunca usar travessão (—) na prosa em português; usar vírgula, dois-pontos ou parênteses.
- Um parágrafo por linha no markdown, sem quebra de linha cosmética.
- Comentários de código em português sem acento.
- Sem comentários de autojustificativa (nada de "removi porque…").

## Mapa

- `simeca_md/modelo.py` — carrega o docx e o descritor, mede a página, acha parágrafo por âncora.
- `simeca_md/conversor.py` — parser do markdown, renderização em OOXML, preenchimento do bloco de título, montagem do zip.
- `simeca_md/verifica.py` — as 18 checagens e os avisos.
- `simeca_md/largura.py` — estimativa de largura de equação, para avisar o que estoura a coluna.
- `simeca_md/pandoc.py`, `simeca_md/pdf.py` — dependências externas, detecção e uso.
- `simeca_md/cli.py` — linha de comando.
- `modelos/<evento>/` — docx, descritor, figuras e o markdown de referência daquele modelo.
- `exemplos/minimo.md` — exercita todo o dialeto aceito.
- `testes/roda_testes.py` — runner sem framework.

## Rodar

```sh
python3 -m simeca_md exemplos/minimo.md -m modelos/simeca-vii/modelo.docx -o /tmp/saida.docx
python3 testes/roda_testes.py
```
