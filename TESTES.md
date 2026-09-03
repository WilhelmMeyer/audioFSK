# Plano de testes -- link acustico entre duas maquinas

Bancada desta campanha (nao misturar com corpora antigos em `old/`):

| ponta | saida | entrada |
|---|---|---|
| maquina A (console, teclado) | caixa Bluetooth | microfone interno do notebook |
| maquina B (agent, headless) | caixa em P2 (com fio) | microfone interno do notebook |

Cabo serial entre as duas so carrega **controle** -- nunca dado. O que e
pontuado viaja apenas pelo ar.

Regra da campanha: **um teste por vez, um eixo por vez.** Dois eixos
multiplicam os trials, e este link precisa de repeticoes mais do que de
amplitude. Repeticoes por ponto sao bem-vindas; escolher a melhor de tres e
reporta-la como resultado nao e -- reporte a mediana, ou todas.

O resultado -- bom ou ruim -- fica registrado em `resultados/<NOME-TESTE>/`
antes do proximo comecar.

## Tabela de recursos

Nome padrao = identificador do teste. Use ele no `--label` da gravacao e no
`--name` da campanha do `study.py`, para audio, ajuste e numero ficarem juntos.

| # | nome padrao | camada / recurso | como liga | os dois lados? | metrica principal |
|---|---|---|---|---|---|
| 01 | `LVL-BASE` | so escuta: ruido de fundo, sem nada tocando | `mic on`, `level` | nao | rms e pico do silencio |
| 02 | `LVL-TONE` | um tom puro chega? | `tonef <hz>` / `meas <hz>` | nao | dB do tom sobre a banda larga |
| 03 | `CH-CHIRP` | resposta de frequencia do canal | `capture.py --chirp` + `channel.py` | nao | mapa de bins, covas do pente |
| 04 | `FSK-BASE` | Bell 202, 1200 baud, 8N1 | `mode fsk` + `send` | sim (modo) | bytes recuperados (esperado: ~zero) |
| 05 | `MFSK-VOTE` | MFSK 10 tons, 5 pares, voto, 100 baud | `mode mfsk` + `fecsend` | sim (modo) | blocos inteiros, B/s |
| 06 | `MFSK-PAR` | MFSK paralelo, 5 bits por simbolo | `fecpar on` | sim | blocos inteiros, B/s |
| 07 | `MARY-BASE` | M-aria 16 tons, 4 bits por simbolo | `mode mary` + `fecsend` | sim (modo) | blocos inteiros, B/s |
| 08 | `MARY-GAIN` | calibracao do ponto de operacao | `gain <0..1>` no transmissor | nao | pico no receptor, alvo 0.4-0.6 |
| 09 | `MARY-GAP` | silencio entre simbolos | `marygap <fracao>` | sim | acerto de bits vs. tempo de ar |
| 10 | `MARY-BAND` | largura da faixa medida por tom | `maryband <Hz>` | sim | acerto de bits |
| 11 | `MARY-CHORD` | nibble como 3 tons em vez de 1 | `marychord on` | sim | acerto de bits |
| 12 | `SYNC-GATE` | sincronismo pelo early/late gate (padrao) | `syncsweep off` | sim | blocos inteiros |
| 13 | `SYNC-SWEEP` | duas varreduras cercando o frame -- **so M-ario** | `syncsweep on` | sim | blocos inteiros, periodo medido |
| 14 | `FEC-REP` | repeticoes de cada bit codificado | `fecrep <n>` | sim | blocos inteiros por n |
| 15 | `PKT-ARQ` | arquivo inteiro, stop-and-wait | `recvfile.py` | negociado no setup | pacotes de N entregues |

Recursos que **os dois lados** precisam ter iguais nao sao detectaveis no
decodificador: a divergencia vira lixo que falha no CRC e le exatamente como
canal ruim. Ligue com `b <comando>` (as duas maquinas de uma vez).

## Nem todo recurso existe em toda camada

