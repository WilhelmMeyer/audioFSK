# 06-MFSK-PAR -- MFSK paralelo, cinco bits por simbolo

- **Codigo:** commit `2abc119` (main), que e `0718f2c` mais as ferramentas
  desta campanha.
- **Quando:** 2026-09-03, 16:11-16:14.
- **Camada:** MFSK paralelo. Cada um dos cinco pares carrega um bit
  diferente (cinco bits por simbolo, em vez de um voto so), 100 baud,
  `fecrep 2`, com FEC.
- **Direcao:** B -> A. Caixa Bluetooth NOVA em B (diferente da 05, que usava a
  caixa antiga em P2).
- **Payload:** 48 bytes aleatorios, duas baterias de 3 trials cada.

Pontuacao offline por `bench.py`.

## Resultado

### Ganho 0.8 (label `mfsk-par-B2A`)

| gravacao | rms | pico | bytes certos |
|---|---|---|---|
| 161136 | 0,0531 | 0,288 | 0/48 |
| 161145 | 0,0544 | 0,299 | 46/48 |
| 161154 | 0,0508 | 0,296 | 21/48 |

**Nenhum bloco inteiro.**

### Ganho 1.0 (label `mfsk-par-g10-B2A`)

| gravacao | rms | pico | bytes certos |
|---|---|---|---|
| 161413 | 0,0641 | 0,376 | 26/48 |
| 161422 | 0,0638 | 0,353 | 29/48 |
| 161432 | 0,0646 | 0,350 | 20/48 |

**Nenhum bloco inteiro.**

## Ressalvas

**As duas baterias empatam dentro do ruido.** Tres trials nao distinguem 0.8
de 1.0 aqui -- os bytes certos variam mais entre trials do mesmo ganho do que
entre os dois ganhos.

**Medido ANTES da correcao da cadeia.** O receptor local estava com ganho de
captura alto demais e a caixa de B no volume maximo, limitando -- ou seja,
esta medida inteira e em cadeia nao linear. A correcao (baixar o volume de B e
o ganho de captura de A) so acontece depois, entre este teste e o 07.

## Leitura

**Paralelo e pior que voto neste link.** Compare com 05-MFSK-VOTE: o voto
recuperou 1 bloco inteiro de 3 mesmo com distorcao audivel e caixa antiga; o
paralelo nao recuperou nenhum, em nenhum dos dois ganhos, com a caixa nova.

O que protege um bit e o numero de observacoes independentes dele. O voto da
cinco observacoes do MESMO bit; o paralelo troca isso por uma observacao de
cada um de cinco bits diferentes -- a mesma capacidade do canal, dividida de
outro jeito. Paralelismo nao cria robustez, cria um dial: so compensa em canal
com margem sobrando, e este link, medido em cadeia nao linear, nao tinha essa
margem.

## Arquivos

- `gravacao/` -- as seis gravacoes (duas baterias de tres), WAV float32 mais
  JSON
- `figuras/` -- espectro cru e contraste, 600-3600 Hz
- `resultado.csv` -- uma linha por gravacao
