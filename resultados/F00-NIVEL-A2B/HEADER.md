# F00-NIVEL-A2B

- **Codigo:** commit `c57fc74-dirty`
- **Quando:** 2026-10-08 16:43:15
- **Bancada:** A Linux alto-falante interno max -> B Windows mic WDM-KS 15 Microfone 1 SST, tunel SSH, 213366c
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-164304-a2b-f00-nivel-wdmks1` | 0.5 | 1 | 48 | 71.61% | nao | 0.27 | 0.052 |

Media de bits certos: 71.61%. Blocos inteiros: 0 de 1.

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
