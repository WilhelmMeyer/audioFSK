# 16fsk-tons.png, 16fsk-decisao.png, 16fsk-enquadramento.png -- como refazer

Tres figuras de artigo (300 dpi, largura de coluna, seguras em escala de
cinza), feitas das tres gravacoes da bateria valida desta campanha, sem
numero transcrito a mao. Nao confundir com as PNGs de diagnostico da pasta
`../gravacao/` nem com as `*-leitura.png` do `HEADER.md`, que sao saida do
`resultado.py` e do `spectro.py`.

- **Codigo:** commit `d56c8d2`, geradas em 2026-09-07. A arvore tinha
  modificacoes nao commitadas nos scripts de figura de outras campanhas, de
  outras sessoes; `modem.py` e `fec.py`, que sao o que alinha estas figuras,
  estavam como no commit.
- **Programas:** `figura_tons.py`, `figura_decisao.py`,
  `figura_enquadramento.py`, todos sobre `comum.py`, nesta pasta.

Os scripts moram aqui, junto da campanha que medem, e nao na pasta do artigo:
`artigo/figuras/` guarda apenas figuras. Uma execucao grava nos dois lugares,
esta pasta e `artigo/figuras/`, entao nao ha copia a sincronizar a mao. Eles
acham a raiz do repositorio subindo ate encontrar `modem.py`, logo rodam de
qualquer pasta.

```bash
./venv/bin/python resultados/07-MARY-BASE/figuras/figura_tons.py
./venv/bin/python resultados/07-MARY-BASE/figuras/figura_decisao.py
./venv/bin/python resultados/07-MARY-BASE/figuras/figura_enquadramento.py
```

Aceitam `--stem` (uma das tres gravacoes), `--simbolo` (onde comeca o trecho,
contado do inicio do quadro) e `--out` (repetivel).

## As gravacoes

So estas tres, que sao a bateria 3 do `HEADER.md`:

```
20260903-162209-mary-base-limpo-B2A
20260903-162220-mary-base-limpo-B2A
20260903-162230-mary-base-limpo-B2A
```

`comum.STEMS` e uma lista fechada e `comum.alinha` recusa qualquer outro nome.
As outras seis gravacoes da pasta sao de outra condicao; uma delas entrar aqui
por descuido daria uma figura correta em forma e falsa em conteudo, e a figura
nao teria como avisar. As figuras publicadas usam a segunda, `162220`, que e
tambem a que pontua melhor das tres; as outras duas rodam pelos mesmos scripts
e servem para conferir que o trecho escolhido nao e sorte de uma gravacao so.

## De onde vem cada coisa

Nada e estimado a olho e nada e digitado a mao.

- **As frequencias** vem de `modem.MARY_TONES`.
- **As fronteiras de simbolo** vem do proprio `MaryDemodulator`, que registra
  em `last_window` a amostra em que mediu cada decisao. `comum._Rastreada` so
  guarda o que ele ja calcula: a janela, as energias dos dezesseis tons e o
  piso corrente. O piso e capturado na entrada de `_update_floor`, e nao no
  `yield`, porque em `_symbols` a ordem e medir, decidir, atualizar o piso,
  entregar; ler depois daria o divisor da *proxima* decisao e a margem
  anotada discordaria em silencio da que o detector usou.
- **O inicio do quadro** vem de `fec.find_sync`, correlacao da palavra de
  referencia de 31 bits sobre o fluxo de valores suaves, nunca de contagem de
  simbolos.
- **Os bits anotados** sao os transmitidos, tirados do `payload_hex` da
  gravacao pelo mesmo caminho do transmissor, `fec.frame`: convolucional,
  repeticao 2, entrelacamento, palavra de referencia na frente. Nao sao os
  decodificados do audio.
