# 12-13-SYNC -- gate vs. varreduras de sincronismo, quadro longo

Os testes 12 (SYNC-GATE) e 13 (SYNC-SWEEP) viram uma pasta só porque foram
medidos como **um** experimento: a mesma gravação, pontuada pelos dois
caminhos de sincronismo. Não há sala nem momento diferentes entre as duas
colunas -- é a única forma de comparar isso com poucos trials, e é a mesma
lógica de comparação pareada já usada no projeto (ver CLAUDE.md, "Compare
paired, over the same recording").

**Esta é a segunda redação deste HEADER.** A primeira reportou as varreduras
perdendo feio do gate (78,1% dos bits, 0/4 blocos) e tirou conclusões daquilo.
Era um bug de carimbo, não um resultado; a investigação está em
[`INVESTIGACAO.md`](INVESTIGACAO.md) e o que foi retirado está listado no fim
desta página.

- **Código:** `d7e170e` (repontuação). As gravações foram feitas em `2abc119`
  mais alterações locais no `capture.py`; o áudio não mudou, só o número
  `sync_span_symbols` no sidecar e o decodificador que o lê.
- **Quando:** gravado 2026-09-03, 16:41-16:42. Repontuado 2026-09-03.
- **Camada:** M-ário, 16 tons, `fecrep 2`, com FEC. Varreduras de
  sincronismo **ligadas** nas duas pontas (`syncsweep on`), então as duas
  colunas abaixo saem do mesmo áudio -- o que muda é só como o receptor
  offline decide onde cada símbolo começa.
- **Direção:** B -> A.
- **Payload:** bloco de **192 bytes** (~24 s de ar), 4 trials.
- **Bancada:** A = Linux, microfone interno Mic1 índice 26, ganho de captura
  Dmic0 45 (-5 dB). B = Windows, caixa Bluetooth AL-667 a ~60% do volume,
  ganho digital 1.0.

## Por que 192 bytes

As duas pontas têm relógios independentes, e a deriva entre eles **acumula**
ao longo do quadro. Um bloco de 48 bytes (6 s, como em 07-MARY-BASE e
08-MARY-GAIN) mal deixa a deriva aparecer. 192 bytes (24 s) é onde o gate
early/late deveria começar a quebrar, e é o intervalo em que o par de
varreduras (uma no início do quadro, outra no fim) mede o período de verdade.
Não é degradação artificial -- é o caso de uso real de um quadro longo.

## Níveis

| gravação | rms | pico | duração |
|---|---|---|---|
| 164114 | 0,0354 | 0,155 | 27,7 s |
| 164142 | 0,0364 | 0,194 | 27,7 s |
| 164210 | 0,0364 | 0,165 | 27,8 s |
| 164238 | 0,0325 | 0,152 | 27,7 s |

## Resultado, pareado, gravação a gravação

Mesmo áudio nas duas colunas. Acerto de bits no melhor deslizamento por força
bruta, uma régua só; bloco inteiro pelo caminho FEC de verdade.

| gravação | gate: bits / bloco | duas varreduras: bits / bloco | período medido |
|---|---|---|---|
| 164114 | 95,71% / OK | 95,71% / OK | 480,021 |
| 164142 | 95,28% / OK | **96,00%** / OK | 479,951 |
| 164210 | 95,65% / OK | **95,67%** / OK | 480,070 |
| 164238 | 94,59% / OK | **95,32%** / OK | 479,899 |
| **média** | **95,31% / 4-4** | **95,68% / 4-4** | **479,99** |

As varreduras não perdem em nenhuma das quatro: ganham em três e empatam na
quarta (95,71 contra 95,71). A margem é pequena -- 0,37 ponto no agregado.

## Resultado, todas as leituras (saída do `align.py`)

| leitura | bits certos | blocos |
|---|---|---|
| gate early/late, como está hoje | 95,3% | 4/4 |
| relógio travado no melhor offset (oráculo, sabendo a resposta) | 95,4% | 4/4 |
| travado, dividindo pelo GANHO por tom (o que um piloto mediria) | 93,8% | 3/4 |
| travado, dividindo pelo RUÍDO por tom (o que o código já estima) | 95,2% | 4/4 |
| varredura inicial só | 93,6% | 4/4 |
| duas varreduras: início E período medidos | **95,7%** | **4/4** |

Erro médio do alinhamento pela varredura inicial contra o melhor offset: 64
amostras de 480. É por isso que a varredura sozinha (93,6%) fica **abaixo** do
gate: ela acerta o início dentro de um oitavo de símbolo e congela ali. O par
é o que conserta isso, porque o período medido reposiciona cada janela.

Período medido pelo par: **479,99 amostras por símbolo** (nominal 480,00),
faixa 479,90 a 480,07, desvio 0,07 entre as quatro gravações. Detecção do par
nas quatro:

| gravação | início (amostra) | segundo pico (amostra) | span (símbolos) |
|---|---|---|---|
| 164114 | 39007 | 1216498 | 2453 |
| 164142 | 41143 | 1218462 | 2453 |
| 164210 | 38945 | 1216556 | 2453 |
| 164238 | 41178 | 1218370 | 2453 |

## Leitura principal

- **A deriva real entre as duas máquinas é indistinguível de zero neste
  enlace.** O período medido pelo par de varreduras é 479,99 ± 0,07 contra um
  nominal de 480,00. Vinte e quatro segundos de quadro não acumularam deriva
  mensurável, e é por isso que o gate não quebrou.
- **O gate está a 0,1 ponto do oráculo** (95,3% contra 95,4%). Não há prêmio
  de sincronismo a coletar aqui: nem o melhor offset possível, escolhido
  sabendo a resposta, tira mais bits deste áudio.
- **As varreduras empatam ou ganham de pouco**, 95,68% contra 95,31%, 4/4
  blocos nos dois casos. Coerente com o corpus anterior (CLAUDE.md: 8 de 8
  blocos contra 5 de 8, e 59 de 60 gravações pareadas), mas com margem muito
  menor -- naquele corpus o canal estava saturado de propósito e o gate
  colapsava em algumas gravações; aqui nada colapsa.
- **A varredura inicial sozinha é pior que o gate** (93,6% contra 95,3%), e
  isso não é contradição: um relógio travado num offset com 64 amostras de
  erro é pior que um relógio que se corrige continuamente. O valor do
  mecanismo está no **par**, não na varredura de abertura.

## Ressalvas

**Este link tem margem demais para o teste discriminar.** 95% dos bits e 4/4
blocos em praticamente todas as leituras significa que o experimento não
separa métodos de sincronismo. Um teste de sincronismo só separa métodos num
canal onde algo falha. O único número que se separou do resto foi um erro de
ferramenta (abaixo), não uma propriedade do canal.

**Quatro trials não resolvem 0,37 ponto.** A vantagem das varreduras no
agregado é menor que a diferença entre duas gravações vizinhas do mesmo
ajuste. O que sustenta alguma coisa é o pareamento -- quatro de quatro sem
perder -- e quatro é pouco para pareamento também.

**O número de "duas varreduras" tem de vir do `align.py`, e só dele.** Conferido
no código (`grep -n sync_chirp *.py`): `align.py:188` é o único que lê o campo.
`resultado.py` e `bench.py` **não leem `sync_chirp`** -- eles demodulam pelo
caminho de streaming com o gate, com os 80 ms de tom varrido caindo onde
deveriam estar os primeiros símbolos do preâmbulo. Ou seja, se a pasta fosse
montada pelo `resultado.py`, as duas condições sairiam com a mesma coluna (a
do gate) e a comparação não mediria nada. Por isso o `resultado.csv` desta
pasta traz `bits_gate` e `bits_varr2` como colunas separadas, as duas vindas
do `align.py`, e diz isso na última linha. **Não consertado de propósito** --
a decisão sobre mexer no `resultado.py` fica para depois.

**As gravações foram recarimbadas.** O áudio é o original; o campo
`sync_span_symbols` nos JSONs passou de 2452,0 para 2453,0. O valor antigo
está preservado em `sync_span_symbols_original` e o campo
`sync_span_corrigido: true` marca os oito sidecars afetados (quatro aqui,
quatro em `captures-sync/`, que são as mesmas gravações). Nenhuma outra pasta
de captura tem `sync_chirp: true`.

## Conclusões retiradas da primeira redação

Não foram apagadas em silêncio porque cada uma delas era uma afirmação sobre o
canal, e as duas estavam erradas pela mesma causa.

1. **"O relógio travado sofre com a deriva variável do codec Bluetooth --
   codec e buffers ajustam ao longo do tempo, então ele fica adiantado num
   trecho e atrasado noutro."** RETIRADA. Não há deriva a acompanhar: o
   período medido é 479,99 ± 0,07 em 480,00. O que fazia o relógio travado
   errar não era o Bluetooth, era um período calculado com um divisor errado.
2. **"Em quadro longo e canal limpo o resultado inverte -- o travamento
   ganhou do gate em quadro curto e canal degradado, e perde aqui."**
   RETIRADA. Não inverte: sobre o mesmo áudio, com o span corrigido, as
   varreduras empatam ou ganham nas quatro gravações. A condição continua
   importando (a margem cai muito num canal limpo), mas o sinal não muda.
3. A inferência de que "a deriva real entre as pontas é de 0,18 amostra em
   480, ou seja 0,04%" também cai: esses 0,18 eram inteiramente o erro de um
   símbolo no span.

**Causa raiz:** `capture.py:sync_span` arredondava o corpo codificado para
baixo onde o transmissor arredondava para cima, carimbando 2452 símbolos onde
o ar levava 2453. Um símbolo em 2452 é 0,2 amostra de período, que ao longo de
24 s acumula quase um símbolo inteiro de deriva -- 78,1% dos bits e 0/4 blocos
contra 95,7% e 4/4 sobre exatamente o mesmo áudio. Consertado em `d7e170e`:
`fec.frame_symbols` é agora a conta canônica, e `console.py` e `capture.py`
chamam a mesma função. Medida completa em [`INVESTIGACAO.md`](INVESTIGACAO.md).

## Arquivos

- `gravacao/` -- as quatro gravações, WAV float32 mais JSON (span recarimbado)
- `figuras/` -- espectro cru e contraste (600-3600 Hz), geradas com
  `spectro.py --lo 600 --hi 3600`; as quatro figuras saíram sem erro
- `resultado.csv` -- uma linha por gravação, gate e duas varreduras lado a lado
- `INVESTIGACAO.md` -- por que a primeira leitura deu o contrário
