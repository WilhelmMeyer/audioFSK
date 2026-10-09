# H06-IFK-2M-C

- **Codigo:** commit `b27660e-dirty`
- **Quando:** 2026-10-08 22:43:01
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 200 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit b27660e
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
| `20261008-224258-h06-ifk-r4` | 0.5 | 1 | 48 | duas varreduras | 87.76% | OK | 85.43% | OK | 0.11 | 0.022 |

Media de bits certos: 87.76%. Blocos inteiros: 1 de 1.
So o gate, nas 1 gravacoes com varredura: 85.43% de bits, 1 de 1 blocos.

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

Repeticao do H06 a ~2 m com o usuario fora da sala. Bits com IFK / sem: 85,43/84,60 (+0,8), 88,84/82,76 (+6,1), 89,18/82,93 (+6,3), 87,76/84,18 (+3,6). IFK a favor em 4 de 4, media +4,2 pontos. Blocos: 3/4 com IFK, 1/4 sem. Picos 0,10-0,11, iguais aos de H06 e H06-B: a ausencia do usuario nao recuperou os ~3 dB perdidos desde H04-4MODOS-200CM, entao a queda nao era a presenca (causa nao identificada; a posicao exata da caixa e a suspeita mais simples).

Somando H06, H06-B e H06-C (12 pares, ~2 m): IFK a favor em 11 de 12, media +3,4 pontos de bits; blocos 5/12 com IFK contra 3/12 sem.
