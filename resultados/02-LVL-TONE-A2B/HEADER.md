# 02-LVL-TONE-A2B -- um tom puro, sentido A->B, agora gravado

- **Codigo:** commit `68412e1`, mesmo commit nas duas maquinas.
- **Quando:** 2026-09-03, entre 17:42 e 17:54.
- **Frequencia:** 1700 Hz, 5 s por tom, 5 trials.
- **Bancada:** A (Linux, console, transmite) caixa Bluetooth
  `41:42:2B:14:D4:2A`, indice PortAudio 20, `gain 1.0`. B (Windows, agent,
  grava) microfone interno do notebook, caixa desligada durante a medida.
- **Ferramenta:** `capture_a2b.py --tone`, que toca o tom em A e manda
  `grave` para B; o par WAV+JSON volta pelo cabo `/dev/ttyUSB0` a 115200 baud.
- **Banda estreita:** +-25 Hz em torno de 1700 Hz, por FFT com janela de
  Hanning sobre a gravacao inteira (mesma funcao `band_rms` de `ruido.py`).
  O numero depende dessa largura -- o mesmo +-25 Hz usado no piso de
  `01-LVL-BASE-A2B` e no `resultados/01-LVL-BASE/HEADER.md`.

## Por que esta pasta substitui a linha A2B do `resultado.csv` antigo

O `resultado.csv` de `resultados/02-LVL-TONE/` ja tinha tres linhas A2B,
medidas pelo comando remoto `meas` do agent (razao +24,2 dB, com a nota "FFT
sem normalizacao"). Essa e uma regua diferente: a escala em dB daquele `meas`
vem de uma FFT sem normalizacao, entao so a razao banda/larga dele e
transportavel, nunca o dBFS. As linhas desta pasta sao gravacoes reais em
disco, pontuadas em dBFS local do jeito que `01-LVL-BASE-A2B` mede o piso da
mesma cadeia -- e por isso comparaveis ao sentido B->A pela primeira vez. Isto
e o item 8 do `HANDOFF.md`: "refazer com gravacao para ficar na mesma regua
do outro sentido". As linhas antigas por `meas` ficam onde estao, no
`resultado.csv` de `02-LVL-TONE`, mas nao valem mais como o numero de
margem desta cadeia -- **as linhas novas abaixo substituem aquelas**.

## Resultado

| trial | 1700 Hz (banda estreita) | banda larga | pico | margem sobre o piso |
|---|---|---|---|---|
| 1 | -18,9 dBFS | -20,2 | 0,389 | +54,4 dB |
| 2 | -19,7 dBFS | -21,6 | 0,301 | +53,5 dB |
| 3 | -21,7 dBFS | -23,3 | 0,316 | +51,6 dB |
| 4 | -22,8 dBFS | -24,5 | 0,216 | +50,5 dB |
| 5 | -23,0 dBFS | -24,6 | 0,212 | +50,3 dB |

Piso em 1700 Hz +-25 Hz, de `01-LVL-BASE-A2B`: **-73,3 dBFS** (mediana de
quatro gravacoes).

Mediana das cinco: banda estreita **-21,7 dBFS**, banda larga **-23,3 dBFS**,
pico **0,301**, **margem +51,6 dB**. Considerando so as tres gravacoes feitas
depois do conserto do `capture_a2b.py` (trials 3-5): mediana da margem
**+50,5 dB** -- 1,1 dB abaixo, dentro do espalhamento entre trials, sem
mudar a leitura.

## Verificacao de saturacao

**Nenhum pico se aproxima de 1,0.** O maior e 0,389 (trial 1), o menor 0,212
(trial 5) -- todos abaixo de 0,4, longe do teto do conversor. Ao contrario do
sentido B->A, onde o volume da caixa de B e fixo e o pico variou 0,117-0,219,
aqui quem regula a saida e o `gain` de A (1.0 nesta medida) e a leitura de B
nao satura. **Este numero nao calibra ganho de transmissao** -- ver ressalva
abaixo.

## Leitura

**O sentido A->B tem margem folgada, como o B->A, so que menor.** +51,6 dB
aqui contra +57,3 dB no sentido B->A (`resultados/02-LVL-TONE/HEADER.md`).
As duas cadeias funcionam nivel; a diferenca de ~6 dB e dentro do que se
espera de duas caixas e dois microfones diferentes, e nao muda a leitura de
que o link nao esta limitado por nivel em nenhum sentido.

**A margem cai ao longo dos cinco trials, quase monotonicamente:** 54,4 ->
53,5 -> 51,6 -> 50,5 -> 50,3 dB, acompanhando o pico, que tambem cai: 0,389 ->
0,301 -> 0,316 -> 0,216 -> 0,212. Isso bate com a leitura ja registrada em
`resultados/01-LVL-BASE/HEADER.md` e em `02-LVL-TONE/HEADER.md`: o microfone
de B tem controle automatico de ganho, e ele reage ao longo da sessao. A
tendencia aqui vai no mesmo sentido -- nivel oscila em bloco (banda estreita
e banda larga se movem juntas, 1,3 dB de diferenca entre elas em todos os
trials) -- reforcando que **calibrar ganho de transmissao lendo nivel em B
nao funciona**, como o teste 08 ja precisava saber.

## Ressalvas

- **Um tom continuo nao calibra o ganho de transmissao.** Um burst M-ario
  troca de tom a cada simbolo, e essas transientes carregam cerca de 2,5x o
  pico de um tom continuo estavel -- o limitador da caixa de A pode cortar um
  burst mesmo quando o tom puro no mesmo `gain` chega limpo aqui, sem indicio
  nenhum nesta medida. A calibracao desta cadeia (A->B) e feita por taxa de
  erro no teste 08 `MARY-GAIN`, nao por nivel.
- **As duas primeiras gravacoes (174247, 174352) foram feitas antes do
  conserto do `capture_a2b.py`** (commit `d7e170e`, o mesmo mencionado em
  `01-LVL-BASE-A2B/HEADER.md`). O conserto nao mexeu em nada que altere o
  audio de um tom continuo; as tres gravacoes de depois nao se destacam das
  duas de antes em nenhuma medida (ver tabela), o que e consistente com essa
  leitura.
- Piso de B oscila e o AGC dele nao foi desligado nesta bancada -- ver
  `01-LVL-BASE-A2B/HEADER.md` e a leitura de `01-LVL-BASE/HEADER.md`.

## Arquivos

- `gravacao/` -- os cinco pares WAV float32 + JSON
- `figuras/` -- espectro cru em cima, contraste embaixo, por gravacao
- `resultado.csv` -- linhas A2B novas (regua "dBFS local, gravado"); as
  linhas A2B por `meas` continuam so em `resultados/02-LVL-TONE/resultado.csv`
