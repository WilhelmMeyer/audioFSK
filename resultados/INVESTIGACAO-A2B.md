# INVESTIGACAO-A2B -- por que o sentido A -> B decodifica tao pior

- **Codigo:** commit `82ef87b` mais os parametros de piso acrescentados por
  esta investigacao (`floor_norm`, `floor_clip`, `floor_top` em
  `MaryDemodulator`), todos com padrao igual ao comportamento anterior.
- **Quando:** 2026-09-03, so leitura de gravacoes -- nenhum hardware foi
  tocado, uma campanha estava no ar ao lado.
- **Corpora:** `captures-a2b/08-mary-gain/` (12 gravacoes, A -> B, M-ario,
  `fecrep 1`, 48 bytes, ganhos 1,0/0,7/0,5/0,25 com 3 trials cada),
  `captures-rep/` (12 gravacoes, B -> A, `rep1`/`rep2`/`rep4`) e
  `captures-chord/` rotulo `chord-off` (3 gravacoes, B -> A).
- **Regua:** acuracia de bits sempre no melhor deslize forcado, para toda
  linha; blocos inteiros como numero separado, decodificados no deslize que
  os bits escolheram. Nenhuma gravacao sem payload entrou.

## O que se queria explicar

`align.py` sobre as 12 gravacoes A -> B dava:

| leitura | A -> B | B -> A |
|---|---|---|
| gate early/late | 79,1%, 0/12 | 89,6%, 12/12 |
| relogio travado no melhor offset | 82,6%, 0/12 | 90,7%, 12/12 |
| travado, dividindo pelo GANHO por tom | 81,7%, 1/12 | 76,4%, 10/12 |
| travado, dividindo pelo RUIDO por tom | **87,6%, 4/12** | 90,7%, 12/12 |

A ultima linha contra a penultima e a pista: em B -> A o estimador cego de
piso ja esta no teto (90,7 contra 90,7), e em A -> B faltam 5 pontos. Ou
seja, **neste sentido o piso corrente por tom esta trabalhando mal.**

A hipotese levantada era AGC no microfone de B: se o ganho de recepcao se
move durante o burst, o piso -- que e uma media longa -- fica defasado.

## 1. A medida de envelope: existe deriva, e ela nao explica nada

Medir o rms em janelas de 100 ms nao serve: o comeco do frame e o preambulo,
que em M-ario e um tom so, e um tom so cai onde o pente da sala o deixa cair
-- em A -> B ele chega 1 a 2 dB acima da media dos 16 tons e em B -> A cerca
de 6 dB abaixo. Isso parece um degrau de AGC e nao e; e a resposta em
frequencia lida em um ponto.

A medida certa divide o pente fora. Para cada simbolo se sabe qual tom foi
enviado (`spectro.tx_tone_indices`); toma-se a energia daquele tom e
divide-se pela energia media com que **aquele mesmo tom** chega ao longo do
burst. O que sobra e o ganho instantaneo, com o pente cancelado porque cada
tom so se compara consigo mesmo. Suavizado em 200 ms, sobre a regiao de
payload:

| | faixa (dB) | p5-p95 (dB) | inclinacao (dB/s) | 0,5 s inicial vs resto |
|---|---|---|---|---|
| A -> B (12) | 5,45 | 4,10 | **-0,99** | **+1,59 dB** |
| B -> A rep (12) | 4,84 | 2,69 | +0,21 | -1,98 dB |
| B -> A chord-off (3) | 4,18 | 2,63 | -0,06 | -0,08 dB |

**A deriva existe e e sistematica.** Em A -> B as 12 gravacoes tem
inclinacao negativa, de -0,53 a -1,63 dB/s, e nas 12 o meio segundo inicial
do payload chega de 1,0 a 2,4 dB mais alto que o resto. Isso e a assinatura
de um compressor abrindo no ataque e fechando depois: cerca de 3,5 dB ao
longo de um burst de 3,4 s. Em B -> A a inclinacao e cinco vezes menor e de
sinal contrario.

**E mesmo assim a hipotese do AGC nao explica o buraco de 5 pontos, por uma
razao que vale a pena escrever.** Um ganho global multiplica os 16 tons pelo
mesmo numero. Dentro de um simbolo esse fator e constante, some do `argmax` e
some de `max(uns) - max(zeros)` no caminho soft. O erro que a deriva injeta
no piso e **modo comum**, e modo comum nao muda decisao nenhuma. Confirmado
pelo experimento: normalizar cada simbolo pela propria energia media --
exatamente o conserto que a hipotese pede -- **piora** A -> B, de 82,6% para
78,8%.

O que estraga a comparacao nao e o piso estar errado, e ele estar errado
**de forma diferente em cada tom**. Medindo o piso cego contra o piso oraculo
(a energia media do tom nos simbolos em que ele nao foi transmitido), com o
modo comum removido:

| | vies medio | vies maximo | desvio por tom | acerto de simbolo |
|---|---|---|---|---|
| A -> B | +0,80 dB | +4,75 dB | **2,11 dB** | 61,8% |
| B -> A | +0,44 dB | +1,42 dB | **0,76 dB** | 79,7% |

