# 08-MARY-GAIN-A2B -- M-ario, varredura de ganho, sentido A->B

- **Codigo:** commit `cce3ee8-dirty` (main).
- **Quando:** 2026-09-03, 17:56-18:14.
- **Bancada:** A (Linux, console, transmite) caixa Bluetooth
  `41:42:2B:14:D4:2A`, indice PortAudio 20. B (Windows, agent, grava)
  microfone interno do notebook. O par WAV+JSON volta de B para A pelo cabo
  `/dev/ttyUSB0` a 115200 baud, int16.
- **Camada:** M-ario, 16 tons, `fecrep 1`, com FEC. `syncsweep off`, sem
  gap, sem banda, sem acorde.
- **Direcao:** A -> B (nunca medida nesta bancada ate a campanha atual).
- **Payload:** 48 bytes aleatorios, quatro pontos de ganho digital no
  transmissor (1.0 / 0.7 / 0.5 / 0.25), 3 trials cada.

Pontuado offline por `resultado.py` (regua do gate, `bloco_ok` pelo caminho
FEC real) e por `align.py` (relogio travado no melhor deslizamento, e as
duas variantes de divisor por tom). Figuras extras `*-leitura.png` geradas
com `spectro.py --fundido --win 480`.

## Resultado

| gravacao | ganho | rep | bytes | bits (gate) | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-175617-mary-g1.0-A2B` | 1,00 | 1 | 48 | 80,93% | nao | 0,562 | 0,122 |
| `20260903-175751-mary-g1.0-A2B` | 1,00 | 1 | 48 | 80,10% | nao | 0,542 | 0,111 |
| `20260903-175925-mary-g1.0-A2B` | 1,00 | 1 | 48 | 79,68% | nao | 0,515 | 0,096 |
| `20260903-180108-mary-g0.7-A2B` | 0,70 | 1 | 48 | 74,60% | nao | 0,486 | 0,098 |
| `20260903-180242-mary-g0.7-A2B` | 0,70 | 1 | 48 | 78,02% | nao | 0,484 | 0,089 |
| `20260903-180415-mary-g0.7-A2B` | 0,70 | 1 | 48 | 76,52% | nao | 0,512 | 0,095 |
| `20260903-180558-mary-g0.5-A2B` | 0,50 | 1 | 48 | 81,85% | nao | 0,470 | 0,097 |
| `20260903-180732-mary-g0.5-A2B` | 0,50 | 1 | 48 | 77,60% | nao | 0,565 | 0,104 |
| `20260903-180906-mary-g0.5-A2B` | 0,50 | 1 | 48 | 80,35% | nao | 0,537 | 0,106 |
| `20260903-181049-mary-g0.25-A2B` | 0,25 | 1 | 48 | 77,85% | nao | 0,396 | 0,081 |
| `20260903-181222-mary-g0.25-A2B` | 0,25 | 1 | 48 | 81,27% | nao | 0,441 | 0,084 |
| `20260903-181357-mary-g0.25-A2B` | 0,25 | 1 | 48 | 79,85% | nao | 0,416 | 0,081 |

Media de bits certos (gate): 79,05%. **Blocos inteiros: 0 de 12, em todos os
quatro pontos de ganho.**

## Relogio travado (`align.py`), por gravacao

| gravacao (ganho) | gate | relogio travado |
|---|---|---|
| 175617 (g1,0) | 80,9% | 83,7% |
| 175751 (g1,0) | 80,1% | 84,2% |
| 175925 (g1,0) | 79,7% | 84,3% |
| 180108 (g0,7) | 74,6% | 79,9% |
| 180242 (g0,7) | 78,0% | 80,8% |
| 180415 (g0,7) | 76,5% | 79,5% |
| 180558 (g0,5) | 81,8% | 83,6% |
| 180732 (g0,5) | 77,6% | 81,3% |
| 180906 (g0,5) | 80,3% | 82,0% |
| 181049 (g0,25) | 77,9% | 81,6% |
| 181222 (g0,25) | 81,3% | 84,8% |
| 181357 (g0,25) | 79,9% | 84,8% |

Agregado dos 12 (`align.py`): gate **79,1%**, 0 de 12 blocos; relogio travado
no melhor offset **82,6%**, 0 de 12; travado dividindo pelo ganho por tom
(o que um piloto mediria) **81,7%**, 1 de 12; travado dividindo pelo *ruido*
por tom (o que o codigo ja estima sozinho, sem piloto) **87,6%**, 4 de 12.
Todos os numeros conferidos rodando `align.py captures-a2b/08-mary-gain` de
novo -- **nenhuma divergencia** dos numeros repassados para esta tarefa.

## Leitura

**1. O ganho digital nao e a alavanca neste sentido.** Os quatro pontos
ficam empatados em 74,6-81,9% de bits pelo gate e 79,5-84,8% pelo relogio
travado, sem tendencia visivel entre 1,0 e 0,25 -- a dispersao entre os tres
trials do mesmo ganho (ate 5,4 pontos) e maior que qualquer diferenca entre
pontos de ganho vizinhos. Nenhum ponto entrega bloco.

**2. O nivel nao serve de regua de calibracao aqui, e isto esta medido em
dois lugares independentes.** O pico recebido quase nao responde ao ganho
digital: cortar 30% do ganho (1,0 -> 0,7) moveu o pico de 0,515-0,562 para
apenas 0,484-0,512, uma queda de ~7% para um corte de 30%. Em paralelo, o
teste `02-LVL-TONE-A2B` (tom puro, mesma cadeia) viu a margem sobre o piso
cair monotonicamente de 54,4 para 50,3 dB ao longo de cinco trials
acompanhando o pico, sem que o transmissor tivesse mudado nada. As duas
observacoes sao a assinatura de um controle automatico de ganho no
microfone de B comprimindo a faixa dinamica do que chega -- exatamente o que
o `TESTES.md` desconfiava ao recusar calibrar o sentido A->B por nivel.

**3. A cadeia A->B e muito pior que a B->A, e este e o resultado principal
desta pasta.** Pelo gate, esta campanha entrega 74,6-81,9% dos bits (18,1 a
25,4% errados); `resultados/14-FEC-REP/HEADER.md`, no sentido B->A, mesma
camada (mary, fecrep 1, gain 1,0), leu 90,5-94,1% pelo gate e 93,3% de media
pelo relogio travado. As duas cadeias nao se deduzem uma da outra -- ate
aqui so havia essa suspeita por `02-LVL-TONE`; agora ha o numero em bits.

**4. Por que zero blocos:** 18-25% de bits errados pelo gate (16-20% pelo
relogio travado) esta acima do que a taxa 1/3 sozinha aguenta -- o
`CLAUDE.md` registra rate 1/3 soft inteira ate 13% e 90% em 16% de erro de
bit. Nao e falha de sincronismo: o relogio travado no melhor offset so ganha
3,5 pontos sobre o gate (79,1% -> 82,6%), a mesma ordem de grandeza vista
onde o sincronismo *nao* era o problema em outras pastas -- se fosse colapso
de sincronismo a diferenca gate/travado seria muito maior (compare com
08-MARY-GAIN B->A, onde os dois blocos que colapsaram liam ~97% travado
contra falha total pelo gate). Aqui os dois numeros ficam proximos e ambos
ruins: o canal, nao o relogio, e o fator limitante.

**5. A linha "/ruido" (87,6%, 4/12) marca o teto, e aponta uma pista.** E o
estimador de piso por tom com a resposta do canal na mao -- nao disponivel
ao vivo. Que ele recupere 4 blocos onde o estimador cego (o que o codigo usa
de fato) recupera 0 sugere que, neste sentido, o piso por tom esta sendo
estimado pior do que no sentido B->A -- mas com 12 gravacoes isto e pista,
nao conclusao, e fica registrado como tal.

**6. Consequencia operacional.** O `gain 1,0` foi escolhido para a fase
seguinte da campanha (melhor bits pelo relogio travado entre os quatro
pontos, e maior nivel no receptor -- ainda que a diferenca de bits entre
pontos seja pequena demais para chamar de tendencia real). O teste 14
(`FEC-REP`) foi movido para antes dos demais nesta direcao, porque
`fecrep 1` aqui nao discrimina nada: zera blocos em todo o eixo de ganho, e
qualquer varredura fina precisa primeiro saber se ha redundancia suficiente
para ver diferenca.

## Ressalvas

- **3 trials por ponto.** A dispersao entre trials do mesmo ganho (ate 5,4
  pontos de bits) e maior que a diferenca entre pontos de ganho vizinhos --
  a leitura "sem tendencia" se apoia nisso, nao em uma media limpa.
- **A comparacao entre pontos de ganho e pareada no tempo apenas por ordem
  de gravacao** (~4 min por ponto, em sequencia); nao ha como isolar deriva
  temporal do AGC do efeito do ganho com este desenho.
- **`acerto_bits` no `resultado.csv` e a regua do gate** (posicao que
  `find_sync` escolheu ao vivo); "relogio travado" vem do `align.py`, que
  re-demodula com `steer=False` no melhor deslizamento por forca bruta. As
  duas reguas nao sao intercambiaveis -- ver `resultados/14-FEC-REP/HEADER.md`
  para a mesma distincao no sentido B->A.
- **`bloco_ok`** passa pelo caminho FEC real (sync por correlacao, Viterbi
  soft, comparacao de bytes). Com 0 de 12 em todo o eixo, ele nao discrimina
  ganho nesta pasta -- a leitura se apoia em bits, que e o que resta quando
  todo o eixo esta abaixo do ponto de quebra da taxa 1/3.
- `llr/*.csv` tem uma linha por simbolo -- quatro colunas em M-aria, quatro
  bits por simbolo. O tamanho do vetor soft nao e uma contagem de simbolos.

## Arquivos

- `gravacao/` -- as doze gravacoes, WAV float32 mais JSON
- `figuras/` -- espectrograma cru+contraste por gravacao (`resultado.py`),
  mais uma figura `*-leitura.png` por gravacao (`spectro.py --fundido
  --win 480`)
- `llr/` -- saida soft do demodulador, uma linha por simbolo
- `bits/` -- bits lidos contra bits transmitidos, alinhados no melhor
  deslizamento
- `resultado.csv` -- uma linha por gravacao (regua do gate)
