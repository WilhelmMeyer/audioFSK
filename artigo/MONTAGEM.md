# Como montar o artigo

O texto do artigo é o `artigo/artigo_modem.md`. A montagem gera `artigo_modem.docx` e `artigo_modem.pdf` ao lado dele, sempre por cima da versão anterior, como um compilador. As duas saídas são ignoradas pelo git: quem monta é a ferramenta, não o repositório.

## Linux e macOS

```sh
./artigo/monta.sh                 # docx e pdf, com figuras
./artigo/monta.sh --sem-figuras   # só as legendas, para revisar o texto
./artigo/monta.sh --verifica      # só confere o que já foi gerado
```

## Windows

```bat
artigo\monta.cmd
artigo\monta.cmd --sem-figuras
artigo\monta.cmd --verifica
```

Rode de qualquer pasta; os dois scripts descobrem sozinhos onde estão. Eles não têm lógica própria, apenas escolhem o interpretador e chamam o `artigo/monta.py`, que é o mesmo arquivo nos dois sistemas.

## O que precisa estar instalado

O conversor vem dentro do repositório, em `artigo/simeca-md`. Não há passo de submódulo, nem `pip install`, nem `venv`: quem tem a pasta do projeto tem a ferramenta.

**Python 3.11 ou mais novo.** No Windows, o instalador de python.org ou a Microsoft Store; o `monta.cmd` procura o `py -3` e, se não houver, o `python`. O conversor não usa nenhuma biblioteca de terceiros, então não há `pip install` e não se usa a `venv` do modem.

**pandoc**, porque o artigo tem equações e é o pandoc que converte o LaTeX delas para a matemática nativa do Word. No Windows, `winget install --id JohnMacFarlane.Pandoc`; no Linux, `sudo apt install pandoc`. Faltando, o conversor mostra o comando e se oferece para instalar.

**LibreOffice ou Word**, só para o PDF. O caminho de menos atrito é o LibreOffice, um comando e nada mais: `winget install --id TheDocumentFoundation.LibreOffice` no Windows, `sudo apt install libreoffice` no Linux. No Windows há também o Word, que reproduz o modelo com mais fidelidade e por isso vem na frente quando existe, mas ele entra por COM e exige o `pywin32` instalado **no mesmo Python que o `py -3` abre**, isto é `py -3 -m pip install pywin32`. Instalado em outro interpretador, o efeito é o docx sair e o PDF não, sem erro que explique o porquê. Sem nenhum dos dois motores o docx sai normalmente e o programa avisa que o PDF não saiu.

## Se der errado

O conversor é uma cópia de `github.com/WilhelmMeyer/simeca-md`, trazida para cá em 2026-09-06. Corrija-o aqui mesmo, em `artigo/simeca-md`, e avise, porque a cópia lá fora não fica sabendo.
