# Handoff -- campanha de medidas do link acustico

Estado em 2026-09-03 20:15. O plano dos testes esta em `TESTES.md`. Leia ele e
o `CLAUDE.md` antes de comecar. Este arquivo substitui a versao das 19:10.

## Por que esta sessao parou

**A maquina B esta offline.** Nao ha nada a medir ate ela voltar. Tudo que foi
gravado esta em disco e pontuado; o que falta e trabalho de sala, nao de
teclado.

Um aviso sobre esta sessao em particular: **duas sessoes do Claude Code
estiveram abertas sobre este repositorio ao mesmo tempo**, entre 19:24 e 19:31.
Uma media na bancada, a outra terminava a investigacao do piso e reescrevia
`CLAUDE.md`, `HANDOFF.md`, `modem.py` e `bench.py` debaixo dela. Nada se
perdeu, porque as duas mexeram em arquivos diferentes e a que media so leu, mas
foi sorte. **Uma sessao por vez neste repositorio** -- a bancada tem um cabo
serial e um par de arquivos de estado, e nenhum dos dois tem tranca.

**Primeiro comando da sessao nova:** commitar o que ficou solto --

```bash
./venv/bin/python loopback_test.py     # tem que imprimir SUCCESS!
git add -A && git commit
```

`modem.py` e `bench.py` estao modificados pela investigacao do piso, que
**terminou** e vale a pena (ver "A causa achada"). O padrao deles continua
sendo o comportamento de hoje, entao commitar nao muda numero nenhum ja
medido.

## A bancada

| ponta | saida | entrada |
|---|---|---|
| **A** (Linux, console, tem teclado) | caixa Bluetooth `41:42:2B:14:D4:2A`, indice 20 | microfone interno Mic1 / Dmic0, indice PortAudio 26 |
| **B** (Windows, agent, headless) | caixa Bluetooth `AL-667`, ~60% de volume | microfone interno |

- Cabo serial em `/dev/ttyUSB0`, 115200. So controle, nunca dado.
- Ganho de captura em A: `Dmic0 45` (-5 dB), `Capture 39` (+12 dB).
- **A caixa de A comprime, e o ponto de operacao dela e 0.20 no PipeWire.**
  Estava em 1.00; foi para 0.45 no teste 16 e para **0.20** no teste 17, que e
  onde ela para de comprimir sem ficar sem sinal (a curva esta abaixo).
  `wpctl set-volume <id> 0.20`. **O id muda quando a caixa reconecta** -- era
  92, agora e 104 -- entao leia `wpctl status` em vez de decorar o numero, e
  confira com `wpctl get-volume <id>` antes de medir, porque o volume volta ao
  maximo na reconexao.
- As duas maquinas rodam `9acc715` ou mais novo. B foi atualizada por `pull` e
  `restart` e responde.

## O que esta fechado

### Sentido B -> A: os quinze testes, todos com pasta em `resultados/`

| teste | resultado |
|---|---|
| 01 `LVL-BASE` | A: -52,5 dBFS (banda util -62,6) |
| 02 `LVL-TONE` | +57,3 dB de margem |
| 03 `CH-CHIRP` | 74 de 76 bins com SNR negativa; contradiz o tom pisado em 76 dB |
| 04 `FSK-BASE` | 2,8% dos bytes, nenhum bloco |
| 05 `MFSK-VOTE` | 1 bloco de 3 (corpus anterior a correcao da cadeia) |
| 06 `MFSK-PAR` | nenhum bloco em 6 (idem) |
| 07 `MARY-BASE` | 3 blocos de 3 |
| 08 `MARY-GAIN` | 11 blocos de 12 |
| 09 `MARY-GAP` | 99,6 / 98,0 / 88,1% de bits, 9/9 -- o gap piora |
| 10 `MARY-BAND` | 99,8 / 99,9 / 99,9%, 9/9 -- nao move nada |
| 11 `MARY-CHORD` | acorde e pior: -4,3 dB de nivel, -1,2 ponto de bits |
| 12-13 `SYNC` | gate 95,31% 4/4; duas varreduras 95,68% 4/4 (repontuado) |
| 14 `FEC-REP` | 12 blocos de 12 em `fecrep` 1, 2 e 4. **`fecrep 1` = 11,3 B/s** |
| 15 `PKT-ARQ` | **21/21 pacotes, 0 retransmissoes, arquivo identico** |