Isto e o estado do codigo hoje, conferido nos arquivos, nao o que seria
desejavel. Sem esta tabela os testes 12 e 13 parecem valer para as tres
camadas, e nao valem.

| recurso | FSK | MFSK | M-ario |
|---|---|---|---|
| fluxo de bytes 8N1 (`send`) | sim | sim | **nao** |
| bloco codificado (`fecsend`) | **nao** | sim | sim |
| varreduras de sync (`syncsweep`) | nao | **nao** | sim |

Onde isso esta no codigo:

- 8N1 do MFSK: `modem.py` `MFSKModulator.modulate` poe start e stop, e
  `_feed_bit` desmonta o mesmo na volta -- de proposito, para que qualquer
  camada fisica apresente a mesma linha serial burra.
- M-ario sem 8N1: `MaryModulator.modulate` manda os 8 bits do byte e nada mais,
  e o receptor nao tem maquina de estados de UART.
- Varreduras: `console.py` `_fec_frame` so as monta dentro do ramo
  `if self.mode == 'mary'`, e `_sweep_llr` instancia `MaryDemodulator` com nome
  fixo.

**As lacunas sao historicas e podem ser fechadas -- menos uma.** Nada impede uma
camada de ter os dois caminhos; o MFSK ja tem. O custo de cada uma:

- **M-ario sem 8N1** e a que mais dói. Sem enquadramento, o `send` do M-ario e
  uma loteria de fase de nibble: comecar um simbolo cedo ou tarde entrega todo
  byte com os nibbles trocados, e num canal quase limpo isso recuperou o
  payload 4 vezes em 16. Trabalho pequeno.
- **MFSK sem varreduras** exige antes dar `steer=False`, `skip` e `period` ao
  `MFSKDemodulator`, que hoje so sabe se corrigir sozinho enquanto o audio
  passa. Uma correcao descoberta depois nao se aplica a decisoes ja tomadas.
  Trabalho medio, e nunca foi medido se ajuda nas camadas de acorde.
- **FSK sem bloco codificado** e a unica ausencia deliberada. Ele existe para
  ser linha serial burra, plugavel num `/dev/pts/N`; dar bloco a ele seria
  fazer dele um M-ario lento.

## O que cada teste faz e o que se espera

**01 `LVL-BASE`** -- abre so o microfone e mede. Nenhuma caixa tocando.
Da o piso: se o ruido de sala ja esta alto, todo numero depois desce junto.
Esperado: rms bem abaixo de 0.01, pico sem estouro.

**02 `LVL-TONE`** -- uma ponta toca um tom fixo, a outra mede aquela faixa e
a banda larga da mesma janela. Mede frequencia enviando aquela frequencia --
varredura responde outra pergunta e ja respondeu errado aqui. Tres repeticoes,
mediana. Esperado: margem folgada nos 16 tons M-arios, nas duas direcoes.

**03 `CH-CHIRP`** -- varredura gravada, virada em mapa por `channel.py`. Diz
onde estao as covas do pente. Esperado: banda util 550-3500 Hz, nada acima de
6 kHz. Serve para escolher tons, nao para julgar tom individual.

**04 `FSK-BASE`** -- a camada original. Decide bit pelo sinal do discriminador,
entao qualquer canal que enfraqueca um tom mais que o outro enviesa tudo.
Esperado: falha. Vale rodar uma vez para a nova bancada ter a linha de base.

**05 `MFSK-VOTE`** -- cinco pares soam juntos, cada par vota. Ganho sai da
conta, entao sobrevive a amplitude que nao da para confiar. Esperado: robusto
e lento, ~1.8 B/s.

**06 `MFSK-PAR`** -- mesmos tons, mas cada par carrega bit diferente. Nao cria
robustez, cria um dial: gasta menos redundancia num canal com margem.
Esperado: mais rapido que 05 e mais fragil.