O vies medio, que cancela, e parecido nos dois sentidos. O espalhamento
**por tom**, que nao cancela, e quase tres vezes maior em A -> B.

## 2. De onde vem o espalhamento: a exclusao do vencedor tem realimentacao

`_update_floor` deixa o tom vencedor de fora de cada atualizacao, para que o
piso nao persiga o sinal que existe para medir. Em um canal com margem isso
esta certo: o vencedor quase sempre e o tom transmitido, e o que se exclui e
sinal. Quando o `argmax` erra -- 38% dos simbolos em A -> B -- a regra passa a
fazer duas coisas erradas ao mesmo tempo, e a segunda e uma realimentacao
positiva:

- o tom **transmitido que perdeu** entra no proprio piso com toda a sua
  energia, o que sobe o piso dele, o que faz ele perder de novo;
- o tom que **venceu sem ter sido transmitido** tem o proprio pico de ruido
  removido do proprio piso, o que desce o piso dele, o que faz ele vencer de
  novo.

O vies por tom em A -> B mostra o segundo efeito com clareza. O tom 0
(888 Hz) perde so 2,1% das vezes e tem vies de **-6,01 dB**: o piso dele esta
6 dB abaixo do verdadeiro, o que infla o escore dele em 6 dB. O vies varre de
-6,01 dB no tom 0 a +3,92 dB no tom 15, dez dB de rampa, e nao acompanha nem
o SNR (correlacao +0,32) nem a taxa de perda (+0,19). Em B -> A o mesmo vies
fica dentro de +-0,7 dB fora de dois tons.

O gatilho e a margem: o SNR por tom medido e 10,3 dB em A -> B e 13,2 dB em
B -> A (pior tom: +0,9 contra +1,4 dB), com 3 dB a mais de espalhamento do
pente. Tres dB de canal pior colocam a estimativa de piso na regiao onde ela
se realimenta, e ai a perda deixa de ser proporcional.

**A hipotese do AGC nao se sustenta como explicacao.** A deriva foi medida e
e real, mas e modo comum; o que custa os 5 pontos e a selecao dentro da
atualizacao do piso.

## 3. O conserto

Se o problema e *selecionar* quem entra na media, a resposta e nao
selecionar: incluir os 16 tons e **limitar** o quanto um simbolo pode
contribuir, em multiplos do piso corrente. O teto tira o vencedor legitimo do
caminho sem o vies de selecao, e a media mais rapida encurta a memoria dos
erros que ainda passarem.

Tres parametros novos em `MaryDemodulator`, todos com padrao igual ao de
hoje:

- `floor_top` -- quantos tons mais altos ficam fora da atualizacao. `1` e o
  vencedor sozinho, como antes; `0` nao exclui ninguem.
- `floor_clip` -- teto, em multiplos do piso corrente, para o que um simbolo
  pode contribuir. `None` e sem teto, como antes.
- `floor_norm` -- divide cada simbolo pela propria energia media antes de
  comparar e de atualizar. Medido e ruim, mantido porque a medida vale.

### Placar, as tres corpora, mesma regua

| variante | A->B bits | A->B blocos | B->A bits | B->A blocos | chord bits | chord blocos |
|---|---|---|---|---|---|---|
| **atual** | 79,1% | 0/12 | 89,6% | 12/12 | 96,0% | 3/3 |
| norm/simbolo | 74,6% | 0/12 | 87,9% | 10/12 | 95,0% | 3/3 |
| alpha 0,005 | 75,2% | 0/12 | 88,8% | 11/12 | 95,6% | 3/3 |
| alpha 0,05 | 80,9% | 0/12 | 89,7% | 11/12 | 95,9% | 3/3 |
| alpha 0,10 | 82,5% | 0/12 | 89,9% | 12/12 | 95,7% | 3/3 |
| alpha 0,15 | 81,4% | 0/12 | 89,9% | 12/12 | 95,3% | 3/3 |
| alpha 0,20 | 82,2% | 0/12 | 89,5% | 12/12 | 95,0% | 3/3 |
| norm + alpha 0,10 | 78,1% | 0/12 | 89,0% | 11/12 | 95,0% | 3/3 |
| clip 3x (com exclusao) | 57,9% | 0/12 | 82,4% | 6/12 | 93,3% | 2/3 |
| clip 1,5x (com exclusao) | 60,9% | 0/12 | 83,1% | 9/12 | 91,7% | 3/3 |
| top2 fora | 71,6% | 0/12 | 89,0% | 12/12 | 95,4% | 2/3 |
| top4 fora | 62,1% | 0/12 | 87,1% | 5/12 | 94,5% | 3/3 |
| sem excl + clip 2x | 66,5% | 0/12 | 85,5% | 10/12 | 94,2% | 3/3 |
| sem excl + clip 3x | 77,6% | 0/12 | 87,9% | 11/12 | 95,5% | 3/3 |
| sem excl + clip 5x | 86,6% | 3/12 | 89,2% | 10/12 | 96,2% | 3/3 |
| sem excl clip3 a.05 | 87,2% | 4/12 | 89,1% | 7/12 | 95,8% | 3/3 |
| sem excl clip5 a.05 | 88,8% | 8/12 | 89,9% | 6/12 | 96,4% | 3/3 |
| sem excl clip5 a.10 | 90,3% | 10/12 | 90,7% | 10/12 | 96,4% | 3/3 |
| sem excl clip8 | 87,3% | 4/12 | 90,0% | 10/12 | 96,0% | 3/3 |
| **sem excl clip8 a.05** | **90,2%** | **9/12** | **91,1%** | **12/12** | **96,7%** | **3/3** |
| norm + sem excl clip3 | 84,2% | 4/12 | 87,8% | 11/12 | 94,9% | 3/3 |

