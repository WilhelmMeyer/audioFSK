# H02-16FSK-MALHA

- **Codigo:** commit `6f03e47-dirty`
- **Quando:** 2026-10-08 18:16:20
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm do mic -> A mic interno Linux (Mic1) Dmic0 45 Capture 39, posicao 2 (PC levemente deslocado, cauda ~-11 dB), tunel SSH, commit c57fc74, 2026-10-08 18:05-18:10
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 4 gravacoes

16-FSK sem varreduras, so malha (gate). r1-r4 estao em F00-NIVEL-10CM.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-180602-f00-nivel-10cm-r5` | 0.5 | 1 | 48 | 96.84% | OK | 0.18 | 0.035 |
| `20261008-180723-f00-nivel-10cm-r6` | 0.5 | 1 | 48 | 95.25% | OK | 0.18 | 0.035 |
| `20261008-180848-f00-nivel-10cm-r7` | 0.5 | 1 | 48 | 93.92% | nao | 0.18 | 0.035 |
| `20261008-181001-f00-nivel-10cm-r8` | 0.5 | 1 | 48 | 95.17% | OK | 0.18 | 0.034 |

Media de bits certos: 95.30%. Blocos inteiros: 3 de 4.

## Como ler

`acerto_bits` e medido no melhor deslizamento por forca bruta, sempre,
e nunca na posicao que o `find_sync` escolheu -- misturar as duas reguas
faz as falhas pontuarem mais alto que os acertos. `bloco_ok` e o numero
honesto separado: passa pelo caminho FEC de verdade (sync por correlacao,
Viterbi soft, comparacao dos bytes) e e o que o enlace de fato entregou.
Com poucas gravacoes ele e ruidoso; nao ajuste parametro por ele.

`llr/*.csv` tem uma linha por simbolo. Em M-aria sao quatro colunas,
porque sao quatro bits por simbolo: o tamanho do vetor soft nao e uma
contagem de simbolos.

## Arquivos

- `gravacao/` -- wav 32-bit float + json, formato de `recording.py`
- `llr/` -- saida soft do demodulador, uma linha por simbolo
- `bits/` -- bits lidos contra bits transmitidos, alinhados
- `figuras/` -- espectrograma por gravacao
- `resultado.csv` -- uma linha por gravacao

## Leitura (16-FSK sem varreduras, so malha, r5 a r8)

Bits: 96.84 OK, 95.25 OK, 93.92 nao, 95.17 OK. Junto com r1-r4 (92.92 nao, 95.50 nao, 98.33 OK, 95.34 OK): 5 de 8 blocos. Mesma posicao 2: 16-FSK com varreduras 7/8 e com IFK 8/8.
