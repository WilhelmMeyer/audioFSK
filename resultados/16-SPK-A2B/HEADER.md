# 16-SPK-A2B

- **Codigo:** commit `82ef87b-dirty`
- **Quando:** 2026-09-03 19:23:20
- **Bancada:** nao informada
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 1.0
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 6 gravacoes

Caixa de A baixada de 1.00 para 0.45 no PipeWire. Dois ganhos digitais, 3 trials cada.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-185041-spk45-g1.0-A2B` | 1.0 | 1 | 48 | 74.94% | nao | 0.36 | 0.066 |
| `20260903-185221-spk45-g1.0-A2B` | 1.0 | 1 | 48 | 78.27% | nao | 0.34 | 0.057 |
| `20260903-185401-spk45-g1.0-A2B` | 1.0 | 1 | 48 | 84.10% | nao | 0.38 | 0.064 |
| `20260903-185801-spk45-g0.25-A2B` | 0.25 | 1 | 48 | 84.18% | nao | 0.12 | 0.017 |
| `20260903-185935-spk45-g0.25-A2B` | 0.25 | 1 | 48 | 88.34% | OK | 0.17 | 0.026 |
| `20260903-190111-spk45-g0.25-A2B` | 0.25 | 1 | 48 | 85.51% | OK | 0.10 | 0.015 |

Media de bits certos: 82.56%. Blocos inteiros: 2 de 6.

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
