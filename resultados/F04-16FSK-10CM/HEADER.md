# F04-16FSK-10CM

- **Codigo:** commit `213366c` (passada A), `c57fc74` (rodadas r1 a r4)
- **Quando:** 2026-10-08, passada A 16:47, rodadas r1 a r4 17:25 a 17:37
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm do mic e apontado -> A mic interno Linux (dispositivo padrao, Mic1), Dmic0 45 (-5 dB), Capture 39 (+12 dB), controle por tunel SSH
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Trials:** 5 gravacoes (1 passada A + 4 rodadas)

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-164832-f04-16fsk-10cm` | 0.5 | 1 | 48 | 100.00% | OK | 0.22 | 0.052 |
| `20261008-172827-f04-16fsk-10cm-r1` | 0.5 | 1 | 48 | 95.84% | OK | 0.18 | 0.036 |
| `20261008-173137-f04-16fsk-10cm-r2` | 0.5 | 1 | 48 | 97.09% | OK | 0.20 | 0.036 |
| `20261008-173422-f04-16fsk-10cm-r3` | 0.5 | 1 | 48 | 94.59% | OK | 0.17 | 0.035 |
| `20261008-173612-f04-16fsk-10cm-r4` | 0.5 | 1 | 48 | 94.92% | OK | 0.17 | 0.036 |

Media de bits certos: 96.49%. Blocos inteiros: 5 de 5.

## Por posicao

Posicao 1 = passada A (caixa a 10 cm, 16:47). Posicao 2 = rodadas r1 a r4: o usuario moveu levemente o PC entre uma e outra e a cauda do tom passou de -14,6 dB para cerca de -11 dB. A mudanca de posicao e uma variavel, nao so repeticao: as duas posicoes nao devem ser misturadas numa media unica.

| posicao | n | bits mediana | faixa | blocos | pico rx |
|---|---|---|---|---|---|
| 1 (passada A) | 1 | 100,00% | 100,00-100,00% | 1/1 | 0.22-0.22 |
| 2 (r1-r4) | 4 | 95,38% | 94,59-97,09% | 4/4 | 0.17-0.20 |

Bits = acerto antes do FEC no melhor deslizamento (`resultado.py`). Bloco = caminho FEC real (malha do gate, `find_sync` + Viterbi soft). Uma gravacao por condicao: n pequeno, a mediana da posicao 2 sobre 4 pontos e indicativa, nao estatistica.

## Reguas de sincronismo (align.py)

Mesma gravacao lida por tres reguas, em % de bits antes do FEC; todas fecharam o bloco (1/1) em todas as gravacoes. Erro do offset em amostras; periodo medido 480,00 amostras/simbolo em todas.

| grav | gate | relogio travado | duas varreduras | erro offset (amostras) |
|---|---|---|---|---|
| A | 100.0 | 100.0 | 100.0 | 120 |
| r1 | 95.8 | 96.0 | 96.3 | 99 |
| r2 | 97.1 | 97.3 | 96.8 | 1 |
| r3 | 94.6 | 95.6 | 94.6 | 65 |
| r4 | 94.9 | 96.8 | 96.1 | 67 |

- Posicao 2, gate: mediana 95,35 [94,6-97,1], 4/4 blocos.

- Posicao 2, travado: mediana 96,4 [95,6-97,3], 4/4 blocos.

- Posicao 2, duas varreduras: mediana 96,19 [94,6-96,8], 4/4 blocos.

## Bancada e ressalvas

- Metodo: 16-FSK + FEC, com duas varreduras, 48 bytes aleatorios, `fecrep 1`, ganho digital 0,5, B -> A apenas.
- Transmite B (Windows, agente `console.py`), alto-falante Realtek no P2, aprimoramentos de audio desligados, a 10 cm do microfone de A e apontado para ele. Grava A (Linux), dispositivo padrao (Mic1), Dmic0 45 = -5 dB, Capture 39 = +12 dB. Controle por tunel SSH, sem cabo serial.
- Commit `213366c` na passada A e `c57fc74` nas rodadas (o campo `-dirty` dos HEADERs antigos era a arvore com os resultados nao versionados).
- `resultado.py` reescreve o HEADER a cada chamada e deixava so a ultima gravacao; este arquivo foi refeito com as cinco, e `resultado.csv` regenerado pelo mesmo `resultado.py` sobre as cinco gravacoes de `gravacao/` (mesmo formato).
- Para refazer: `./venv/bin/python resultado.py F04-16FSK-10CM gravacao/*.json --out <dir> --bancada "..."` (e `align.py` para as reguas de F04/F06).

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
