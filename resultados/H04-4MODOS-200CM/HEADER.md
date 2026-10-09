# H04-4MODOS-200CM

- **Codigo:** commit `443e54e-dirty`
- **Quando:** 2026-10-08 21:50:44
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 200 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 443e54e
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
| `20261008-215041-h04-multicanal-r4` | 0.5 | 1 | 48 | 69.36% | nao | 0.06 | 0.009 |

Media de bits certos: 69.36%. Blocos inteiros: 0 de 1.

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

2 m, 4 rodadas, ordem girando. 2-FSK 4/4 (93,3-94,7%), 16-FSK 4/4 (87,1-89,8%), votada 0/4 (65,9-73,7%), multicanal 0/4 (59,3-69,4%). As duas camadas de acorde (cinco tons de uma vez, cada um ~14 dB abaixo) caem primeiro; as de um tom por vez fecham tudo. Picos: 0,12-0,15 nas de um tom, 0,05-0,06 nas de acorde.
