# H04-4MODOS-20CM

- **Codigo:** commit `1023679-dirty`
- **Quando:** 2026-10-08 19:48:24
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 20 cm, apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH; gravado em 8355840/0e10364, pontuado em 0e10364
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
| `20261008-191024-h04-2fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 96.09% | nao | 0.26 | 0.068 |
| `20261008-191125-h04-votada-r1` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.18 | 0.041 |
| `20261008-191217-h04-multicanal-r1` | 0.5 | 1 | 48 | gate | 99.55% | OK | -- | -- | 0.16 | 0.034 |
| `20261008-191300-h04-16fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 99.83% | OK | 0.31 | 0.069 |
| `20261008-193053-h04-votada-r2` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.17 | 0.041 |
| `20261008-193143-h04-multicanal-r2` | 0.5 | 1 | 48 | gate | 99.40% | OK | -- | -- | 0.16 | 0.033 |
| `20261008-193236-h04-16fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.31 | 0.068 |
| `20261008-193836-h04-2fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 98.58% | nao | 0.26 | 0.067 |
| `20261008-193858-h04-multicanal-r3` | 0.5 | 1 | 48 | gate | 99.77% | OK | -- | -- | 0.16 | 0.033 |
| `20261008-193912-h04-16fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 99.83% | OK | 0.31 | 0.069 |
| `20261008-193938-h04-2fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.25 | 0.068 |
| `20261008-194000-h04-votada-r3` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.16 | 0.041 |
| `20261008-194015-h04-16fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 99.83% | OK | 0.31 | 0.069 |
| `20261008-194037-h04-2fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 100.00% | OK | 0.26 | 0.068 |
| `20261008-194103-h04-votada-r4` | 0.5 | 1 | 48 | gate | 100.00% | OK | -- | -- | 0.17 | 0.041 |
| `20261008-194117-h04-multicanal-r4` | 0.5 | 1 | 48 | gate | 99.92% | OK | -- | -- | 0.15 | 0.033 |

Media de bits certos: 99.91%. Blocos inteiros: 16 de 16.
So o gate, nas 8 gravacoes com varredura: 99.27% de bits, 6 de 8 blocos.

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

Os quatro modos do artigo, 4 rodadas, ordem girando uma casa por rodada: 2-FSK (`fsk2`, FEC, varreduras), 5x2 votada, 5x2 multicanal, 16-FSK com varreduras. 16 de 16 blocos inteiros a 20 cm. As rodadas 1-2 a 20 cm foram gravadas com outro processo pesado na maquina (carga ~50); nenhuma saiu pior por isso.