Dois desses derrubaram linhas do `CLAUDE.md`, ja reescritas la: a taxa 1/3
sozinha recupera tudo nesta cadeia (a tabela antiga descrevia uma cadeia
saturada), e a transferencia de arquivo funciona -- sem mudar protocolo, so o
nivel analogico. **Linearidade valeu mais que qualquer mudanca de codigo.**

### Sentido A -> B: 01, 02, 03 e 08 fechados

| teste | resultado |
|---|---|
| 01 `LVL-BASE-A2B` | piso de B: -52,3 dBFS (banda util -55,0) |
| 02 `LVL-TONE-A2B` | +51,6 dB de margem |
| 03 `CH-CHIRP-A2B` | 76 de 76 bins positivos -- o oposto do outro sentido |
| 08 `MARY-GAIN-A2B` | caixa em 1.00: 80-84% dos bits nos quatro ganhos, **0 de 12 blocos** |
| 16 `SPK-A2B` | caixa em 0.45: 82,6%, **2 de 6** -- os primeiros blocos deste sentido |
| 08B `MARY-GAIN-A2B` | caixa em 0.45, seis ganhos: 84,7% no gate, 87,0% travado, 4 de 12 |
| 17 `SPK-LEVEL-A2B` | caixa como eixo: **0.20 e o joelho**, 88,2% travado, 8 de 9 |

## Os problemas encontrados e o que foi feito

1. **`capture.py` so ligava ajustes, nunca desligava.** `marychord` e
   `mfskgroup` ficavam grudados no agent e envenenavam o teste seguinte, com o
   JSON dizendo o contrario. Corrigido: manda os quatro explicitos sempre.
2. **O span das varreduras era contado duas vezes com arredondamentos
   diferentes.** Sobre o mesmo audio, span errado deu 78,1% dos bits e 0 de 4
   blocos; o certo, 95,7% e 4 de 4. Era isso, e nao o canal, que fazia as
   varreduras parecerem piores que o gate. Uma funcao so agora,
   `fec.frame_symbols`. Corpus recarimbado e repontuado; tres conclusoes da
   redacao anterior do 12-13 foram **retiradas por escrito**.
3. **`resultado.py` dava "bloco inteiro" para gravacao de silencio** -- payload
   vazio decodifica vazio e `b'' == b''`. Corrigido: `--` e fora do
   denominador.
4. **`resultado.py` e `bench.py` nao leem `sync_chirp`; so o `align.py` le.**
   Pontuar uma gravacao com varredura por eles mede o risco da varredura, nao o
   beneficio. **Nao consertado de proposito** -- mexer no pontuador no meio da
   campanha move a regua debaixo dos numeros. Fica como trabalho.
5. **`console.py fetch_recording` nao separava caminho do Windows**, e o arquivo
   caia como `captures\2026...wav` no diretorio corrente.
6. **Seis defeitos no `capture_a2b.py`** achados em revisao, o pior deles uma
   falha macia saindo com codigo 0 -- o retry do driver nunca disparava e um
   ponto virava diretorio vazio sem ninguem notar.

## O achado que ainda esta aberto

**A cadeia A -> B e muito pior: 16-20% de bits errados contra 3-5% em B -> A**,
e nenhum ganho entrega bloco. Duas pistas, e elas nao se excluem:

- **A caixa de A estava comprimindo.** Com ela no maximo, cortar o ganho digital
  de 1.0 para 0.25 quase nao mexia no pico recebido (0,515-0,562 para pouco
  menos). Com ela em 0.45, o mesmo corte leva o pico de 0,345-0,375 para
  0,117-0,172, que e proporcional. As gravacoes do teste 16 estao em
  `captures-a2b/16-spk/` e **ainda nao foram pontuadas** -- e o primeiro
  comando a rodar na proxima sessao.
