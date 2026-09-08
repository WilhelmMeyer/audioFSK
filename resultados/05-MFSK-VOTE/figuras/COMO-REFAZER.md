# As tres figuras da 5x2-FSK votada -- como refazer

Três figuras da modulação de cinco pares votados, todas tiradas da gravação
`gravacao/20260903-155727-mfsk-vote-B2A.wav` desta pasta, a que entregou o
bloco inteiro:

- `5x2fsk-alternancia.png` -- os dois acordes se revezando símbolo a
  símbolo, no trecho alternado que abre a transmissão.
- `5x2fsk-espectro-dos-acordes.png` -- dois painéis: o espectro de um símbolo que
  levava bit 0 e o de um que levava bit 1, na janela exata em que o detector
  decide.
- `5x2fsk-votacao-nos-dados.png` -- o mesmo mecanismo sobre a carga codificada, onde
  os bits não se alternam mais.

- **Codigo:** commit `d56c8d2`, geradas em 2026-09-07.
- **Programa:** `figura_voto.py`, nesta pasta.

Um programa só para as três, ao contrário das outras campanhas, e por um
motivo: as três dependem do mesmo alinhamento de símbolo. Se cada uma
encontrasse as fronteiras por conta própria, duas figuras do mesmo áudio
poderiam mostrar réguas diferentes. Uma execução gera as três e grava nos
dois lugares, esta pasta e `artigo/figuras/`. `--figura a|b|c` gera uma só.
Ele acha a raiz do repositorio subindo ate encontrar `modem.py`, logo roda de
qualquer pasta.

```bash
./venv/bin/python resultados/05-MFSK-VOTE/figuras/figura_voto.py
```

## De onde vem o alinhamento

Nada é estimado a olho e nada é contado em múltiplos de 480 amostras. Os
símbolos saem do próprio `MFSKDemodulator`: cada iteração de `_symbols` deixa
em `last_window` o índice absoluto da janela que produziu aquela decisão, que
é onde o receptor de fato mediu, com a porta early/late já tendo corrigido o
passo. O início do bloco sai de `fec.find_sync` sobre os mesmos valores
suaves, do jeito que `bench.py` faz.

A conferência é o decodificador: esta gravação devolve os 48 bytes sem erro
nenhum, então as fronteiras desenhadas são as que decodificaram. E os bits
anotados na figura (c) são os *transmitidos* -- a carga do sidecar passada
por `fec.frame(payload, repeat=2)`, o mesmo caminho do transmissor -- não os
decodificados do áudio. O recebido coincidir é o resultado, não o rótulo.

No trecho da figura (c) a distância entre janelas vizinhas vai de 375 a 585
amostras contra as 480 de largura de cada uma, e é daí que vêm a folga e a
sobreposição entre elas na figura. Quase tudo isso é escolha de sonda e não
relógio: a porta corrige o passo em 15 amostras por símbolo, 3,1%, enquanto
as três sondas ficam a 60 amostras uma da outra e a escolhida desloca a
janela em até 120.

**A guarda é de 15%, não de 35%.** `MFSKDemodulator` tem `guard=0.15`: 72
amostras descartadas de 480, decisão sobre as 408 restantes, 8,5 ms. O
`CLAUDE.md` da raiz diz 35% para esta camada e está enganado; o que vale é o
código que recebeu este som, e é dele que a figura tira o número.

## Espectro e dado na mesma figura

Em (a) e (c) o fundo é o espectrograma, em escala de cinza -- STFT com janela
de Hann de 480 amostras, um símbolo, 100 Hz por bin, salto de 48 -- e por
cima vai a leitura do receptor:

- um marcador em cada um dos cinco tons que o detector leu naquele símbolo,
  um por par. A forma diz o que o tom significa, círculo para 0 e losango
  para 1; a cor diz se aquele par votou o bit que foi transmitido, verde-azul
  quando sim e vermelho quando votou contra.
- a grade, de passo constante: as verticais no período nominal do símbolo,
  10 ms, e as horizontais no meio do caminho entre um tom e o seguinte,
  delimitando a faixa de cada um. Sobre o valor do tom elas cortariam
  justamente o que se quer ler.
- o bit do símbolo, numa caixa acima do quadro, azul para 0 e verde para 1.

