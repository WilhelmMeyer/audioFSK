# H03-2FSK-FEC

- **Codigo:** commit `0e10364-dirty`
- **Quando:** 2026-10-08 19:47:01
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm (posicao 2, a mesma da campanha anterior), apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH; gravado em 8355840/0e10364, pontuado em 0e10364
- **Camada:** fsk2, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 12 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | sincronismo | bits | bloco | bits gate | bloco gate | pico | rms |
|---|---|---|---|---|---|---|---|---|---|---|
| `20261008-184232-h03-2fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 98.92% | OK | 98.75% | OK | 0.18 | 0.056 |
| `20261008-184258-h03-16fsk-r1` | 0.5 | 1 | 48 | duas varreduras | 99.00% | OK | 98.25% | OK | 0.17 | 0.035 |
| `20261008-184339-h03-votada-r1` | 0.5 | 1 | 48 | gate | 99.83% | OK | -- | -- | 0.12 | 0.030 |
| `20261008-184444-h03-votada-r2` | 0.5 | 1 | 48 | gate | 98.75% | OK | -- | -- | 0.12 | 0.027 |
| `20261008-184530-h03-16fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 97.34% | OK | 96.84% | OK | 0.19 | 0.037 |
| `20261008-184635-h03-2fsk-r2` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 99.67% | OK | 0.15 | 0.050 |
| `20261008-184735-h03-2fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 100.00% | OK | 99.17% | OK | 0.14 | 0.049 |
| `20261008-184820-h03-16fsk-r3` | 0.5 | 1 | 48 | duas varreduras | 83.35% | nao | 80.85% | nao | 0.16 | 0.034 |
| `20261008-184912-h03-votada-r3` | 0.5 | 1 | 48 | gate | 98.92% | OK | -- | -- | 0.11 | 0.025 |
| `20261008-184959-h03-votada-r4` | 0.5 | 1 | 48 | gate | 99.42% | OK | -- | -- | 0.10 | 0.022 |
| `20261008-185056-h03-16fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 97.17% | OK | 95.42% | nao | 0.20 | 0.042 |
| `20261008-185159-h03-2fsk-r4` | 0.5 | 1 | 48 | duas varreduras | 99.58% | OK | 98.42% | OK | 0.20 | 0.049 |

Media de bits certos: 97.69%. Blocos inteiros: 11 de 12.
So o gate, nas 8 gravacoes com varredura: 95.92% de bits, 6 de 8 blocos.

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

Pergunta: o 2-FSK falha por ser 2-FSK ou pelo jeito do Bell 202 (1200 baud, discriminador por sinal, sem FEC)? O `fsk2` (1700/2350 Hz, 100 baud, energia/piso, FEC, varreduras) leu 98,4–100% e fechou 4/4; a votada 4/4; o 16-FSK 3/4. A falha do 16-FSK na rodada 3 (83%) nao e sincronismo: o melhor offset travado tambem da 83%. A posicao desta pasta era a 2 (cauda ~-11 dB); o usuario reposicionou depois e repetiu em H04.
