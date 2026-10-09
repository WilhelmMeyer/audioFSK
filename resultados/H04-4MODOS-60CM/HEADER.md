# H04-4MODOS-60CM

- **Codigo:** commit `7d6d6d4-dirty`
- **Quando:** 2026-10-08 21:02:40
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 60 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 7d6d6d4
- **Camada:** mfsk, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-210237-h04-multicanal-r4` | 0.5 | 1 | 48 | 90.72% | OK | 0.10 | 0.016 |

Media de bits certos: 90.72%. Blocos inteiros: 1 de 1.

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

## Leitura (2026-10-08)

Os quatro modos, 4 rodadas, ordem girando: 16 de 16 blocos inteiros a 60 cm. 2-FSK 100% (a malha sozinha perderia 2 dos 4 blocos), votada 99,4-99,8%, multicanal 89,8-91,7%, 16-FSK 95,3-100% (primeira distancia em que sai de 100%). Picos 0,08-0,18.