- **O estimador cego de piso trabalha mal neste sentido, e agora se sabe por
  que.** Investigado ate o fim; o relatorio esta em
  `resultados/INVESTIGACAO-A2B.md`. Resumo na secao seguinte.

Note que a distorcao **nao** acompanha o ganho: em A -> B o excesso entre tons
foi de +0,4 a +6,8 dB e o ganho 1.0 deu os *menores* excessos. Se a caixa
estivesse ceifando em 1.0, seria o contrario. Entao "esta alto" e verdade e
pode nao ser a causa inteira.

## A causa achada, e o conserto que ainda nao foi ao ar

`resultados/INVESTIGACAO-A2B.md` tem tudo. O essencial:

**O AGC existe e nao e a causa.** A deriva esta la -- cerca de 3,5 dB ao longo
do burst, inclinacao de -0,99 dB/s em A -> B contra +0,21 em B -> A, e o meio
segundo inicial 1,6 dB acima do resto. Mas um ganho global multiplica os 16
tons igualmente, e constante dentro do simbolo e some do `argmax` e da margem.
O conserto que essa hipotese pedia -- normalizar cada simbolo pela propria
energia -- foi medido e **piora**: 82,6% para 78,8%. Fica registrado como morto
para ninguem tentar de novo.

**A causa e realimentacao positiva na exclusao do vencedor.** `_update_floor`
deixa o `argmax` de fora de cada atualizacao, o que e correto enquanto quase
todo simbolo acerta -- e o `CLAUDE.md` explica por que. Com 38% de simbolos
errados vira um laco: o tom transmitido que perde entra no proprio piso e o
levanta; o tom que vence sem ter sido transmitido tem seu pico de ruido
removido do proprio piso e o abaixa. O tom 0 (888 Hz) perde so 2,1% das vezes e
acumula vies de **-6,01 dB** -- piso 6 dB baixo, escore 6 dB inflado. O vies
varre de -6,01 a +3,92 dB entre o tom 0 e o 15, e nao acompanha nem a SNR nem a
taxa de perda, que e como se sabe que e o laco e nao o canal.

E por isso que `fecrep 2` nao resgatava nada neste sentido: os valores soft nao
estavam incertos, estavam **confiantemente errados**, que e o pior caso para um
Viterbi soft. O vies *medio* e parecido nos dois sentidos; o que nao cancela e
o espalhamento por tom, quase 3x maior em A -> B.

**O conserto: nao excluir ninguem, e limitar o quanto cada simbolo contribui**,
com media mais curta. Tres parametros novos em `MaryDemodulator`, com o padrao
igual ao comportamento de hoje:

    floor_alpha 0.02 -> 0.05     floor_clip None -> 8.0     floor_top 1 -> 0

| corpus | bits hoje | bits novo | blocos hoje | blocos novo |
|---|---|---|---|---|
| A -> B (12) | 79,1% | **90,2%** | 0 de 12 | **9 de 12** |
| B -> A rep (12) | 89,6% | 91,1% | 12 de 12 | 12 de 12 |
| B -> A acorde-off (3) | 96,0% | 96,7% | 3 de 3 | 3 de 3 |

Pareado sobre a mesma gravacao, le mais bits em **27 de 27**, sem uma perda. E
passa do teto do oraculo de ruido (87,6%, 4/12), porque o oraculo e um divisor
estatico e este acompanha a deriva tambem.

**As duas metades sao necessarias, e a ordem importa:** so `alpha 0.05` da +1,8
ponto e zero bloco; so o teto *mantendo* a exclusao (`clip 3x`) da 57,9%, vinte
pontos **abaixo** de nao fazer nada. Adotar meio conserto e pior que nenhum.

**Estado:** `modem.py` e `bench.py` estao modificados na arvore com os
parametros e com um memo em `_energies` (valores identicos, demodulador 8x mais
rapido -- sem ele a varredura de 21 variantes nao caberia). O padrao continua
sendo o de hoje, entao nada muda sob os testes ja feitos.
`./venv/bin/python loopback_test.py` imprime `SUCCESS!` com os padroes atuais
**e** com os do vencedor. Confira voce mesmo antes de commitar.