- **O bloco e alimentado ao demodulador em pedacos de 2048 amostras**, o
  mesmo tamanho com que o `bench.py` pontuou esta campanha. O demodulador
  guarda estado e a porta early/late anda conforme o que ja consumiu, entao
  alimentar tudo de uma vez daria outro alinhamento que o que produziu os 3
  blocos de 3 do `HEADER.md`.

**O portao.** `comum.alinha` so devolve um alinhamento depois de o bloco
decodificar de volta, byte a byte, a carga gravada no JSON, depois de o bit de
sincronismo cair em fronteira de simbolo e depois de a janela do ultimo
simbolo caber inteira na gravacao. Se qualquer um dos tres falhar, o programa
para. Uma figura de fronteiras desenhada sobre um bloco que nao decodifica nao
mostra o enquadramento, mostra uma suposicao.

## Forma, decidida pelo usuario

Estas tres seguem o mesmo padrao das figuras da camada de cinco pares, em
`resultados/05-MFSK-VOTE/figuras/`.

**O nome comeca pela camada.** `16fsk-` mais o que a figura mostra.

**O sinal e sempre cinza, e o piso de ruido fica a vista.** Os espectrogramas
sao desenhados em nivel relativo ao maximo do trecho, sem dividir nada: o
ruido de fundo e o cinza da figura e o tom e o que escurece sobre ele. Uma
versao anterior dividia cada raia pelo piso dela e o fundo saia branco, o que
deixava de parecer um espectrograma; a escala de 28 dB abaixo do maximo e o
que poe o piso em cinza medio sem afogar o tom.

**A cor fica reservada ao que o receptor fez, nunca ao sinal.** O marcador
sobre cada simbolo diz o tom detectado, `#1B7F79` quando saiu o tom
transmitido e `#C43D2F` quando nao, com contorno claro para sobreviver a fundo
claro e escuro. O que rotula simbolo, que sao os bits, vai numa faixa propria
acima do quadro: tinta sobre o cinza se somaria a ele e viraria uma terceira
cor, que nao quer dizer nada.

**A grade e de passo constante**, no periodo nominal do simbolo, fina,
pontilhada e cinza 0,30. As horizontais vao no meio do caminho entre um tom e
o seguinte, delimitando a faixa de cada um, e nunca sobre o valor do tom. As
fronteiras que o receptor de fato usou nao sao a grade: elas sao as divisorias
da faixa de bits, e a comparacao entre as duas e o que a figura do
enquadramento tem a dizer.

**O eixo de frequencia e a lista dos dezesseis tons**, lida de
`modem.MARY_TONES`. Uma escala de 500 em 500 Hz obrigaria a medir com regua o
que a camada define. O eixo de tempo conta em milissegundos desde o inicio do
trecho, porque o instante absoluto dentro da gravacao nao diz nada a quem le e
a duracao do simbolo diz tudo.

**Rotulo nao diz "vencedor" nem "ganhou".** O marcador diz tom detectado.

**Legenda curta e sem moldura**, sem repetir o que o eixo ja diz.

**O trecho e um em que todo bit sai certo.** Simbolos 290 a 320, 30 de 30
decididos no tom transmitido e portanto os 120 bits. A dificuldade da camada
aparece dentro do simbolo, na margem entre o tom detectado e o segundo, e nao
no bit final.

## Escolhas de desenho, e por que

**As duas figuras de espectrograma sao deslizantes**, janela de um simbolo e
salto de um oitavo dele, com a FFT preenchida com zeros ate 2048 pontos. A
janela precisa ter o comprimento do simbolo, que e o minimo para separar tons
distantes 162 Hz; o preenchimento nao cria resolucao nenhuma, so evita que a
figura saia um tabuleiro de raias de 100 Hz. Uma versao anterior desenhava uma
coluna por simbolo, sincronizada com o detector, e ficava um mosaico de blocos
em vez de um espectrograma.

**As duas partilham `figura_tons.desenha` e `figura_tons.legenda`**, para que
nao possam divergir em nada que nao seja o que cada uma tem a dizer.

