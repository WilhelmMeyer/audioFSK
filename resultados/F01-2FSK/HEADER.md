# F01-2FSK

- **Codigo:** commit `213366c-dirty`
- **Quando:** 2026-10-08 16:31:53
- **Bancada:** B Windows P2 Realtek sem aprimoramentos, caixa reposicionada -> A mic26 Dmic0 45 Capture 39, tunel SSH, 213366c
- **Camada:** fsk, sem FEC
- **Amostragem:** 48000 Hz, 1200 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-163150-f01-2fsk-v4` | 0.5 | 0 | 48 | 53.54% | nao | 0.28 | 0.029 |

Media de bits certos: 53.54%. Blocos inteiros: 0 de 1.

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

## Figuras que falharam

Uma figura quebrada nao derruba a coleta; fica registrada aqui.

- `20261008-163150-f01-2fsk-v4`: codigo 1: [spectro] --ideal precisa de uma captura com --fec
