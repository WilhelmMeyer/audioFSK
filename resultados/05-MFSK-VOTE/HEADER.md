# 05-MFSK-VOTE -- MFSK votado, dez tons, cinco pares

- **Codigo:** commit `2abc119` (main), que e `0718f2c` mais as ferramentas
  desta campanha.
- **Quando:** 2026-09-03, 15:57-15:58.
- **Camada:** MFSK votado. Dez tons, cinco pares, cada par vota qual dos dois
  tons chegou mais forte, 100 baud, `fecrep 2`, com FEC (Viterbi de decisao
  suave).
- **Direcao:** B -> A. B transmite, ganho 0.8; A grava pelo microfone interno,
  indice 26.
- **Payload:** 48 bytes aleatorios, 3 trials.

Pontuacao offline por `bench.py`.

## Resultado

| gravacao | rms | pico | bytes falhos | bloco |
|---|---|---|---|---|
| 155727 | 0,0799 | 0,351 | 0/48 | **INTEIRO** |
| 155755 | 0,0752 | 0,346 | 1/48 | falhou |
| 155823 | 0,0771 | 0,335 | 11/48 | falhou |

**1 bloco inteiro de 3.**

## Ressalvas obrigatorias

**Medido com a caixa ANTIGA da maquina B (alto-falante em P2), que foi trocada
depois.** Nao e comparavel com os testes 06, 07 e 08, que usam caixa
Bluetooth -- caminho eletroacustico diferente, entao rms e pico aqui nao se
comparam com os das outras pastas.

**A cadeia estava com distorcao audivel.** A metrica de distorcao acima da
banda (desenvolvida depois desta medida, ainda nao mergeada) da +0,7 a +1,8 dB
nestas gravacoes, abaixo do limiar de 3 dB usado la. Registrado porque a
distorcao foi ouvida, mas o instrumento que a mediria numericamente nao
confirma que ela seja o suficiente para explicar a falha.

**Uma atribuicao minha foi retirada.** Eu havia dito que os dois blocos
perdidos se explicavam por intermodulacao, medindo -13,5 dB de energia entre
tons vizinhos. Esse numero e a linha de base da propria modulacao (limpo da
-15,4 dB), nao e distorcao -- a diferenca entre os dois e pequena demais para
sustentar a leitura que eu tinha escrito. **A causa dos dois blocos perdidos
permanece desconhecida.**

## Arquivos

- `gravacao/` -- as tres gravacoes, WAV float32 mais JSON
- `figuras/` -- espectro cru e contraste, 600-3600 Hz
- `resultado.csv` -- uma linha por gravacao