Bits na coluna do gate -- o alinhamento que um receptor de fato consegue.
Blocos idem. (Com o relogio travado no melhor offset o vencedor faz 91,4%
com 12/12 em A -> B, contra 82,6% e 0/12 de hoje.)

### O vencedor

**`floor_top=0`, `floor_clip=8.0`, `floor_alpha=0.05`.**

| | bits, hoje | bits, novo | blocos, hoje | blocos, novo |
|---|---|---|---|---|
| A -> B (12) | 79,1% | **90,2%** | 0 de 12 | **9 de 12** |
| B -> A rep (12) | 89,6% | **91,1%** | 12 de 12 | 12 de 12 |
| B -> A chord-off (3) | 96,0% | **96,7%** | 3 de 3 | 3 de 3 |

Nada piora em lugar nenhum. Em A -> B sao 11,1 pontos de bits e a diferenca
entre nao entregar bloco nenhum e entregar 9 de 12, a `fecrep 1`. E passa por
cima do teto que o oraculo de ruido marcava (87,6%, 4/12) porque o oraculo e
um divisor **estatico** por tom, e este acompanha a deriva tambem.

**Pareado, sobre a mesma gravacao, le mais bits em 27 de 27.** Delta de
+7,8 a +13,6 pontos nas 12 de A -> B e de +0,3 a +2,6 nas 15 de B -> A.
Duas medias sobre trials ruidosos nao estabeleceriam isso; 27 de 27 sem uma
unica perda, sim.

### As duas metades sao necessarias e nenhuma funciona sozinha

- So a media rapida (`alpha 0,05`): +1,8 ponto em A -> B, zero bloco.
- So o teto, **mantendo a exclusao** (`clip 3x`): 57,9%, vinte pontos
  **abaixo** de nao fazer nada. Excluir o vencedor e depois limitar o resto
  tira a energia duas vezes e o piso desaba.
- Sem exclusao e sem teto nao foi medido porque nao ha o que medir: o piso
  passaria a perseguir o sinal, que e exatamente o motivo pelo qual a
  exclusao existe.
- Sem exclusao com teto de 2x tambem e ruim (66,5%): o teto tem de deixar
  passar o ruido genuino, e 2x do piso ainda e ruido. O joelho esta entre 5x
  e 8x.

## 4. O que fica

- `modem.py`, `MaryDemodulator.__init__` (linha 799) e `_update_floor`: tres
  parametros novos, padrao igual ao de hoje. `loopback_test.py` continua
  imprimindo `SUCCESS!` com os padroes atuais **e** com os do vencedor.
- `modem.py`, `_energies`: memo de uma entrada. A mesma janela era pedida
  duas vezes por simbolo no relogio travado e cinco no gate; os valores sao
  identicos e o demodulador ficou 8 vezes mais rapido (3,9 s -> 0,46 s por
  gravacao). Sem isso esta varredura nao caberia numa tarde.
- `bench.py`, `FEC_VARIANTS`: as ideias de M-ario nao cabiam em `VARIANTS`,
  que e pontuado pelo caminho de bytes duros -- nesta camada uma loteria de
  nibble. Agora uma captura codificada e pontuada por todas as linhas da
  lista nova.

**A mudanca exata, se for para adotar:** em `modem.py:797-799`, trocar
`floor_alpha=0.02` por `0.05`, `floor_clip=None` por `8.0` e `floor_top=1`
por `0`. Nao foi feita: o padrao ficou como estava para que nenhuma medida ja
registrada mude de valor sob os pes de quem a leu. A decisao e de quem manda
no link.

## 5. O que isto **nao** diz

- Nao mede o link no ar. Sao 27 gravacoes de duas manhas; a sala nao esta
  aqui. Antes de adotar, vale re-medir A -> B com o parametro novo.
- Nao explica por que A -> B tem 3 dB menos de SNR por tom. Explica so por
  que esses 3 dB custam muito mais do que 3 dB deveriam custar: eles jogam a
  estimativa de piso na regiao onde ela se realimenta.
- As 12 gravacoes de A -> B varrem ganho de 1,0 a 0,25 e o ganho nao aparece
  em lugar nenhum deste resultado -- o vies por tom e o mesmo nos quatro
  pontos. Confere com o que a camada promete e com 08-MARY-GAIN.
- `fecrep 1` em todas as 12 de A -> B. A `fecrep 2` provavelmente todas as
  variantes recuperam tudo e a comparacao nao mede nada, que e o motivo de
  calibrar a `fecrep 1`.