**O que falta e o que decide:** 27 gravacoes nao sao o link no ar. Re-medir
A -> B com o parametro novo antes de adotar. Se confirmar, isso muda a contagem
de blocos de todos os testes M-arios ja feitos -- o que e barato, porque a
pontuacao e offline e o audio esta guardado, e e a mesma repontuacao que a
branch `feat/clock-tracking` ja exigia.

## A outra causa, medida ate o fim: a caixa de A comprimia

Esta e a primeira das duas pistas da secao anterior, e agora esta fechada. O
metodo importa porque "esta alto" nao e uma medida: **o volume do PipeWire e o
ganho digital chegam ao mesmo lugar por caminhos diferentes**, entao variar um
com o outro fixo separa a compressao do nivel.

Com o ganho digital fixo em 0.5, 3 trials por ponto, bits no relogio travado
(a regua estavel; blocos ao lado como numero honesto):

| caixa de A | bits (travado) | blocos, `mary atual` |
|---|---|---|
| 1.00 | 82,3% | 0 de 3 |
| 0.45 | 85,1% | 0 de 3 |
| **0.20** | **88,0%** | 3 de 3 travado, 2 de 3 no gate |
| 0.10 | 82,2% | 1 de 3 |

Um U invertido com o joelho em **0.20**. Acima disso a caixa comprime; abaixo
acaba o sinal -- em 0.10 o rms recebido caiu para 0,0055-0,0066 e uma das tres
gravacoes saiu contaminada por um evento da sala.

**A prova de que era compressao, e nao nivel, esta na inversao.** Com a caixa
em 0.45 o ganho digital andava ao contrario do que deveria: *quanto menor,
melhor*, 81,4% em 1.0 contra 89,1% em 0.25, com o pico recebido em apenas
0,10-0,19 -- longe de qualquer coisa que o *receptor* pudesse ceifar. Com a
caixa em 0.20 essa inversao some:

| ganho digital @ caixa 0.20 | bits (travado) |
|---|---|
| 1.0 | 88,2% |
| 0.5 | 88,2% |
| 0.25 | 85,2% |

Chapado de 1.0 a 0.5 e caindo em 0.25, que e o que uma cadeia linear faz. **O
sinal de que ainda ha compressao no caminho e o ganho digital menor vencer**;
quando ele parar de vencer, a cadeia esta linear. Isso vale como teste de
bancada e custa 6 trials.

E o mesmo achado do sentido B -> A, na outra ponta: **linearidade valeu mais
que qualquer mudanca de codigo**, e neste sentido ela sozinha levou de 0 de 12
blocos a 8 de 9.

`resultados/16-SPK-A2B/`, `resultados/08B-MARY-GAIN-A2B/`,
`resultados/17-SPK-LEVEL-A2B/`.

## O conserto do piso, replicado -- e o limite dele

O conserto da secao anterior (`floor_top=0, floor_clip=8.0, floor_alpha=0.05`)
foi re-medido em um corpus **novo**, gravado depois de baixar a caixa, que a
investigacao original nao viu. Nas 12 gravacoes de `08b-mary-gain` (caixa em
0.45): **9 de 12 blocos contra 4 de 12** do padrao de hoje. Replica limpa, em
audio independente.

**Mas ele nao e uma melhora geral, e o corpus mais linear mostra isso.** Nas 3
gravacoes com a caixa em 0.20 e ganho 0.5 -- a cadeia menos distorcida ja
medida neste sentido -- o conserto deu **0 de 3** e o padrao de hoje deu 2 de
3. E as falhas tem carater diferente: o padrao erra por pouco (41-47 dos 48
bytes) e o conserto erra **0 de 48**, que e assinatura de sync perdido, nao de
bits ruins. O mesmo aconteceu em 3 das 12 gravacoes de 0.45, todas entre as de
menor nivel recebido.

