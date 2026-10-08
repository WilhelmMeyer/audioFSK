# F02-5X2-VOTADA-10CM

- **Codigo:** commit `213366c` (passada A), `c57fc74` (rodadas r1 a r4)
- **Quando:** 2026-10-08, passada A 16:47, rodadas r1 a r4 17:25 a 17:37
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 10 cm do mic e apontado -> A mic interno Linux (dispositivo padrao, Mic1), Dmic0 45 (-5 dB), Capture 39 (+12 dB), controle por tunel SSH
- **Camada:** mfsk, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Trials:** 5 gravacoes (1 passada A + 4 rodadas)

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20261008-164756-f02-votada-10cm` | 0.5 | 1 | 48 | 100.00% | OK | 0.14 | 0.029 |
| `20261008-172643-f02-votada-10cm-r1` | 0.5 | 1 | 48 | 98.83% | OK | 0.10 | 0.021 |
| `20261008-173015-f02-votada-10cm-r2` | 0.5 | 1 | 48 | 79.10% | nao | 0.10 | 0.021 |
| `20261008-173348-f02-votada-10cm-r3` | 0.5 | 1 | 48 | 99.25% | OK | 0.09 | 0.021 |
| `20261008-173537-f02-votada-10cm-r4` | 0.5 | 1 | 48 | 99.33% | OK | 0.09 | 0.021 |

Media de bits certos: 95.30%. Blocos inteiros: 4 de 5.

## Por posicao

Posicao 1 = passada A (caixa a 10 cm, 16:47). Posicao 2 = rodadas r1 a r4: o usuario moveu levemente o PC entre uma e outra e a cauda do tom passou de -14,6 dB para cerca de -11 dB. A mudanca de posicao e uma variavel, nao so repeticao: as duas posicoes nao devem ser misturadas numa media unica.

| posicao | n | bits mediana | faixa | blocos | pico rx |
|---|---|---|---|---|---|
| 1 (passada A) | 1 | 100,00% | 100,00-100,00% | 1/1 | 0.14-0.14 |
| 2 (r1-r4) | 4 | 99,04% | 79,10-99,33% | 3/4 | 0.09-0.10 |

Bits = acerto antes do FEC no melhor deslizamento (`resultado.py`). Bloco = caminho FEC real (malha do gate, `find_sync` + Viterbi soft). Uma gravacao por condicao: n pequeno, a mediana da posicao 2 sobre 4 pontos e indicativa, nao estatistica.

## Bancada e ressalvas

- Metodo: 5x2-FSK votada + FEC, 48 bytes aleatorios, `fecrep 1`, ganho digital 0,5, B -> A apenas.
- Transmite B (Windows, agente `console.py`), alto-falante Realtek no P2, aprimoramentos de audio desligados, a 10 cm do microfone de A e apontado para ele. Grava A (Linux), dispositivo padrao (Mic1), Dmic0 45 = -5 dB, Capture 39 = +12 dB. Controle por tunel SSH, sem cabo serial.
- Commit `213366c` na passada A e `c57fc74` nas rodadas (o campo `-dirty` dos HEADERs antigos era a arvore com os resultados nao versionados).
- `resultado.py` reescreve o HEADER a cada chamada e deixava so a ultima gravacao; este arquivo foi refeito com as cinco, e `resultado.csv` regenerado pelo mesmo `resultado.py` sobre as cinco gravacoes de `gravacao/` (mesmo formato).
- Para refazer: `./venv/bin/python resultado.py F02-5X2-VOTADA-10CM gravacao/*.json --out <dir> --bancada "..."` (e `align.py` para as reguas de F04/F06).

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
