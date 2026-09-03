# 14-FEC-REP

- **Codigo:** commit `02be235-dirty`
- **Quando:** 2026-09-03 17:28:52
- **Bancada:** B->A. B (Windows): caixa Bluetooth AL-667 ~60% volume. A (Linux): mic interno Mic1/Dmic0, dev PortAudio 26, Dmic0 45 (-5 dB), Capture 39 (+12 dB). Serial /dev/ttyUSB0 so controle.
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 1.0
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Direcao:** B -> A (B transmite, A grava)
- **Entrada / saida:** entrada `26` (Mic1 de A) / saida: caixa Bluetooth de B
- **Payload:** 48 bytes aleatorios, 4 trials por ponto, um eixo so (`fecrep`)
- **Trials:** 12 gravacoes

Teste 14: fecrep 1, 2 e 4, quatro trials cada, tudo o mais fixo (mary, ganho 1.0, 48 bytes, sem gap, sem banda, sem acorde, sem varredura).

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-172504-rep1-B2A` | 1.0 | 1 | 48 | 94.09% | OK | 0.19 | 0.031 |
| `20260903-172511-rep1-B2A` | 1.0 | 1 | 48 | 90.76% | OK | 0.20 | 0.034 |
| `20260903-172519-rep1-B2A` | 1.0 | 1 | 48 | 90.51% | OK | 0.19 | 0.031 |
| `20260903-172526-rep1-B2A` | 1.0 | 1 | 48 | 93.17% | OK | 0.18 | 0.031 |
| `20260903-172550-rep4-B2A` | 1.0 | 4 | 48 | 63.17% | OK | 0.20 | 0.044 |
| `20260903-172606-rep4-B2A` | 1.0 | 4 | 48 | 91.89% | OK | 0.19 | 0.041 |
| `20260903-172623-rep4-B2A` | 1.0 | 4 | 48 | 92.00% | OK | 0.19 | 0.037 |
| `20260903-172639-rep4-B2A` | 1.0 | 4 | 48 | 92.42% | OK | 0.19 | 0.038 |
| `20260903-172703-rep2-B2A` | 1.0 | 2 | 48 | 92.07% | OK | 0.21 | 0.035 |
| `20260903-172714-rep2-B2A` | 1.0 | 2 | 48 | 92.03% | OK | 0.20 | 0.037 |
| `20260903-172724-rep2-B2A` | 1.0 | 2 | 48 | 92.28% | OK | 0.19 | 0.035 |
| `20260903-172735-rep2-B2A` | 1.0 | 2 | 48 | 91.31% | OK | 0.18 | 0.032 |

Media de bits certos: 89.64%. Blocos inteiros: 12 de 12.

## Resultado por ponto

| `fecrep` | tempo de ar | taxa util | bits certos (gate) | bits certos (relogio travado) | blocos inteiros |
|---|---|---|---|---|---|
| 1 | 4,26 s | **11,3 B/s** | 92,2% | 93,3% | **4 de 4** |
| 2 | 7,19 s | 6,7 B/s | 91,9% | 93,2% | **4 de 4** |
| 4 | 13,04 s | 3,7 B/s | 84,9% | 85,6% | **4 de 4** |

## Leitura principal

**Nesta bancada a redundancia nao compra nada, e `fecrep 1` e 2,2x mais rapido.**
Doze gravacoes, tres pontos, e os doze blocos saem inteiros. A tabela do
`CLAUDE.md` que dizia que a taxa 1/3 sozinha "nao recupera praticamente nada"
foi medida em outra bancada e num ponto de operacao saturado; **nesta cadeia
corrigida ela recupera tudo.** Isso reposiciona a linha M-aria do projeto: 11,3
B/s com bloco inteiro em 4 de 4, contra os 9,4 B/s registrados hoje.

**O que a redundancia compra e a cauda, nao a media.** A gravacao `172550`
(rep 4) leu **63,2% dos bits pelo gate e 64,0% com o relogio travado** -- um
terço dos bits errados -- e **mesmo assim entregou o bloco inteiro.** Nenhum dos
pontos em rep 1 ou rep 2 chegou perto desse nivel de erro, entao a bancada nao
mostrou o caso simetrico; mas o mecanismo esta demonstrado: taxa 1/3 repetida
quatro vezes sobreviveu a um evento que teria destruido qualquer bloco em rep 1.
A media de bits de rep 4 (85,6%) so e mais baixa por causa dessa unica gravacao;
sem ela as tres condicoes ficam empatadas em 92-93%.

**Conclusao operacional:** rodar o link em `fecrep 1` e usar o tempo economizado
em mais blocos. `fecrep 4` e seguro de reserva para quando a sala estiver ruim,
nao um ajuste de rotina.

## Ressalvas

- **Este teste nao discrimina.** Com 12 de 12 blocos inteiros em todos os pontos,
  o eixo nao separou nada pela metrica principal da tabela (blocos inteiros). A
  leitura acima se apoia em bits e em tempo de ar, que e o que resta quando o
  canal esta acima do ponto de quebra. Para *discriminar* seria preciso degradar
  de proposito -- baixar o ganho, afastar as maquinas -- e isso e outro teste.
- **A gravacao `172550` nao foi explicada.** rms 0,0443 (o mais alto das doze) e
  pico 0,195, ou seja, nao foi sinal fraco nem saturacao; o relogio travado leu
  o mesmo que o gate (64,0% contra 63,2%), entao tambem nao foi colapso de
  sincronismo. Sobra evento acustico na sala durante aqueles 13 s. Fica
  registrada como esta, sem descarte: descartar a unica gravacao que demonstra
  o valor da redundancia seria descartar o resultado.
- **`acerto_bits` no `resultado.csv` e a regua do gate.** Os numeros de "relogio
  travado" vem do `align.py`, que re-demodula com `steer=False` a cada offset de
  amostra. As duas reguas nao sao intercambiaveis.
- **Uma bateria abortou e foi refeita.** A primeira tentativa de `rep 2` morreu
  em "a entrada nao entregou audio em 3s" -- o microfone de A que nao acorda logo
  depois de outro processo soltar o dispositivo. Repetida integralmente 25 s
  depois; nenhuma gravacao parcial entrou no corpus.
- Commit anotado `02be235-dirty`: pastas de resultado nao commitadas mais a
  correcao do `capture.py` descrita em `resultados/11-MARY-CHORD/HEADER.md`.
  DSP (`modem.py`, `fec.py`) intacto em `02be235`.
- Taxa util = payload / tempo de ar do quadro codificado. Nao inclui o tempo
  entre blocos nem o round trip da serial, que aqui e so controle.


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
