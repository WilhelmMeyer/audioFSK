# 12-13-SYNC -- gate vs. varreduras de sincronismo, quadro longo

Os testes 12 (SYNC-GATE) e 13 (SYNC-SWEEP) viram uma pasta só porque foram
medidos como **um** experimento: a mesma gravação, pontuada pelos dois
caminhos de sincronismo. Não há sala nem momento diferentes entre as duas
colunas -- é a única forma de comparar isso com poucos trials, e é a mesma
lógica de comparação pareada já usada no projeto (ver CLAUDE.md, "Compare
paired, over the same recording").

- **Código:** main em `2abc119`, mais alterações locais em `capture.py`
  (parâmetro `--sync-chirp`, e o carimbo de `sync_hush`/`sync_span_symbols`
  no JSON -- ver "Falha de ferramenta" abaixo).
- **Quando:** 2026-09-03, 16:41-16:42.
- **Camada:** M-ário, 16 tons, `fecrep 2`, com FEC. Varreduras de
  sincronismo **ligadas** nas duas pontas (`syncsweep on`).
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

## Resultado

Saída do `align.py`: mesmo áudio, cinco leituras diferentes, mudando só como
o receptor decide onde cada símbolo começa.

| leitura | bits certos | blocos |
|---|---|---|
| gate early/late, como está hoje | 95,3% | 4/4 |
| relógio travado no melhor offset (oráculo, escolhido sabendo a resposta) | 95,4% | 4/4 |
| travado, dividindo pelo GANHO por tom (o que um piloto mediria) | 93,8% | 3/4 |
| travado, dividindo pelo RUÍDO por tom (o que o código já estima sozinho) | 95,2% | 4/4 |
| varredura inicial só | 93,6% | 4/4 |
| duas varreduras: início E período medidos | **78,1%** | **0/4** |

Erro médio do alinhamento pela varredura inicial contra o melhor offset: 64
amostras de 480.

Período medido pelo par de varreduras: **480,18 amostras por símbolo**
(nominal 480,00), desvio de 0,07 entre as quatro gravações. Detecção do par
nas quatro gravações -- início / segundo pico / span em símbolos, na mesma
ordem em que as gravações foram listadas:

| gravação | início (amostra) | segundo pico (amostra) | span (símbolos) |
|---|---|---|---|
| 164114 | 39007 | 1216498 | 2452 |
| 164142 | 41143 | 1218462 | 2452 |
| 164210 | 38945 | 1216556 | 2452 |
| 164238 | 41178 | 1218370 | 2452 |

## Leitura principal

Este resultado **contraria o corpus anterior do projeto**:

- O gate **não quebrou** com o quadro longo -- ficou a 0,1 ponto do oráculo.
  A deriva real entre as pontas é de 0,18 amostra em 480, ou seja 0,04%, o
  que acumula cerca de um símbolo em 24 s. Pouco.
- As duas varreduras **medem bem e atrapalham ao ser usadas**: elas dão o
  período **médio** dos 24 s e congelam o relógio nele. Num enlace Bluetooth
  a deriva não é constante -- codec e buffers ajustam ao longo do tempo --
  então o relógio travado fica adiantado num trecho e atrasado noutro,
  enquanto o gate acompanha continuamente.
- Em quadro curto e canal degradado de propósito, o travamento já ganhou do
  gate neste projeto (o CLAUDE.md registra 8 de 8 blocos contra 5 de 8 --
  campanha anterior, canal saturado de propósito). A condição é parte do
  resultado: aqui são 24 s de quadro e canal limpo, e o resultado inverte.

## Ressalva obrigatória

95% dos bits e 4/4 blocos em quase todas as leituras significa que **este
link tem margem demais para o teste discriminar** entre gate, oráculo e piso
por tom -- só a leitura de duas varreduras se separa do resto, e para pior.
Um teste de sincronismo só separa métodos num canal onde algo falha; aqui,
quase nada falhou, exceto a própria estratégia das duas varreduras.

## Falha de ferramenta revelada por este teste

O `capture.py` ganhou `--sync-chirp`, mas inicialmente carimbava só
`sync_chirp` no JSON, sem `sync_span_symbols` nem `sync_hush`. O `align.py`
lê `sync_span_symbols` e, sem ele, nem tenta procurar o par de varreduras --
a linha correspondente simplesmente não aparecia na saída, e a primeira
leitura concluiu erradamente que o par não tinha sido detectado. O span
(quantos símbolos separam as duas varreduras) não é dedutível do áudio: o
intervalo entre as varreduras só vira período depois de dividido por ele, e
o receptor só o conhece porque sabe o tamanho do bloco. Errar o span em um
símbolo erra o período medido em um quinto de amostra.

## Arquivos

- `gravacao/` -- as quatro gravações, WAV float32 mais JSON
- `figuras/` -- espectro cru e contraste (600-3600 Hz), geradas com
  `spectro.py --lo 600 --hi 3600`; as quatro figuras saíram sem erro
