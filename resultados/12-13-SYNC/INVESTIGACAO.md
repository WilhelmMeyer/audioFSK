# Investigacao -- por que as duas varreduras "perderam" do gate em 12-13-SYNC

Analise offline, so sobre as quatro gravacoes ja existentes
(`resultados/12-13-SYNC/gravacao/`, identicas as de `captures-sync/`).
Nenhum hardware foi tocado.

## O fato a explicar

O teste mediu, sobre o mesmo audio:

| leitura | bits certos | blocos |
|---|---|---|
| gate early/late | 95,3% | 4/4 |
| duas varreduras | 78,1% | 0/4 |

O corpus anterior do projeto registra o contrario (8 de 8 blocos com as
varreduras contra 5 de 8 do gate, e 59 de 60 gravacoes pareadas a favor das
varreduras). Uma inversao dessa dimensao pede causa, nao interpretacao.

## Hipotese

O periodo de simbolo medido pelas varreduras e o intervalo entre os dois
picos **dividido pelo numero de simbolos que eles cercam** (`sync_span_symbols`,
carimbado no JSON pelo `capture.py`). Esse numero nao e deduzivel do audio.
Se o carimbo estiver errado em **um simbolo**, o periodo sai errado em ~0,2
amostra, o relogio travado nele acumula ~1 simbolo de deriva ao longo do
quadro, e a leitura vira uma resposta confiante e errada -- exatamente o modo
de falha que o CLAUDE.md ja descreve para a deteccao dos picos, por outra
porta.

Suspeita reforcada pelo proprio numero do HEADER: 480,18 amostras por simbolo
com desvio de apenas 0,07 entre as quatro gravacoes. Um vies **sistematico**
e pequeno, igual nas quatro -- assinatura de erro de conta, nao de deriva de
relogio de Bluetooth, que variaria de gravacao para gravacao.

## Conferencia do codigo, linha a linha

Transmissor -- `console.py:387`, `AudioNode.mary_frame_symbols`:

    return len(pre) // MARY_BITS + -(-nbits // MARY_BITS) + 6

Carimbo da gravacao -- `capture.py:152`, `sync_span`:

    body = len(list(fec.frame(bytes(nbytes), repeat=repeat))) // MARY_BITS

Um usa **teto** (`-(-n // 4)`), o outro usa **piso** (`// 4`). O preambulo tem
480 bits (multiplo de 4) e nao revela a diferenca; o corpo codificado, nao:

| payload | fecrep | bits codificados | bits % 4 | span `capture.py` | span real (TX) |
|---|---|---|---|---|---|
| 192 B | 2 | 9283 | 3 | **2452** | **2453** |
| 192 B | 1 | 4657 | 1 | 1296 | 1297 |
| 48 B | 2 | 2371 | 3 | 724 | 725 |

O JSON destas quatro gravacoes carimbou `sync_span_symbols: 2452.0`. O
transmissor montou 2453. `MaryModulator.modulate_bits` (`modem.py:768`)
completa os bits ate multiplo de 4 -- entao o simbolo parcial existe no ar e
o piso o descarta.

## Medida

Mesmo audio, mesma leitura por par de varreduras, mudando so o span. Acerto
de bits no melhor deslize (regra unica, como manda o `align.py`), e o perfil
do acerto em oito janelas do comeco ao fim do bloco:

| gravacao | span | periodo | bits | bloco | perfil (8 janelas, %) |
|---|---|---|---|---|---|
| 164114 | 2452 | 480,217 | 81,8% | X | 49 64 80 87 94 93 93 94 |
| 164114 | **2453** | **480,021** | **95,7%** | **OK** | 98 97 95 96 96 95 94 95 |
| 164142 | 2452 | 480,146 | 76,1% | X | 95 96 94 87 73 59 53 52 |
| 164142 | **2453** | **479,951** | **96,0%** | **OK** | 96 98 95 96 97 92 97 97 |
| 164210 | 2452 | 480,265 | 79,5% | X | 53 60 72 81 89 92 96 92 |
| 164210 | **2453** | **480,070** | **95,7%** | **OK** | 92 96 97 98 97 96 97 93 |
| 164238 | 2452 | 480,095 | 74,9% | X | 96 95 92 84 69 58 53 53 |
| 164238 | **2453** | **479,899** | **95,3%** | **OK** | 95 95 94 94 97 95 95 96 |