Nenhuma cor entra na área de dados a não ser nos marcadores. Faixas tingidas
sobre o espectrograma foram tentadas e saíram: qualquer cor sobre o cinza se
soma a ele e vira outra cor, e o que a figura mostra ali é nível.

**A grade tem passo constante, e a janela de decisão não.** O período do
símbolo varia 15 amostras, 3%, que é o passo com que a porta early/late
corrige. O que salta mais é qual das três sondas venceu -- cedo, em cima ou
tarde, a 60 amostras uma da outra -- e isso desloca a janela em até um quarto
de símbolo sem mudar a duração dela. Por isso a grade segue o período nominal
e os marcadores ficam onde o receptor mediu; eles não caem no centro exato da
célula, e é essa diferença que se está vendo.

A janela de um símbolo é a mais longa que se pode usar sem atravessar
fronteiras e misturar os dois acordes, e a 100 baud ela dá 100 Hz por bin
contra 200 Hz entre os tons de um par e 220 Hz entre pares vizinhos. Ou seja,
o espectrograma trabalha no limite da própria resolução, e é por isso que os
tons aparecem como manchas e não como dez raias finas. Os marcadores dizem,
sobre essa mancha, o que o detector leu -- que é uma medida na frequência
exata e no instante exato.

## A figura (b): a FFT, e as dez medidas atrás dela

Dois painéis, um por símbolo, porque são instantes diferentes e a comparação
que o receptor faz é dentro de um instante, entre os dois tons de um par.

A curva é a FFT da janela de decisão daquele símbolo, na mesma janela
retangular de 408 amostras que o detector usa. Atrás dela, uma barra fina em
cada um dos dez tons, na altura que o detector mediu -- `probe_0`/`probe_1`
sobre a mesma janela. A curva diz o que chegou em toda a banda; as barras são
os dez números que a decisão de fato usa, e só eles. Mesma cor dos
marcadores, mais o cinza claro para o tom mais fraco de cada par.

Vale ler as barras contra a curva em 1320 e 1540 Hz no painel de baixo: a
barra fica bem acima do vale vizinho, e isso é o espalhamento da janela
retangular, não tom transmitido.

## O trecho da figura (c), e por que ele não é "típico"

A distribuição de erros ao longo do bloco é bimodal: em janelas de 30
símbolos, 36 das 77 não erram nada e 19 erram um quarto ou mais. Não existe
trecho típico, então o programa escolhe um da moda, com exatamente um bit
errado e esse bit longe da borda, para que a figura mostre o mecanismo
funcionando e ao menos um símbolo que a correção teve de consertar. O número
de erros impresso vale para o trecho; o do bloco é o 88,1% abaixo.

## O que ele imprimiu nesta geracao