**A figura da decisao tem dois paineis alinhados na frequencia.** Em cima a
FFT da janela como curva, com uma barra em cada tom na altura que o detector
mediu, mais o piso corrente. Embaixo a mesma medida contada do proprio piso de cada tom, que
e a grandeza que decide.

**A curva e a FFT densa da janela, com preenchimento de zeros ate 8192
pontos, e nao os dezesseis pontos ligados por retas.** Duas alternativas foram
desenhadas e descartadas pelo usuario em 2026-09-07. Ligar so os dezesseis
pontos tira os lobulos largos que incomodam, e tira junto a informacao de que
uma janela de 408 amostras resolve 117,6 Hz enquanto os tons estao a 162 Hz,
que e o motivo de os lobulos se sobreporem. Janela de Hann so na curva alisa
os lobulos e e pior por outro motivo: tira a curva de cima dos pontos
medidos, entao ela deixa de passar pelo topo das barras e vira uma segunda
medida ao lado delas. O preenchimento com zeros nao inventa resolucao, so
avalia em mais frequencias a mesma transformada que as 408 amostras ja
definem.

**Os lobulos largos sao da janela de medida, nao do canal.** Um seno perfeito
de 2512 Hz, sintetizado e sem canal nenhum, medido nas mesmas 408 amostras,
da o mesmo lobulo, com as covas em f0 mais ou menos 116 e 119 Hz contra os
117,6 Hz previstos por fs/N. Sobreposto ao simbolo gravado, as duas curvas
diferem 2,7 dB em media dentro do lobulo principal e 16,2 dB longe dele, que
e onde esta o ruido da sala. Vale ler assim: perto do tom a curva fala da
janela, longe do tom fala do canal, e a decisao nao olha nem uma coisa nem
outra, so os dezesseis pontos.

**A marcacao da margem tem uma linha de chamada por barra**, e nao so pela
mais alta: a flecha mede a distancia entre duas alturas, entao as duas
precisam estar marcadas ou ela parece medir de um valor ate coisa nenhuma. A
flecha vai com `shrinkA` e `shrinkB` em zero, porque o padrao do matplotlib
recua alguns pontos em cada ponta e ela fica sem encostar nas duas linhas. As barras tem a mesma
espessura e as mesmas cores nos dois paineis, porque sao os mesmos dezesseis
tons na mesma janela e duas cores para o mesmo tom fariam a figura parecer
falar de duas coisas; o que muda de um painel para o outro e de onde a barra e
contada. Sao tres cores: o tom transmitido, os tons calados que ainda assim
chegaram acima do proprio piso, e os que ficaram abaixo dele. A margem e
marcada no painel de baixo e nao no de cima, porque e a diferenca entre duas
barras e so ali as duas alturas sao comparaveis a olho.

**O simbolo dessa figura nao e escolhido a mao.** `figura_decisao.tipico` pega
o simbolo do mesmo trecho cuja margem esta mais perto da mediana do bloco,
entre os que saem certos e em que a energia bruta e a normalizada concordam
sobre os dois primeiros colocados. Da o 305, com margem de 8,0 dB contra
mediana de 7,9 dB no bloco. E uma decisao comum, nao a mais folgada nem a mais
apertada. `--simbolo` desenha outro.

## O que os programas imprimiram nesta geracao

