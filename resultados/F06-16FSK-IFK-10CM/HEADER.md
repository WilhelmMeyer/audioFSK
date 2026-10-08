# F06-16FSK-IFK-10CM

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
| `20261008-164852-f06-16fsk-ifk-10cm` | 0.5 | 1 | 48 | 98.75% | OK | 0.24 | 0.051 |
| `20261008-172852-f06-16fsk-ifk-10cm-r1` | 0.5 | 1 | 48 | 96.75% | OK | 0.17 | 0.035 |
| `20261008-173217-f06-16fsk-ifk-10cm-r2` | 0.5 | 1 | 48 | 99.08% | OK | 0.18 | 0.036 |
| `20261008-173441-f06-16fsk-ifk-10cm-r3` | 0.5 | 1 | 48 | 98.25% | OK | 0.18 | 0.035 |
| `20261008-173631-f06-16fsk-ifk-10cm-r4` | 0.5 | 1 | 48 | 97.92% | OK | 0.21 | 0.036 |

Media de bits certos: 98.15%. Blocos inteiros: 5 de 5.

## Por posicao

Posicao 1 = passada A (caixa a 10 cm, 16:47). Posicao 2 = rodadas r1 a r4: o usuario moveu levemente o PC entre uma e outra e a cauda do tom passou de -14,6 dB para cerca de -11 dB. A mudanca de posicao e uma variavel, nao so repeticao: as duas posicoes nao devem ser misturadas numa media unica.

| posicao | n | bits mediana | faixa | blocos | pico rx |
|---|---|---|---|---|---|
| 1 (passada A) | 1 | 98,75% | 98,75-98,75% | 1/1 | 0.24-0.24 |
| 2 (r1-r4) | 4 | 98,09% | 96,75-99,08% | 4/4 | 0.17-0.21 |

Bits = acerto antes do FEC no melhor deslizamento (`resultado.py`). Bloco = caminho FEC real (malha do gate, `find_sync` + Viterbi soft). Uma gravacao por condicao: n pequeno, a mediana da posicao 2 sobre 4 pontos e indicativa, nao estatistica.

## Reguas de sincronismo (align.py)

Mesma gravacao lida por tres reguas, em % de bits antes do FEC; todas fecharam o bloco (1/1) em todas as gravacoes. Erro do offset em amostras; periodo medido 480,00 amostras/simbolo em todas.

| grav | gate | relogio travado | duas varreduras | erro offset (amostras) |
|---|---|---|---|---|
| A | 98.8 | 99.7 | 99.0 | 50 |
| r1 | 96.8 | 98.6 | 98.4 | 44 |
| r2 | 99.1 | 99.5 | 99.4 | 19 |
| r3 | 98.3 | 98.4 | 98.7 | 20 |
| r4 | 97.9 | 98.7 | 98.2 | 62 |

- Posicao 2, gate: mediana 98,1 [96,8-99,1], 4/4 blocos.

- Posicao 2, travado: mediana 98,65 [98,4-99,5], 4/4 blocos.

- Posicao 2, duas varreduras: mediana 98,55 [98,2-99,4], 4/4 blocos.

## Pares IFK: F06 menos F04 (pontos percentuais, mesma passada)

| rodada | malha (resultado.py) | gate (align) | relogio travado | duas varreduras |
|---|---|---|---|---|
| A | -1,25 | -1,2 | -0,3 | -1,0 |
| r1 | +0,91 | +1,0 | +2,6 | +2,1 |
| r2 | +1,99 | +2,0 | +2,2 | +2,6 |
| r3 | +3,66 | +3,7 | +2,8 | +4,1 |
| r4 | +3,00 | +3,0 | +1,9 | +2,1 |

O IFK ganhou nas 4 rodadas da posicao 2 em todas as reguas (malha 4/4, gate 4/4, travado 4/4, varreduras 4/4), de +0,9 a +4,1 pt; perdeu 1,2 pt na passada A (posicao 1, onde o F04 ja estava em 100%, sem margem para ganhar).

Ressalva: o F06 foi sempre gravado logo depois do F04 (cerca de 20 s), nunca em ordem alternada. Se o canal derivasse monotonicamente no minuto, o par favoreceria um dos dois. Quatro pares, o mesmo sinal em todos, mas sem sorteio de ordem. O tom de repeticao (3487,5 Hz) chega com +56,3 dB nesta bancada (`../G01-TONS`).

## Bancada e ressalvas

- Metodo: 16-FSK + IFK + FEC, com duas varreduras, 48 bytes aleatorios, `fecrep 1`, ganho digital 0,5, B -> A apenas.
- Transmite B (Windows, agente `console.py`), alto-falante Realtek no P2, aprimoramentos de audio desligados, a 10 cm do microfone de A e apontado para ele. Grava A (Linux), dispositivo padrao (Mic1), Dmic0 45 = -5 dB, Capture 39 = +12 dB. Controle por tunel SSH, sem cabo serial.
- Commit `213366c` na passada A e `c57fc74` nas rodadas (o campo `-dirty` dos HEADERs antigos era a arvore com os resultados nao versionados).
- `resultado.py` reescreve o HEADER a cada chamada e deixava so a ultima gravacao; este arquivo foi refeito com as cinco, e `resultado.csv` regenerado pelo mesmo `resultado.py` sobre as cinco gravacoes de `gravacao/` (mesmo formato).
- Para refazer: `./venv/bin/python resultado.py F06-16FSK-IFK-10CM gravacao/*.json --out <dir> --bancada "..."` (e `align.py` para as reguas de F04/F06).

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