```
[voto] 20260903-155727-mfsk-vote-B2A.wav: 1333248 amostras a 48000 Hz, 2776 símbolos a 100 baud
    bloco: 48 bytes, repetição 2, 0 bytes falhos, bloco INTEIRO
    palavra de sincronismo no símbolo 138 (amostra 66555, 1,387 s da gravação); corpo codificado a partir do símbolo 169
    bits do corpo: 2340 comparados contra o transmitido, 88,1% certos antes da correção
    acerto de voto por par, no corpo:
      par 0    700 Hz (bit 0) /   900 Hz (bit 1): 75,8%
      par 1   1320 Hz (bit 0) /  1120 Hz (bit 1): 86,1%
      par 2   1540 Hz (bit 0) /  1740 Hz (bit 1): 82,0%
      par 3   2160 Hz (bit 0) /  1960 Hz (bit 1): 80,7%
      par 4   2380 Hz (bit 0) /  2580 Hz (bit 1): 74,0%
    erros em janelas de 30 símbolos: 36 janelas sem erro nenhum, 19 com um quarto ou mais, de 77 -- a distribuição é bimodal e não há trecho típico
        12 dos 12 símbolos lidos como transmitidos
[voto] /home/willj/audioFSK/resultados/05-MFSK-VOTE/figuras/5x2fsk-alternancia.png, /home/willj/audioFSK/artigo/figuras/5x2fsk-alternancia.png
    (a) 12 símbolos do preâmbulo, símbolos 126 a 137, terminando na palavra de sincronismo
        bits decididos: 010101010101
        espectrograma: Hann de 480 amostras (10,0 ms, 100 Hz por bin), salto 48; marcadores e fronteiras vêm do detector, cuja janela é de 408 amostras depois de 72 de guarda
        em 12 dos 12 símbolos a maioria dos cinco pares aponta o bit decidido
[voto] /home/willj/audioFSK/resultados/05-MFSK-VOTE/figuras/5x2fsk-espectro-dos-acordes.png, /home/willj/audioFSK/artigo/figuras/5x2fsk-espectro-dos-acordes.png
    (b) FFT da janela de decisão: símbolo 136 (bit 0) em cima, símbolo 135 (bit 1) embaixo; janela de 408 amostras (8,5 ms, 117,6 Hz por bin), retangular, guarda de 72 de 480 descartada
        símbolo 136, bit 0: votos [0, 0, 0, 0, 0] -> maioria 0
          par 0    700 Hz (0)   -28,7 dBFS     900 Hz (1)   -30,8 dBFS   diferença   2,1 dB
          par 1   1320 Hz (0)   -23,2 dBFS    1120 Hz (1)   -44,1 dBFS   diferença  21,0 dB
          par 2   1540 Hz (0)   -23,3 dBFS    1740 Hz (1)   -53,9 dBFS   diferença  30,5 dB
          par 3   2160 Hz (0)   -25,6 dBFS    1960 Hz (1)   -30,7 dBFS   diferença   5,1 dB
          par 4   2380 Hz (0)   -29,3 dBFS    2580 Hz (1)   -37,5 dBFS   diferença   8,2 dB
        símbolo 135, bit 1: votos [0, 1, 1, 1, 1] -> maioria 1
          par 0    700 Hz (0)   -30,0 dBFS     900 Hz (1)   -52,2 dBFS   diferença  22,1 dB
          par 1   1320 Hz (0)   -39,7 dBFS    1120 Hz (1)   -28,4 dBFS   diferença  11,3 dB
          par 2   1540 Hz (0)   -36,3 dBFS    1740 Hz (1)   -28,2 dBFS   diferença   8,1 dB
          par 3   2160 Hz (0)   -51,7 dBFS    1960 Hz (1)   -28,0 dBFS   diferença  23,7 dB
          par 4   2380 Hz (0)   -28,6 dBFS    2580 Hz (1)   -24,8 dBFS   diferença   3,8 dB
[voto] /home/willj/audioFSK/resultados/05-MFSK-VOTE/figuras/5x2fsk-votacao-nos-dados.png, /home/willj/audioFSK/artigo/figuras/5x2fsk-votacao-nos-dados.png
    (c) 30 símbolos da carga, símbolos 1781 a 1810, 0,30 s de ar
        começa 16,12 s depois do primeiro bit codificado do bloco (o bloco todo dura 23,40 s)
        bits transmitidos: 011010111101100101000101010000
        bits decididos:    011010111101100101000101010000
        todo bit do trecho saiu certo: 0 de 30 símbolos discordam
        e em 22 dos 30 símbolos ao menos um par votou contra os outros, com o bit final ainda saindo certo
        distância entre janelas vizinhas no trecho: 375 a 585 amostras, contra 480 de largura de janela -- daí a folga e a sobreposição entre elas na figura
        e isso é quase todo escolha de sonda, não relógio: a porta corrige o passo em 15 amostras por símbolo (3,1%), enquanto as três sondas ficam a 60 amostras uma da outra, o que desloca a janela em até 120
```

## Duas leituras que o `HEADER.md` desta campanha ainda não registra

1. **O par 0 discorda dos outros quatro, e é isso que a votação existe para
   absorver.** No painel de baixo da figura (b), o símbolo em que foi
   transmitido bit 1: o tom de 700 Hz (que significa 0) chega a -30,0 dBFS e
   o de 900 Hz (que significa 1) a -52,2, então o par 0 vota 0 num símbolo
   que era 1, e a maioria de 4 a 1 salva o bit. Ao longo do corpo codificado
   nenhum par sozinho é confiável -- o melhor acerta 86,1% dos símbolos e o
   pior 74,0% -- e a maioria dos cinco acerta 87,7%, com o valor suave somado
   chegando a 88,1%.

2. **88,1% dos bits certos antes da correção, e o bloco sai inteiro.** São
   2340 bits do corpo comparados contra o transmitido. Uma taxa dessas é
   irrecuperável sem código: o que entrega os 48 bytes é o convolucional com
   repetição 2 e a decisão suave por cima dela.
