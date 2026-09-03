# 17-SPK-LEVEL-A2B

- **Codigo:** commit `82ef87b-dirty`
- **Quando:** 2026-09-03 20:10:20
- **Bancada:** nao informada
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 12 gravacoes

Volume da caixa de A como eixo varrido (0.20 e 0.10), com o ganho digital fixo em 0.5 para o par comparavel, mais 1.0 e 0.25 em 0.20. fecrep 1, 48 bytes, 3 trials por ponto.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-194719-spk20-g0.5-A2B` | 0.5 | 1 | 48 | 87.26% | OK | 0.09 | 0.012 |
| `20260903-194853-spk20-g0.5-A2B` | 0.5 | 1 | 48 | 85.35% | OK | 0.10 | 0.010 |
| `20260903-195028-spk20-g0.5-A2B` | 0.5 | 1 | 48 | 85.76% | nao | 0.06 | 0.011 |
| `20260903-195247-spk10-g0.5-A2B` | 0.5 | 1 | 48 | 80.93% | nao | 0.16 | 0.005 |
| `20260903-195422-spk10-g0.5-A2B` | 0.5 | 1 | 48 | 72.52% | nao | 0.21 | 0.019 |
| `20260903-195557-spk10-g0.5-A2B` | 0.5 | 1 | 48 | 86.51% | OK | 0.09 | 0.007 |
| `20260903-195822-spk20-g1.0-A2B` | 1.0 | 1 | 48 | 82.93% | nao | 0.08 | 0.011 |
| `20260903-195956-spk20-g1.0-A2B` | 1.0 | 1 | 48 | 90.76% | OK | 0.09 | 0.012 |
| `20260903-200131-spk20-g1.0-A2B` | 1.0 | 1 | 48 | 85.93% | OK | 0.12 | 0.018 |
| `20260903-200309-spk20-g0.25-A2B` | 0.25 | 1 | 48 | 85.85% | OK | 0.08 | 0.010 |
| `20260903-200444-spk20-g0.25-A2B` | 0.25 | 1 | 48 | 77.94% | nao | 0.18 | 0.015 |
| `20260903-200619-spk20-g0.25-A2B` | 0.25 | 1 | 48 | 83.26% | nao | 0.13 | 0.007 |

Media de bits certos: 83.75%. Blocos inteiros: 6 de 12.

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