Media: **78,1% e 0/4 blocos** com o span carimbado, **95,7% e 4/4 blocos** com
o span certo. Os 78,1% reproduzem exatamente o numero do HEADER, o que
confirma que a linha investigada e a mesma que foi medida.

**Deriva, nao offset.** O perfil responde a pergunta 3 sozinho: com o span
errado o acerto e uma **rampa** monotonica (49 -> 94, ou 96 -> 52; sobe ou
desce conforme onde o melhor deslize centrou o erro), assinatura de periodo
errado. Com o span certo o perfil e **plano** em ~95% do inicio ao fim. A
conta fecha: 0,2 amostra por simbolo x 2452 simbolos = ~440 amostras, quase
um simbolo inteiro de deriva acumulada em 24 s.

## Conclusao

**E bug de codigo, nao limitacao do mecanismo em quadro longo.**

- Arquivo e linha: `capture.py:152` (funcao `sync_span`, linhas 141-153).
- Conserto: trocar o piso por teto no corpo codificado, isto e

      body = -(-len(fec.frame(bytes(nbytes), repeat=repeat)) // MARY_BITS)

  (o `len(list(...))` continua valendo; o que muda e a divisao). Melhor ainda
  seria `capture.py` chamar uma unica funcao compartilhada com
  `console.py:mary_frame_symbols`, pelo mesmo motivo que aquele docstring da:
  duas contas do mesmo numero divergem, e divergiram. **Nao aplicado aqui**,
  por pedido.
- O `selfcapture.py` **nao** tem este bug: ele deriva o span do numero de
  amostras do corpo que ele mesmo sintetizou (`selfcapture.py:161`), sem
  contar simbolos. Por isso os numeros antigos do CLAUDE.md (8/8 e 59/60,
  caminho de auto-captura) continuam validos -- o defeito e do caminho de
  duas maquinas, e e recente (`--sync-chirp` do `capture.py` e alteracao local
  nao commitada, ver "Falha de ferramenta" no HEADER).

## O que muda no resultado do teste 12-13

Corrigido o span, o periodo medido cai para **479,99 amostras por simbolo**
(479,90 a 480,07, desvio 0,07) -- ou seja, a deriva real entre as duas
maquinas neste enlace e **indistinguivel de zero**, nao os 0,04% que o HEADER
inferiu. E a comparacao passa a ser:

| leitura | bits | blocos |
|---|---|---|
| gate early/late | 95,3% | 4/4 |
| oraculo (melhor offset travado) | 95,4% | 4/4 |
| duas varreduras, span corrigido | **95,7%** | **4/4** |

As varreduras deixam de perder e passam a empatar/ganhar por margem pequena.
A ressalva do HEADER permanece e fica ainda mais forte: **este link tem margem
demais para o teste discriminar** metodos de sincronismo. O que o teste
discriminou de fato foi um erro de um simbolo numa formula duplicada.

Duas frases do HEADER ficam **retiradas** pela medida acima: a de que o
relogio travado sofre com deriva variavel do codec Bluetooth, e a de que a
condicao (quadro longo, canal limpo) inverte o resultado. Nenhuma das duas se
sustenta -- o mesmo audio, com o span certo, nao inverte nada.

## Adendo -- conserto aplicado

O conserto foi aplicado depois desta analise, em `d7e170e`, de forma um pouco
melhor do que o sugerido acima: `fec.frame_symbols(nbytes, repeat,
symbol_bits, idle_symbols=6)` passou a ser a conta canonica, e
`console.py:mary_frame_symbols` e `capture.py:sync_span` a chamam. Uma conta
so, em vez de duas que ja divergiram. As oito gravacoes existentes foram
recarimbadas (2452 -> 2453), com o valor antigo preservado em
`sync_span_symbols_original` e um `sync_span_corrigido: true` no sidecar. Os
numeros repontuados estao no `HEADER.md`.
