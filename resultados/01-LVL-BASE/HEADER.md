# 01-LVL-BASE -- piso de ruido, nada transmitindo

- **Codigo:** commit `0718f2c` mais `ruido.py`, `rcmd.py`, `tom.py`, `resultado.py`
  e `spectro.py` corrigido, nenhum commitado ainda
- **Quando:** 2026-09-03 15:49 (lado A) e 15:52 (lado B). **Segunda tentativa.**
- **A:** Linux, microfone interno Mic1 / Dmic0, indice PortAudio 26.
  Dmic0 +5 dB (55/70), Capture +12 dB (39/63). Saida em silencio.
- **B:** Windows, microfone interno, medido pelo comando `level` do agent.
- **Duracao:** A 10 s de gravacao (mais 1,5 s de assentamento descartados);
  B cinco leituras de `level` espacadas 6 s.

Mede o que cada microfone entrega com o link parado. Todo numero das outras
medidas e uma razao contra este.

**Os dois lados usam instrumentos diferentes e isso limita a comparacao.** A e
uma gravacao guardada em disco, com tabela por faixa e espectro. B e o `level`
do agent pelo cabo serial -- rms, pico e razao em banda por janela, sem
gravacao e sem tabela por faixa (`ruido.py` nao roda la). Os dois numeros sao
do mesmo tipo, rms em dBFS com nada transmitindo, e nao se pode exigir mais
que isso deles. O dBFS do `level` e rms da entrada, calculado antes de
qualquer filtro (`console.py:738`), entao ele nao muda com a camada ativa --
o que torna as duas rodadas de B comparaveis entre si.

## Resultado

### Lado A, 10 s

| medida | rms | dBFS |
|---|---|---|
| banda inteira | 0,002363 | **-52,5** |
| pico | 0,020057 | -34,0 |
| banda util 550-3600 Hz | 0,000743 | **-62,6** |

| faixa | rms | dBFS |
|---|---|---|
| 50-300 Hz | 0,002192 | -53,2 |
| 300-550 Hz | 0,000359 | -68,9 |
| 550-1200 Hz | 0,000462 | -66,7 |
| 1200-2000 Hz | 0,000432 | -67,3 |
| 2000-3000 Hz | 0,000343 | -69,3 |
| 3000-3600 Hz | 0,000185 | -74,6 |
| 3600-6000 Hz | 0,000230 | -72,8 |
| 6000-12000 Hz | 0,000282 | -71,0 |

Piso em cada tom M-ario (+-25 Hz): entre **-87,3 e -78,6 dBFS**. Pior em
1375 Hz, melhor em 3162 Hz, espalhamento de 8,7 dB.

Estacionaridade: em blocos de 0,5 s a leitura fica entre -55 e -51 dBFS ao
longo dos 19 blocos. **4 dB de variacao total, sem evento nenhum.**

### Lado B, cinco leituras de `level`

| leitura | dBFS | pico |
|---|---|---|
| 1 (logo apos `mic on`) | -49,7 | 0,01 |
| 2 | -53,4 | 0,01 |
| 3 | -54,0 | 0,01 |
| 4 | -53,9 | 0,01 |
| 5 | -54,0 | 0,01 |

Mediana **-53,9 dBFS**. Espalhamento **4,3 dB**, e **0,6 dB** descartando a
primeira leitura, que e a unica com aquecimento do stream dentro.

## Leitura

**O ruido esta quase todo abaixo de 300 Hz.** -53,2 dBFS no grave contra -66,7
na primeira faixa que o modem usa. A banda util senta 10 dB abaixo do total, e
cada tom M-ario individualmente senta cerca de 27 dB abaixo dele. Nao e sorte:
rede, ventoinha e transito moram no grave.

**O ruido tem espectro, nao e branco.** A faixa de controle acima de 3600 Hz
nao acompanha o grave -- -72,8 contra -53,2. Isso diz que o grave e fonte, nao
piso do conversor.