**07 `MARY-BASE`** -- um tom por vez, amplitude inteira. E o maior ganho de
potencia medido aqui. Esperado: melhor taxa e melhor recuperacao das tres
camadas. Rodar em `fecrep 1` para o teste discriminar; em `fecrep 2` quase
tudo passa e a comparacao nao mede nada.

**08 `MARY-GAIN`** -- calibra a amplitude de saida. Calibrar num **burst**
(`fecsend`), nunca num tom: a troca abrupta de tom carrega ~2.5x o pico de um
tom continuo, e o limitador da outra ponta corta isso sem aviso. Esperado:
existe um ponto melhor; alto demais clipa, baixo demais some no ruido.

**09 `MARY-GAP`** -- insere silencio no fim de cada simbolo. Esperado: ajuda os
bits um pouco e nao se paga -- 30% do tempo de ar por ~2 pontos.

**10 `MARY-BAND`** -- largura da janela de medida ao redor de cada tom. Estreita
demais perde o tom que derivou; larga demais entra ruido do vizinho.

**11 `MARY-CHORD`** -- nibble virando tres tons. Divide a potencia por tres,
que e exatamente o que a camada M-aria existe para nao fazer. Esperado: pior;
rodar para ter o numero.

**12 `SYNC-GATE`** -- sincronismo padrao, early/late gate. Nao e ruim na media;
ele **colapsa** de vez em quando, e coisa que codigo nenhum conserta.

**13 `SYNC-SWEEP`** -- 80 ms de varredura em cada ponta do frame. A primeira da
o inicio absoluto, o intervalo entre as duas da o periodo medido de simbolo.
Comparar **pareado, sobre a mesma gravacao**, nunca por duas medias. Esperado:
ganho pequeno na media de bits e seguro contra o colapso do gate.

**14 `FEC-REP`** -- redundancia. Numa bancada nova isso e propriedade do link,
nao do codigo: precisa ser remedido aqui. `fecrep` tem que ser enviado ao outro
lado, nunca assumido.

**15 `PKT-ARQ`** -- arquivo inteiro. So depois que 07/13/14 estiverem fechados;
hoje o transfer de arquivo e a parte que nao funciona.

## O ganho nao e um ajuste do link, e um ajuste de uma cadeia

`gain 0.5` no lado A e `gain 0.5` no lado B **nao sao a mesma coisa**, e tratar
os dois como um so numero e o erro mais facil de cometer nesta bancada.

Cada sentido tem sua propria cadeia inteira: sistema de som, volume do sistema,
alto-falante, o ar, o microfone e o ganho de captura da placa. Aqui elas nao
compartilham um unico elemento -- Bluetooth com codec e volume proprio de um
lado, P2 direto no outro; dois microfones internos diferentes, dois ganhos de
captura diferentes, e ao que tudo indica controle automatico de ganho so em um
deles. O mesmo numero no transmissor produz niveis diferentes no receptor, e
quem decide se decodifica e o nivel **no receptor**.

Tres consequencias, e todas mudam como esta lista se roda:

1. **Cada sentido se calibra sozinho.** `MARY-GAIN` nao e um teste, sao dois.
   Um ganho medido em A->B nao diz nada sobre B->A.
2. **Calibrar vem antes de medir a camada.** Rodar `MARY-BASE` num ganho
   arbitrario mede o ganho, nao a camada -- e ja aconteceu neste projeto, onde
   0.8 recuperou 5 blocos de 15 e 0.5 recuperou 4 de 4 no mesmo link.
3. **Nenhum limiar absoluto serve para os dois lados.** Squelch, contraste e
   qualquer numero em dBFS sao propriedade de um receptor, nao do link.

E a calibracao em si tem que ser feita **no burst, nunca no tom**: a troca
abrupta de tom carrega cerca de 2,5x o pico de um tom continuo, e o limitador
da outra ponta corta isso sem aviso.

## Ordem

**Sequencial, na ordem da tabela.** Nao ha atalho aprovado.

Duas ordens mais curtas foram propostas e descartadas, e vale dizer por que,
porque as duas parecem mais espertas do que sao:

