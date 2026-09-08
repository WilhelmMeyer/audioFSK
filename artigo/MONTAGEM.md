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

No Git Bash o `./artigo/monta.sh` também serve, e escolhe o mesmo interpretador que o `.cmd` escolheria.

Rode de qualquer pasta; os dois scripts descobrem sozinhos onde estão. Eles não têm lógica própria, apenas escolhem o interpretador e chamam o `artigo/monta.py`, que é o mesmo arquivo nos dois sistemas.

Escolher pelo nome não bastaria no Windows. O `python3` do PATH costuma ser o atalho da Microsoft Store, que não é interpretador nenhum: ele convida a instalar e sai com erro, e esse convite aparecia no lugar do artigo. Os dois lançadores rodam um `-c` em cada candidato antes de lhe entregar o trabalho, o que de quebra recusa um Python anterior ao 3.11 que o conversor exige. A ordem é `py -3`, depois `python`, e no Git Bash o `python3` vem antes dos dois.

## O que precisa estar instalado

O conversor vem dentro do repositório, em `artigo/simeca-md`. Não há passo de submódulo, nem `pip install`, nem `venv`: quem tem a pasta do projeto tem a ferramenta.

**Python 3.11 ou mais novo.** No Windows, o instalador de python.org ou a Microsoft Store; o `monta.cmd` procura o `py -3` e, se não houver, o `python`. O conversor não usa nenhuma biblioteca de terceiros, então não há `pip install` e não se usa a `venv` do modem.

**pandoc**, porque o artigo tem equações e é o pandoc que converte o LaTeX delas para a matemática nativa do Word. No Windows, `winget install --id JohnMacFarlane.Pandoc`; no Linux, `sudo apt install pandoc`. Faltando, o conversor mostra o comando e se oferece para instalar. Sem ele não sai nem o docx: as equações estão no texto, e não há caminho que as ignore.

No Windows há duas armadilhas em volta disso, e as duas estão tratadas no `simeca_md/pandoc.py`. A primeira é o PATH: um terminal aberto antes da instalação não enxerga o pandoc recém-instalado, então o conversor procura também nas pastas do instalador (`%ProgramFiles%\Pandoc`, `%LOCALAPPDATA%\Pandoc` e os atalhos do winget) antes de dizer que não achou. A segunda é a pergunta de instalação: o `isatty()` do Windows não distingue um terminal do dispositivo `NUL`, de modo que a montagem chamada por um script chegava a perguntar e morria com um `EOFError`. Sem ninguém para responder, ela agora termina pela mensagem que diz o que instalar.

**LibreOffice ou Word**, só para o PDF. O caminho de menos atrito é o LibreOffice, um comando e nada mais: `winget install --id TheDocumentFoundation.LibreOffice` no Windows, `sudo apt install libreoffice` no Linux. No Windows há também o Word, que reproduz o modelo com mais fidelidade e por isso vem na frente quando existe, mas ele entra por COM e exige o `pywin32` instalado **no mesmo Python que o `py -3` abre**, isto é `py -3 -m pip install pywin32`. Instalado em outro interpretador, o efeito é o docx sair e o PDF não, sem erro que explique o porquê. Sem nenhum dos dois motores o docx sai normalmente e o programa avisa que o PDF não saiu.

## Se der errado

O conversor é uma cópia de `github.com/WilhelmMeyer/simeca-md`, trazida para cá em 2026-09-06. Corrija-o aqui mesmo, em `artigo/simeca-md`, e avise, porque a cópia lá fora não fica sabendo.