Leitura: o conserto e um reparo para cadeia distorcida, medido contra corpora
distorcidos, e **degrada quando o nivel recebido cai**. A explicacao que se
encaixa e que sem a exclusao do vencedor, e com media mais curta, o piso comeca
a seguir o sinal em SNR baixa, o contraste desaba e o gate perde a trava -- por
isso 0 bytes em vez de poucos bytes. **Nao adotar como padrao antes de medir
nos dois regimes.** Um `floor_clip` mais generoso ou um piso que so muda de
regime abaixo de um contraste minimo sao as duas coisas a tentar, e nenhuma foi
medida.

Note tambem que, no corpus de 0.45, o oraculo de ruido **deixou de ganhar** do
estimador cego: 85,9% contra 87,0% travado, quando na caixa em 1.00 era 87,6%
contra 82,6%. Ou seja: **parte do que parecia defeito do estimador de piso era
a compressao da caixa**, e some junto com ela. As duas pistas da secao anterior
nao eram independentes.

## Transferencia da gravacao: pelo cabo ou pela rede

O `puxa` anda a 8,1 kB/s -- dois minutos por gravacao de dez segundos, ou seja
horas movendo arquivo e minutos medindo. `netlink.py` resolve: servidor HTTP da
stdlib no lado do console, `urllib` do outro, e **a maquina remota empurra**
(conexao para fora, sem esbarrar no firewall de entrada do Windows). O cabo
carrega a URL, entao nenhum lado precisa saber o endereco do outro.

Estado: **implementado, nao validado.** Faltou uma coisa so, e ela ja foi feita
pelo usuario: `sudo ufw allow 8765/tcp`. O `ufw` de A estava ativo e descartava
a entrada em silencio, o que le como timeout e e indistinguivel de isolamento
de clientes no ponto de acesso.

Para conferir em um comando, com o console parado:

```bash
./venv/bin/python -c "
import netlink, subprocess, os
os.makedirs('/tmp/rx', exist_ok=True)
with netlink.Receiver('/tmp/rx') as rx:
    print('url', rx.url)
    print(subprocess.run(['./venv/bin/python','rcmd.py','--port','/dev/ttyUSB0',
                          '--timeout','40', f'rede {rx.url}'],
                         capture_output=True, text=True).stdout)
"
```

Se ainda der timeout, as duas maquinas estao numa rede que isola clientes.
**Os scripts da campanha ja estao com `--serial-only`** por isso: o
`capture_a2b.py` cai para o cabo sozinho, mas a prova gasta alguns segundos por
trial e sao cerca de cinquenta trials. Tire a opcao de `run_a2b_rest.sh` e
`run_a2b_rep.sh` no dia em que `rede <url>` responder `pong` da outra ponta.

O que ja se sabe, para nao refazer o diagnostico: antes da regra de `ufw` as
duas maquinas nao se alcancavam nem estando na mesma sub-rede, em nenhuma das
duas direcoes, e A alcancava o gateway normalmente. Isso deixou duas causas
possiveis com o mesmo sintoma -- `ufw` descartando entrada em silencio, e o
ponto de acesso isolando clientes. A regra elimina a primeira; **so o teste
acima separa as duas**, e ele nunca chegou a rodar.

Uma alternativa comecada e nao terminada: subir o baud do cabo para 921600, com
reversao automatica (o agent volta a 115200 se ninguem falar na taxa nova em
25 s, para que uma taxa que o adaptador nao segure nao leve o canal junto).
`serial_link.Control.set_baud` ja existe; o comando `baud` no `console.py`
**nao foi escrito**.

## O que falta medir

**Tudo daqui para baixo espera a maquina B voltar.** E tudo neste sentido roda
com a caixa de A em **0.20**, que e o joelho medido -- confira o volume antes
de cada campanha, porque ele volta ao maximo quando a caixa reconecta.

1. **Refazer 08 `MARY-GAIN-A2B` no volume novo, com mais trials.** Ha 3 trials
   por ponto em 1.0, 0.5 e 0.25 na caixa em 0.20; 1.0 e 0.5 empatam em 88,2% e
   3 trials nao separam um empate. Seis por ponto decide, e decide o ganho que
   todos os testes seguintes vao usar. Enquanto nao decidir, use **0.5**: e o
   melhor dos dois no par com mais blocos e deixa margem para a caixa.