- **"07 primeiro, que e a melhor camada"** -- otimiza para chegar rapido ao
  melhor numero e deixa as outras camadas sem comparacao *nesta* bancada. As
  linhas de FSK e MFSK continuariam sendo de outro alto-falante e outro
  microfone, e a tabela do projeto existe justamente para compara-las entre si.
- **"08 antes de 07, calibrar antes de medir"** -- correto em principio, e caiu
  porque a calibracao por nivel nao e confiavel no sentido A->B: o receptor de
  la parece ter controle automatico de ganho, entao a regua se mexe junto com o
  que ela mede. Calibrar A->B, se for preciso, sera por taxa de erro, e so
  depois que houver um resultado ruim que justifique o custo.

O ganho continua sendo **dois ajustes, um por sentido** (ver a secao acima) --
isso nao mudou. O que mudou e que 08 nao vem antes.

## Teste 01, passo a passo

1. Maquina A: `mic on`, `spk off`. Deixa escutando.
2. Espera curta e aleatoria (segundos), com a sala como esta.
3. `level` -- le rms e pico do intervalo, nao da vida do processo.
4. Repete na maquina B.

So depois disso a caixa toca alguma coisa.

## Como fica um resultado no disco

Uma pasta por teste, nomeada com o nome padrao da tabela:

```
resultados/<NOME-TESTE>/
  HEADER.md          commit do codigo, data, bancada, ajustes fixos, trials, caveats
  gravacao/          o .wav float32 e o .json irmao, como saíram do disco
  llr/<stem>.csv     saida soft do demodulador, uma linha por simbolo
  bits/<stem>.txt    bits esperados, bits lidos, e a linha de diferencas
  figuras/<stem>.png espectro em cima, leitura em baixo
  resultado.csv      uma linha por gravacao com as metricas
```

O `HEADER.md` abre pelo commit, e isso nao e burocracia: uma acuracia de bits
fala do decodificador tanto quanto do canal, e este decodificador muda toda
semana.

**M-ario devolve quatro LLR por simbolo, nao um.** Quatro bits por simbolo,
quatro log-verossimilhancas. Tamanho do array nao e contagem de simbolos.

### A figura

Dois paineis, e o de cima nao leva marca nenhuma de proposito:

- **espectro** -- so o que o microfone gravou, energia absoluta em dB.
- **leitura** -- o mesmo espectro esmaecido ao fundo, com a grade de simbolo
  por cima, o **ideal em vermelho** (o que o transmissor mandou, reconstruido
  do payload guardado), o **lido em verde**, e **amarelo onde os dois batem**.

Manter os dois lado a lado e o que deixa uma marca sem energia embaixo dela
visivelmente ser uma afirmacao sobre nada. Uma figura anotada sozinha esconde
exatamente esse caso.

Tres defeitos corrigidos nessa figura, que davam leitura errada:

- **O fundo era o painel de contraste, e tinha que ser o absoluto.** Contraste
  divide cada linha de frequencia pela propria mediana, entao um tom que fica
  ligado muito tempo -- o preambulo M-ario sao 120 simbolos alternando dois
  tons -- levanta a propria mediana e some. O preambulo inteiro desenhava preto
  e lia como canal morto.
- **A grade desenhava todos os simbolos.** A 7,5 px por simbolo o tracejado
  vira parede e tapa o dado que ele existe para posicionar. Agora so desenha os
  simbolos que ficam a pelo menos 16 px um do outro.
- **45 dB de piso sob as marcas.** O painel de cima mostra o ruido; o de baixo
  serve para dizer se a marca cai sobre um tom. Sob as marcas o piso agora e 28 dB.

### Achado que a figura corrigida ja mostrou

No preambulo M-ario o receptor decide **o tom de cima em todos os simbolos**,
enquanto o espectro mostra os dois tons alternando como deviam. Nao e erro de
desenho -- conferido no demodulador direto, 119 simbolos seguidos no mesmo tom.
Nao investigado ainda.