**A e B estao a 1,4 dB um do outro** (-52,5 contra -53,9 de mediana). Sao dois
microfones e dois ganhos de captura diferentes, entao a proximidade e
coincidencia e nao autoriza um limiar comum: cada direcao do link continua
tendo que ser calibrada sozinha.

**O piso de B sobe quando a sala silencia, e isso e a segunda evidencia de
controle automatico de ganho la.** Na primeira tentativa, com conversa na sala,
B leu mediana -65,0 dBFS com 18 dB de espalhamento; agora, com a sala quieta,
le -53,9 com 4,3 dB. **Mais quieto na sala, mais alto no medidor** -- o
contrario do que contaminacao faria, e exatamente o que um AGC faz ao subir o
ganho quando nao ha nada para comprimir. A outra evidencia esta no teste 02: no
sentido A->B a banda estreita e a banda larga oscilaram 8 dB **em bloco**, com
a razao entre elas travada em 0,1 dB. Consequencia pratica registrada la:
calibrar ganho de transmissao lendo nivel em B nao vai funcionar.

## A primeira tentativa foi descartada, e o motivo importa

**Havia conversa na sala durante os 10 s.** Voz ocupa 100-3000 Hz, em cima da
banda que o modem usa. Os numeros descartados e os validos, lado a lado:

| | descartado (com fala) | valido | erro |
|---|---|---|---|
| banda larga | -40,4 | -52,5 | 12,1 dB |
| 550-3600 Hz | -55,2 | -62,6 | 7,4 dB |
| pico | -18,3 | -34,0 | 15,7 dB |
| variacao em blocos de 0,5 s | 17 dB | 4 dB | -- |

**O pico e o numero que denuncia.** Eu tinha lido os 22 dB de crista como
"cliques, teclado, movimento" e escrito que era argumento a favor de
redundancia. Era voz humana. A figura mostrava as listras verticais de banda
larga e eu atribui a causa errada -- a figura estava certa, a leitura nao.

O audio descartado ficou em `descartado/`, com a figura dele. Nao foi apagado:
um piso medido com voz dentro e um erro que se repete, e o par de gravacoes
lado a lado e a unica forma de reconhece-lo rapido da proxima vez.

**Verificacao de contaminacao por outro processo.** Havia uma segunda sessao de
Claude trabalhando neste repositorio. Foi checado por dois caminhos
independentes: o worktree dela foi criado as 15:46:02, depois de todas as
medidas anteriores, e a cauda de silencio da gravacao da varredura das 15:46
esta a -47,7 dBFS contra -47,8 do silencio de meia hora antes. Sala igualmente
quieta. Nada do que ela fez entrou em medida nenhuma. Fica registrado porque a
pergunta so pode ser respondida por existir o audio guardado com hora -- de uma
tabela de percentuais ela seria irrespondivel.

## Duas falhas de instrumento encontradas antes do numero valer

**A fonte estava MUTED no PipeWire enquanto o `amixer` mostrava ela aberta.**
Sao duas camadas: o mixer ALSA (`amixer -c1 sget Dmic0`, +5 dB, `[on]`) e o no
do PipeWire acima dele (`wpctl status`, `[vol: 0.56 MUTED]`). Aberto embaixo e
mudo em cima entrega **bloco de zero exato**. Foi clique acidental no mute.

**A primeira gravacao tinha 5,5 s de sala e 4,5 s de zeros, e a media passou.**
O laco contava amostras, e zero e uma amostra. Deu -50,0 dBFS. O unico indicio
foi a figura ficar branca na metade direita -- o numero sozinho nao denunciava
nada. `ruido.py` agora aborta ao ver 0,2 s de zeros exatos, porque zero exato
nao e microfone silencioso, e microfone ausente.

## Arquivos

- `gravacao/` -- o WAV float32 e o JSON irmao da medida valida
- `figuras/` -- espectro cru em cima, contraste embaixo (50-6000 Hz, 10 s)
- `descartado/` -- a primeira tentativa, com fala na sala
