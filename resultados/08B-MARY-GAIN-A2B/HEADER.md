# 08B-MARY-GAIN-A2B

- **Codigo:** commit `82ef87b-dirty`
- **Quando:** 2026-09-03 20:09:31
- **Bancada:** nao informada
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 12 gravacoes

Varredura de ganho digital A->B com a caixa de A em 0.45 no PipeWire (o teste 08 original foi em 1.00). fecrep 1, 48 bytes, 3 trials por ponto.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-192442-spk45-g0.5-A2B` | 0.5 | 1 | 48 | 83.18% | nao | 0.19 | 0.027 |
| `20260903-192616-spk45-g0.5-A2B` | 0.5 | 1 | 48 | 85.68% | nao | 0.13 | 0.023 |
| `20260903-192750-spk45-g0.5-A2B` | 0.5 | 1 | 48 | 80.77% | nao | 0.14 | 0.023 |
| `20260903-192927-spk45-g0.35-A2B` | 0.35 | 1 | 48 | 85.43% | OK | 0.11 | 0.017 |
| `20260903-193100-spk45-g0.35-A2B` | 0.35 | 1 | 48 | 82.85% | nao | 0.10 | 0.017 |
| `20260903-193234-spk45-g0.35-A2B` | 0.35 | 1 | 48 | 81.10% | nao | 0.09 | 0.017 |
| `20260903-193411-spk45-g0.15-A2B` | 0.15 | 1 | 48 | 83.10% | nao | 0.10 | 0.014 |
| `20260903-193545-spk45-g0.15-A2B` | 0.15 | 1 | 48 | 83.76% | nao | 0.12 | 0.015 |
| `20260903-193720-spk45-g0.15-A2B` | 0.15 | 1 | 48 | 88.18% | OK | 0.11 | 0.012 |
| `20260903-193858-spk45-g0.10-A2B` | 0.1 | 1 | 48 | 90.84% | OK | 0.10 | 0.013 |
| `20260903-194033-spk45-g0.10-A2B` | 0.1 | 1 | 48 | 85.26% | nao | 0.18 | 0.015 |
| `20260903-194208-spk45-g0.10-A2B` | 0.1 | 1 | 48 | 86.34% | OK | 0.19 | 0.019 |

Media de bits certos: 84.71%. Blocos inteiros: 4 de 12.

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
