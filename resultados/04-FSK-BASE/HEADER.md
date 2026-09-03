# 04-FSK-BASE -- Bell 202, a camada original

- **Codigo:** commit `0718f2c` (mais as ferramentas novas desta campanha, que
  nao tocam no caminho de sinal)
- **Quando:** 2026-09-03 15:53
- **Camada:** FSK Bell 202. Marca 1200 Hz, espaco 2200 Hz, 1200 baud, UART 8N1.
- **Direcao:** B -> A. B transmite pela caixa em P2, ganho 0.8; A grava pelo
  microfone interno, indice 26.
- **Payload:** 48 bytes aleatorios, 3 trials
- **Sem correcao de erro** -- esta camada nao tem caminho codificado, e a
  ausencia e deliberada: ela existe para ser linha serial burra, plugavel num
  `/dev/pts/N`.

Pontuacao offline por `bench.py`, com alinhamento por `difflib`
(`autojunk=False`). Este link **apaga** bytes, nao so corrompe, e um byte
perdido desloca todos os seguintes -- uma comparacao indice a indice pontuaria
um link quase perfeito em ~50%.

## Resultado

| gravacao | rms | pico | fsk atual | squelch 0,0005 | bytes brutos | sync |
|---|---|---|---|---|---|---|
| 155313 | 0,0800 | 0,686 | 2,1% (1/48) | 4,2% (2/48) | 50 / 56 | SEM SYNC |
| 155318 | 0,0700 | 0,658 | 2,1% (1/48) | 4,2% (2/48) | 45 / 49 | SEM SYNC |
| 155321 | 0,0733 | 0,642 | 4,2% (2/48) | 6,2% (3/48) | 47 / 51 | SEM SYNC |

Media: **2,8%** no ajuste atual, **4,9%** com squelch dez vezes menor.
Blocos inteiros: **nenhum**, e a camada nem tem bloco.

## Leitura

**Nao e falta de sinal.** rms 0,07-0,08 e pico 0,64-0,69, contra um piso de
banda util de -62,6 dBFS (~0,0007) medido meia hora antes. O sinal chega cerca
de 40 dB acima do ruido. Baixar o squelch de 0,005 para 0,0005 levou 2,8% para
4,9% -- mexeu, e e a diferenca entre nada e nada.

**O receptor entrega 45 a 56 bytes de um payload de 48, e acerta 1 ou 2.** Esse
e o retrato do modo de falha do 8N1: o detector de start bit acha borda de
descida em toda parte e produz uma quantidade plausivel de bytes, todos
errados. Contagem certa, conteudo lixo. E a mesma razao pela qual medir vazao
com `0x55` mente tao bem -- conta bytes, e byte e o que esta camada produz
mesmo sem entender nada.

**`SEM SYNC` nas seis leituras.** Nem o preambulo foi localizado.

## Uma hipotese minha foi medida e caiu

Ao apresentar o teste eu afirmei que o FSK falha aqui porque a resposta em
pente da sala entrega um tom bem mais forte que o outro, e a decisao por
**sinal** do discriminador `x[n]*x[n-D]` enviesa entao todas as decisoes para o
mesmo lado. Medindo a energia que de fato chegou em cada tom:

| gravacao | 1200 Hz | 2200 Hz | diferenca |
|---|---|---|---|
| 155313 | -43,5 dBFS | -45,1 | **+1,6 dB** |
| 155318 | -41,0 dBFS | -44,0 | **+3,0 dB** |
| 155321 | -44,7 dBFS | -44,9 | **+0,2 dB** |

**0,2 a 3,0 dB de assimetria e pouco demais para explicar 2,8% de acerto.** A
explicacao era plausivel e esta errada. Fica registrada como caida, e nao
apagada, porque ela e a primeira coisa que ocorre a quem olha este resultado --
inclusive a mim, de novo, daqui a um mes.

## Aberto

A causa real nao foi identificada. Duas suspeitas, nenhuma testada:

- **Enquadramento 8N1.** O receptor esta achando bordas de start onde nao ha --
  45 a 56 bytes de 48 e a evidencia. Um start falso desloca tudo o que vem
  depois, e nao ha nada em que ressincronizar.
- **Recuperacao de tempo a 1200 baud.** E doze vezes mais rapido que as outras
  camadas desta bancada, com um simbolo de 0,83 ms.

Separar as duas custa uma gravacao ja existente e nenhuma sala: as tres estao
em `gravacao/`, e um desmodulador com relogio congelado (como o `steer=False`
do M-ario) diria se e tempo ou enquadramento.

## Para que serve este numero

Linha de base historica **desta bancada**: Bell 202 entrega 2,8% dos bytes com
sinal 40 dB acima do ruido. Sem ele, a tabela do projeto compararia o M-ario de
hoje com um FSK medido noutro alto-falante e noutro microfone.

## Arquivos

- `gravacao/` -- as tres gravacoes, WAV float32 mais JSON
- `figuras/` -- espectro cru e contraste, 600-3600 Hz