```
[tons] .../resultados/07-MARY-BASE/figuras/16fsk-tons.png, .../artigo/figuras/16fsk-tons.png
    20260903-162220-mary-base-limpo-B2A, 10,33 s gravados, 48 B de carga, repeticao 2
    quadro de 593 simbolos, 1,799 a 7,721 s; simbolo de 480 amostras, guarda 72 (15%), janela de decisao 408
    simbolos certos 89,5%, bits certos 94,5%
    trecho: símbolos 290 a 320 do quadro, 4,699 a 4,999 s da gravação, 2,90 s depois do início do quadro
    16 tons de 888 a 3325 Hz, separação 162–163 Hz; símbolo de 480 amostras, 10 ms
    janela 480 amostras, salto 60, FFT preenchida até 2048; escala de 28 dB abaixo do máximo do trecho
    pico menos mediana da coluna: mediana 15,6 dB, mínimo 4,8 dB
    no trecho, 30 dos 30 símbolos decididos no tom transmitido, e portanto todos os 120 bits

[decisão] .../resultados/07-MARY-BASE/figuras/16fsk-decisao.png, .../artigo/figuras/16fsk-decisao.png
    20260903-162220-mary-base-limpo-B2A, 10,33 s gravados, 48 B de carga, repeticao 2
    quadro de 593 simbolos, 1,799 a 7,721 s; simbolo de 480 amostras, guarda 72 (15%), janela de decisao 408
    simbolos certos 89,5%, bits certos 94,5%
    símbolo 305 do quadro, 4,850 s da gravação; janela 232887–233295, 408 amostras
    transmitido tom 10 (2512 Hz), bits 0011; detectado tom 10 (2512 Hz)
    margem sobre o segundo colocado 8,0 dB; mediana do bloco 7,9 dB (2,6 a 12,6 dB entre os decis)
    o tom detectado é também o mais forte em energia bruta neste símbolo (tom 10), como pede a escolha do símbolo comum
    piso deste símbolo: 7,1 dB entre o tom de piso mais alto e o mais baixo; mediana do bloco 6,9 dB

[enquadramento] .../resultados/07-MARY-BASE/figuras/16fsk-enquadramento.png, .../artigo/figuras/16fsk-enquadramento.png
    20260903-162220-mary-base-limpo-B2A, 10,33 s gravados, 48 B de carga, repeticao 2
    quadro de 593 simbolos, 1,799 a 7,721 s; simbolo de 480 amostras, guarda 72 (15%), janela de decisao 408
    simbolos certos 89,5%, bits certos 94,5%
    trecho: símbolos 290 a 320 do quadro, 4,699 a 4,999 s da gravação, 2,90 s depois do início do quadro, 0,300 s de duração
    símbolo nominal 480 amostras; no trecho o receptor consumiu de 420 a 585, mediana 480; guarda descartada 72 amostras (1,5 ms)
    fronteira medida contra grade nominal: afastamento máximo 1,88 ms, mediana 0,63 ms
    bits enviados no trecho, em ordem de fluxo: 001000100010001011011111110010000100100111110000010101001001001101100110100000111000011101001100101101000110110011111101
    30 dos 30 símbolos foram decididos no tom transmitido, e portanto todos os 120 bits do trecho; no quadro inteiro, 89,5% dos símbolos e 94,5% dos bits
```

Pelas tres gravacoes, com os mesmos programas:

| gravacao | simbolos certos | bits certos | margem mediana | piso, espalhamento mediano |
|---|---|---|---|---|
| 162209 | 72,5% | 85,2% | 6,0 dB | 7,7 dB |
| 162220 | 89,5% | 94,5% | 7,9 dB | 6,9 dB |
| 162230 | 87,4% | 93,7% | 7,3 dB | 5,5 dB |

Nas tres o quadro tem 593 simbolos, comeca entre 1,79 e 1,85 s da gravacao e o
receptor consome entre 375 e 585 amostras por simbolo, com mediana em 480. As
tres decodificam a carga inteira, que e o portao de `comum.alinha`, e sao os 3
blocos de 3 do `HEADER.md`.

## Uma discrepancia com a documentacao

O `CLAUDE.md` da raiz e o `artigo/CLAUDE.md` dizem que o intervalo de guarda e
de 35% do simbolo. Na 16-FSK nao e: `MaryDemodulator.__init__` tem
`guard=0.15`, que sobre as 480 amostras do simbolo descarta 72 e mede em 408.
Os 35% sao da camada de cinco pares e aparecem tambem como caso de teste no
`loopback_test.py`. As figuras seguem o codigo. O codigo nao foi mexido.
