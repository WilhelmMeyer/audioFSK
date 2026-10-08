# H01-IFK-ORDEM-INVERTIDA

- **Codigo:** commit `6f03e47-dirty`
- **Quando:** 2026-10-08 18:15:48
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm do mic -> A mic interno Linux (Mic1) Dmic0 45 Capture 39, posicao 2 (PC levemente deslocado, cauda ~-11 dB), tunel SSH, commit c57fc74, 2026-10-08 18:05-18:10
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 8 gravacoes

r5-r8: ordem invertida, IFK (f06) primeiro e sem IFK (f04) ~20 s depois; r1-r4 em F06-16FSK-IFK-10CM tinham IFK em segundo.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-180524-f06-16fsk-ifk-10cm-r5` | 0.5 | 1 | 48 | 96.50% | OK | 0.18 | 0.034 |
| `20261008-180625-f06-16fsk-ifk-10cm-r6` | 0.5 | 1 | 48 | 97.09% | OK | 0.18 | 0.035 |
| `20261008-180752-f06-16fsk-ifk-10cm-r7` | 0.5 | 1 | 48 | 97.50% | OK | 0.17 | 0.034 |
| `20261008-180922-f06-16fsk-ifk-10cm-r8` | 0.5 | 1 | 48 | 98.17% | OK | 0.18 | 0.035 |
| `20261008-180544-f04-16fsk-10cm-r5` | 0.5 | 1 | 48 | 95.84% | OK | 0.17 | 0.035 |
| `20261008-180656-f04-16fsk-10cm-r6` | 0.5 | 1 | 48 | 95.67% | nao | 0.18 | 0.036 |
| `20261008-180819-f04-16fsk-10cm-r7` | 0.5 | 1 | 48 | 95.50% | OK | 0.18 | 0.035 |
| `20261008-180940-f04-16fsk-10cm-r8` | 0.5 | 1 | 48 | 97.50% | OK | 0.20 | 0.035 |

Media de bits certos: 96.72%. Blocos inteiros: 7 de 8.

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

## Leitura (ordem invertida, r5 a r8)

Ordem por rodada: IFK (f06) primeiro, sem IFK (f04) cerca de 20 s depois, o inverso de r1-r4 (`F06-16FSK-IFK-10CM`). Bits antes do FEC, `align.py`:

| rodada | malha IFK / sem | relogio travado IFK / sem | duas varreduras IFK / sem |
|---|---|---|---|
| r5 | 96.5 / 95.8 | 97.9 / 96.3 | 98.3 / 96.9 |
| r6 | 97.1 / 95.7 | 98.1 / 96.7 | 98.3 / 97.2 |
| r7 | 97.5 / 95.5 | 98.7 / 97.3 | 99.0 / 97.3 |
| r8 | 98.2 / 97.5 | 98.9 / 97.8 | 98.9 / 97.9 |

Diferenca IFK menos sem: malha +0.7 +1.4 +2.0 +0.7; travado +1.6 +1.4 +1.4 +1.1; varreduras +1.4 +1.1 +1.7 +1.0. Blocos pela malha: IFK 4/4, sem IFK 3/4 (r6 nao); blocos pelas varreduras iguais.
Junto com r1-r4 (IFK em segundo, +0.9 a +4.1, media ~+2.5): IFK melhor em 8 de 8 pares, nas duas ordens. Ganho menor na ordem invertida (~+1.3), entao parte do efeito anterior era ordem/deriva. Afirmacao: +1 a +2 pt de bits nesta bancada, sem diferenca de blocos.
