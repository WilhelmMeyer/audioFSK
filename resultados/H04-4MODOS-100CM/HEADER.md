# H04-4MODOS-100CM

- **Codigo:** commit `24f9aff-dirty`
- **Quando:** 2026-10-08 21:39:14
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 100 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 24f9aff
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
| `20261008-213911-h04-multicanal-r4` | 0.5 | 1 | 48 | 80.75% | nao | 0.08 | 0.015 |

Media de bits certos: 80.75%. Blocos inteiros: 0 de 1.

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

1 m, 4 rodadas, ordem girando. 2-FSK 4/4 (99,9-100%; a malha sozinha perderia 3 dos 4), 16-FSK 4/4 (94,7-96,4%), votada 3/4 (95,8-98,2% nas que fecharam), multicanal 0/4 (77,4-80,8%). A votada da rodada 2 (76,7%) chegou com pico 0,18, o dobro das outras votadas (0,09): provavel evento sonoro na sala durante a gravacao, nao o canal.
