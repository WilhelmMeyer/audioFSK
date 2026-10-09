# H06-IFK-2M-B

- **Codigo:** commit `516f334-dirty`
- **Quando:** 2026-10-08 22:39:16
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 200 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 516f334
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | sincronismo | bits | bloco | bits gate | bloco gate | pico | rms |
|---|---|---|---|---|---|---|---|---|---|---|
| `20261008-223913-h06-ifk-r4` | 0.5 | 1 | 48 | duas varreduras | 85.68% | nao | 81.60% | nao | 0.09 | 0.016 |

Media de bits certos: 85.68%. Blocos inteiros: 0 de 1.
So o gate, nas 1 gravacoes com varredura: 81.60% de bits, 0 de 1 blocos.

## Como ler

`acerto_bits` e medido no melhor deslizamento por forca bruta, sempre,
e nunca na posicao que o `find_sync` escolheu -- misturar as duas reguas
faz as falhas pontuarem mais alto que os acertos. `bloco_ok` e o numero
honesto separado: passa pelo caminho FEC de verdade (sync por correlacao,
Viterbi soft, comparacao dos bytes) e e o que o enlace de fato entregou.
Com poucas gravacoes ele e ruidoso; nao ajuste parametro por ele.

**Duas reguas de sincronismo.** Nas gravacoes com `sync_chirp`,
`acerto_bits` e `bloco_ok` saem do audio relido como o receptor ao
vivo o rele (`modem.sweep_soft`, o mesmo de `console.py`): relogio
congelado, inicio na varredura de abertura e periodo medido entre as
duas (`sincronismo` = duas varreduras). Se o par nao serve, so a de
abertura com relogio nominal (uma varredura); se nenhuma aparece, o
gate, e a coluna diz. `acerto_bits_gate` e `bloco_ok_gate` sao a
leitura pelo gate early/late, como esta ferramenta fazia antes --
pessimista nessas gravacoes, porque o gate toma a varredura pelos
primeiros simbolos do preambulo. Gravacoes sem varredura so tem a
regua do gate, nas colunas sem sufixo. `span_simbolos` e o vao entre
as varreduras calculado como o receptor calcula (`fec.sweep_span`);
`span_json` e o que o gravador carimbou, so para conferencia.
`llr/` e `bits/` saem da regua principal.

`llr/*.csv` tem uma linha por simbolo. Em M-aria sao quatro colunas,
porque sao quatro bits por simbolo: o tamanho do vetor soft nao e uma
contagem de simbolos.

## Arquivos

- `gravacao/` -- wav 32-bit float + json, formato de `recording.py`
- `llr/` -- saida soft do demodulador, uma linha por simbolo
- `bits/` -- bits lidos contra bits transmitidos, alinhados
- `figuras/` -- espectrograma por gravacao
- `resultado.csv` -- uma linha por gravacao

## Leitura (2026-10-08)

Repeticao do H06 a ~2 m, sala sem interferencia de outra sessao. Bits com IFK / sem: 88,26/87,09 (+1,2), 89,43/83,68 (+5,8), 89,01/83,51 (+5,5), 85,68/83,51 (+2,2). IFK a favor em 4 de 4, media +3,6 pontos (contra +1 a +2 a 10 cm). Blocos: 2/4 com IFK, 2/4 sem -- a ~85-89% de bits o bloco fecha ou nao por sorte (uma gravacao sem IFK fechou com 83,5%, uma com IFK falhou com 89,0%), entao blocos nao separam as duas. Somando H06 e H06-B: IFK a favor em 7 de 8 pares, media +3,0 pontos.