2. **14 `FEC-REP`** -- as 7 gravacoes em `captures-a2b/14-fec-rep/` sao do
   volume 1.00, a cadeia comprimida, e deram 0 blocos. **Refazer.** Elas nao
   medem o link, medem a compressao, e agora existe corpus melhor.
3. Depois: **04, 05, 06, 07, 09, 10, 11 e 12-13** neste sentido, por
   `run_a2b_rest.sh <ganho>`.

**A decisao que estava aberta caducou.** Era "se nem `fecrep 4` entregar bloco,
a tabela e uma coluna de zeros -- vale medir assim ou atacar a causa antes?" A
causa foi atacada e cedeu: com a caixa em 0.20 sao 8 blocos de 9 em `fecrep 1`.
Blocos inteiros voltaram a discriminar e a campanha pode seguir a regua normal.

**Duas coisas de codigo, nenhuma no caminho critico:**

- Re-medir o conserto do piso nos dois regimes de nivel antes de mudar o
  padrao (ver a secao acima). Se for adotado, repontuar tudo -- barato, o audio
  esta guardado.
- O `--serial-only` custa 85 s por trial movendo 700 kB pelo cabo, contra ~7 s
  de audio. **A campanha inteira e transferencia de arquivo, nao medida.** O
  teste de `rede <url>` de uma linha continua sem nunca ter rodado; e o maior
  ganho de tempo disponivel e leva um comando.

**O 15 `PKT-ARQ` nao existe no sentido A -> B.** O `recvfile.py` puxa com o
receptor dirigindo, e o receptor precisa de audio e serial ao mesmo tempo, que
e o lado do console. Faria falta um `sendfile.py`, ou ensinar o agent a
receber. E trabalho de codigo, nao de medida, e nunca esteve no plano.

## Coisas que quebram se voce nao souber

**Uma sessao do Claude Code por vez neste repositorio.** Duas rodaram juntas
nesta bancada e reescreveram `CLAUDE.md`, `HANDOFF.md`, `modem.py` e `bench.py`
debaixo da que estava medindo. Nada se perdeu por sorte, nao por desenho: o
cabo serial tem um dono so, e os arquivos de estado nao tem tranca.

**O microfone de A as vezes nao acorda.** Logo depois de outro processo soltar o
dispositivo ele entrega zeros. O `capture.py` aborta alto; espere 4 s e repita
o ponto. Aconteceu uma vez nesta campanha, no `fecrep 2` do teste 14 B -> A.

**A caixa Bluetooth anuncia zero canais por um a dois segundos** depois de
liberada. O `capture_a2b.py` tenta quatro vezes com 3 s entre elas.

**`grave` satura em 120 s sem avisar.** O `capture_a2b.py` agora aborta o trial
em vez de gravar uma janela truncada. O maior ponto da campanha e o MFSK votado
com 48 bytes em `fecrep 2`, 27,6 s.

**Bloco de zero exato nao e sala silenciosa, e fonte ausente.**

**Conversa na sala contamina medida de piso.** Voz ocupa 100-3000 Hz.

**Blocos recuperados e uma medida ruim para escolher parametro fino.** Use
acuracia de bits do `align.py`, que e estavel, e deixe blocos como numero
honesto separado.

**`marygap`, `maryband`, `marychord`, `fecrep`, `fecpar` e `syncsweep` tem que
ser iguais nos dois lados.** O `capture.py` manda todos, ligados ou desligados,
no inicio de cada rodada -- e passou a mandar os desligados por causa do defeito
1 acima.

## Codigo

Main em `9acc715` mais o que estiver por commitar. As quatro branches em
worktrees continuam sem merge; ver a versao anterior deste arquivo no git para
a descricao delas. `feat/clock-tracking` continua valendo a pena: nas 30
gravacoes M-arias de hoje a regra atual deu 20/30 blocos e a correlacao mole
com coerencia deu 29/30. Mergear muda a contagem de todos os testes ja feitos,
o que e barato -- a pontuacao e offline e o audio esta guardado.
