# H04-4MODOS-10CM

- **Codigo:** commit `0e10364-dirty`
- **Quando:** 2026-10-08 19:47:43
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, ~10 cm (posicao 3, reposicionada pelo usuario), apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH; gravado em 8355840/0e10364, pontuado em 0e10364
- **Camada:** fsk2, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 16 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | sincronismo | bits | bloco | bits gate | bloco gate | pico | rms |
|---|---|---|---|---|---|---|---|---|---|---|
| `20261008-190318-h04-2fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.27 | 0.109 |
| `20261008-190341-h04-votada-r1` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.045 |
| `20261008-190355-h04-multicanal-r1` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.037 |
| `20261008-190408-h04-16fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.31 | 0.072 |
| `20261008-190434-h04-votada-r2` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.045 |
| `20261008-190448-h04-multicanal-r2` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.17 | 0.036 |
| `20261008-190500-h04-16fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.32 | 0.075 |
| `20261008-190523-h04-2fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.25 | 0.102 |
| `20261008-190536-h04-multicanal-r3` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.037 |
| `20261008-190548-h04-16fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.30 | 0.075 |
| `20261008-190611-h04-2fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.25 | 0.103 |
| `20261008-190634-h04-votada-r3` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.045 |
| `20261008-190650-h04-16fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.30 | 0.074 |
| `20261008-190711-h04-2fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 98.50% | nao | 0.28 | 0.102 |
| `20261008-190734-h04-votada-r4` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.045 |
| `20261008-190749-h04-multicanal-r4` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.17 | 0.037 |

Media de bits certos: 100.00%. Blocos inteiros: 16 de 16.
So o gate, nas 8 gravacoes com varredura: 99.81% de bits, 7 de 8 blocos.

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

Os quatro modos do artigo, 4 rodadas, ordem girando uma casa por rodada: 2-FSK (`fsk2`, FEC, varreduras), 5x2 votada, 5x2 multicanal, 16-FSK com varreduras. 16 de 16 blocos inteiros a 10 cm. As rodadas 1-2 a 20 cm foram gravadas com outro processo pesado na maquina (carga ~50); nenhuma saiu pior por isso.
