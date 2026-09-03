# 07-MARY-BASE -- M-ario 16 tons, linha de base

- **Codigo:** commit `2abc119` (main), que e `0718f2c` mais as ferramentas
  desta campanha.
- **Quando:** 2026-09-03, 16:16-16:23.
- **Camada:** M-ario, 16 tons, um por vez, 4 bits por simbolo, `fecrep 2`,
  com FEC (Viterbi de decisao suave).
- **Direcao:** B -> A. Caixa Bluetooth nova em B.
- **Payload:** 48 bytes aleatorios, tres baterias de 3 trials cada.

Pontuacao offline por `bench.py`. Figuras extras `*-leitura.png` geradas com
`spectro.py --fundido --win 480`, que sobrepoe o que foi interpretado sobre o
espectro real.

## Resultado

### Bateria 1 -- ganho 1.0, cadeia SATURADA (label `mary-base-B2A`)

rms ~0,48, **pico 1,000 nos tres**, 9,65% das amostras acima de 0,99.

| gravacao | resultado |
|---|---|
| 161643 | bloco INTEIRO |
| 161653 | 0/48 bytes |
| 161704 | 0/48 bytes |

**1 bloco inteiro de 3.**

### Bateria 2 -- ganho 0.5, ainda SATURADA (label `mary-base-g05-B2A`)

rms ~0,41, pico 1,000, 4,83% das amostras acima de 0,99. **Nao foram
pontuadas individualmente** -- descartadas por saturacao, registradas aqui
apenas com as gravacoes e figuras.

### Bateria 3 -- ganho 1.0, cadeia LINEAR (label `mary-base-limpo-B2A`), **valida**

| gravacao | rms | pico |
|---|---|---|
| 162209 | 0,0266 | 0,165 |
| 162220 | 0,0313 | 0,200 |
| 162230 | 0,0275 | 0,140 |

**3 blocos inteiros de 3.**

## O que mudou entre as baterias

Duas saturacoes foram corrigidas entre a bateria 2 e a bateria 3:

**(a) A caixa Bluetooth de B estava no volume maximo e limitando.**
Evidencia: cortar o ganho digital de 1.0 para 0.5 mudou o rms recebido so
17% (deveria cair pela metade), e o usuario ouviu que o som saia com a mesma
intensidade. Baixado para ~60% do volume.

**(b) O ganho de captura de A estava alto para o novo nivel.** Dmic0 baixado
de 55 (+5 dB) para 45 (-5 dB).

Depois disso, teste de linearidade confirmando (numeros informados, sem
gravacao/stem associado dado nesta mensagem): ganho 1,00 -> rms 0,0277; 0,50
-> 0,0162; 0,25 -> 0,0081. Cai aproximadamente proporcional (residuo de ~17%
por passo, provavel compressao suave restante).

## Leitura principal

Os 3 de 3 vieram com pico de 0,14 a 0,20 -- sinal fraco e limpo -- enquanto o
mesmo teste com pico 1,000 e 10% das amostras ceifadas dava 1 de 3.
**Linearidade valeu mais que amplitude.**

## Arquivos

- `gravacao/` -- as nove gravacoes das tres baterias, WAV float32 mais JSON
- `figuras/` -- espectro cru e contraste (600-3600 Hz) para as nove; mais uma
  figura `<stem>-leitura.png` por gravacao (`--fundido --win 480`) mostrando o
  que foi interpretado sobre o espectro real
- `resultado.csv` -- uma linha por gravacao; bateria 2 marcada
  `bloco_inteiro=nao_pontuado`
