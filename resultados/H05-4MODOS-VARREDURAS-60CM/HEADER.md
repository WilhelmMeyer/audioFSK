# H05-4MODOS-VARREDURAS-60CM

- **Codigo:** commit `7f40e49-dirty`
- **Quando:** 2026-10-08 21:31:25
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 60 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 7f40e49
- **Camada:** mfsk, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | sincronismo | bits | bloco | bits gate | bloco gate | pico | rms |
|---|---|---|---|---|---|---|---|---|---|---|
| `20261008-213122-h05-multicanal-r4` | 0.5 | 1 | 48 | duas varreduras | 91.47% | OK | 91.85% | OK | 0.14 | 0.017 |

Media de bits certos: 91.47%. Blocos inteiros: 1 de 1.
So o gate, nas 1 gravacoes com varredura: 91.85% de bits, 1 de 1 blocos.

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

Os quatro modos com varreduras (commit 7f40e49 nas duas maquinas), 60 cm, 4 rodadas, ordem girando: 16 de 16 blocos. 2-FSK 99,9-100% (a malha sozinha perderia os 4), votada 100% nas 4, 16-FSK 98,8-99,8%, multicanal 89,6-91,5%. Na multicanal o erro nao e sincronismo: align.py --mode mfsk-par da gate 90,8%, melhor offset travado 91,2%, duas varreduras 90,4%. O que falta a ela e sinal por tom (potencia dividida por 10 tons).
