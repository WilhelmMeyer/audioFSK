<!--
FONTE DO TEXTO. VII SIMECA / IFPR. Artigo do modem acustico.

Montagem: ./artigo/monta.sh  (gera artigo_modem.docx e artigo_modem.pdf; aceita --verifica, --sem-figuras)
Conversor: artigo/simeca-md. Correcao no conversor se faz la, nunca por copia.
Estilo: artigo/estilo.md. Ler antes de redigir qualquer secao.

ESTRUTURA (decisao do autor, 2026-09-06): 1 INTRODUCAO (uma lauda no maximo), 2 PRINCIPIO DE FUNCIONAMENTO,
  3 METODO DE MEDICAO, 4 RESULTADOS EXPERIMENTAIS, 5 CONSIDERACOES FINAIS. O modelo do evento sugere uma
  secao de fundamentacao teorica; e a forma de outro professor, nao regra de conteudo, e nao se segue. Nao ha
  secao de teoria: cada mecanismo traz a teoria minima que o sustenta, no ponto em que e usado. Objetividade
  antes de volume, em toda secao.
Secoes nao numeradas do modelo (AGRADECIMENTOS, FINANCIAMENTO, DECLARACAO DE IAG, CONFLITO, REFERENCIAS) ficam.
Extensao: 4 a 10 laudas. Resumo 150-300 palavras; 3 a 5 palavras-chave separadas por ponto final.
Legenda de figura ABAIXO do elemento; legenda de tabela ACIMA. Equacao centralizada e numerada a direita.
Citacao ABNT autor-data; "et al." em italico e sem ponto em "et".

Orcamento, em palavras de prosa (~750 por lauda; figura ou tabela 150-250):
  resumo 300 | introducao 450 | principio 900 | metodo 350 | resultados 750 | consideracoes 200
Contagem: wc -w artigo/artigo_modem.md  (inclui comentarios; descontar)

Convencoes: um paragrafo = uma linha; sem travessao na prosa; equacoes $...$ e $$...\tag{N}$$;
  figura como ![](figuras/x.png "escala") seguida da linha "Figura N - legenda";
  "Tabela N - legenda" na linha antes da tabela em pipes; numeracao e conferida, nao gerada.
Nenhum numero entra sem origem em resultados/<pasta>.
CITACOES: nenhuma referencia foi inventada. "(CITAR: ...)" marca onde entra aglomerado e de que tipo.

ENQUADRAMENTO (decisao do autor, 2026-09-05): artigo didatico. Apresenta o sistema proposto, compara
brevemente com outros meios de transmissao, avalia o problema do canal acustico e propoe uma solucao para
este caso. Nao pretende substituir outro meio nem reivindicar melhoria sobre a literatura.

NOMENCLATURA (decisao do autor, 2026-09-05; fixa, nao muda mais):
  M-aria: modulacao de ordem M, em que cada simbolo e um tom escolhido entre M frequencias e carrega
    log2(M) bits. Abrange as quatro formas, inclusive a binaria (M = 2).
  FSK: modulacao por chaveamento na frequencia, do ingles *frequency shift keying* (FSK). Designa a 2-FSK.
  MFSK: chaveamento em multiplas frequencias, do ingles *multiple frequency shift keying* (MFSK). Designa
    as que usam mais de duas frequencias: 5x2-FSK (nas duas variantes) e 16-FSK.
  As quatro formas, sempre por esta notacao: 2-FSK; 5x2-FSK votada; 5x2-FSK multicanal; 16-FSK.
  Nunca: "20-FSK"; "M-ario" sem o M explicado; "MFSK" como nome de uma unica forma; nomes internos do
    codigo (mary, mfsk-par, fecrep) na prosa.
  Desvio em relacao ao codigo e ao CLAUDE.md da raiz: la "MFSK" e a de cinco pares e "M-ary" e a de
    dezesseis tons. No artigo nao. A correspondencia esta no CLAUDE.md da raiz.
  Forma de toda sigla estrangeira: nome em portugues, "do ingles", termo em italico, sigla entre
    parenteses depois do termo.

ESTADO DO TEXTO: resumo aprovado 2026-09-05. Secoes 1 e 2 redigidas 2026-09-06 na estrutura acima, por
  revisar. Secoes 3, 4 e 5 sao esqueleto.
-->

# Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele

<!--
Titulo: objeto + problema + solucao, tom didatico, sem promessa de melhoria. Maximo 3 linhas. Candidatos:
- Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele
- Um modem acústico com placa de som e microfone: da modulação binária ao M-ário com correção de erros
- Enlace de dados pelo ar audível: o que o canal faz com o sinal e o que se fez a respeito
-->

**AUTORES:**

<!--
nome | ORCID | filiacao | e-mail. Modelo exige ORCID de TODOS os autores, com o link correto.
Linha 1: o proprio Winderson preenche ORCID, campus e e-mail.
-->

1. Winderson | | IFPR | 
2. Jefferson Wilhelm Meyer Soares | 0000-0003-3372-9298 | IFPR, Campus Jacarezinho | jefferson.soares@ifpr.edu.br

**DOI:** https://doi.org/10.5281/zenodo.XXX

## RESUMO

<!--
Redigido e aprovado em 2026-09-05. Ordem: o que apresenta; o problema, que e o meio; a solucao em duas
camadas; a implementacao e o metodo; os numeros. So a ultima frase tem numero.
Fonte dos numeros: resultados/14-FEC-REP, resultados/15-PKT-ARQ.
-->

Este artigo apresenta a transmissão de dados por som audível entre dois computadores, com alto-falante e microfone comuns, expondo o enlace à aplicação como uma porta serial. O meio acústico impõe condições severas: a banda audível comporta poucas unidades de informação por segundo, aqui chamadas de símbolos, a amplitude que chega não é a que saiu, frequências vizinhas chegam com dezenas de decibéis de diferença, o eco de um símbolo invade o seguinte, o ruído e a fala ocupam a mesma banda, e o hardware também pode saturar e distorcer o sinal. Tratamos essas dificuldades em duas camadas. Na física, conferimos quatro modulações de ordem M, ditas M-árias, em que cada símbolo é um tom escolhido entre M frequências e carrega tantos bits quanto essa escolha permite: a 2-FSK binária, modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), e três por chaveamento em múltiplas frequências, do inglês *multiple frequency shift keying* (MFSK), a 5×2-FSK com o mesmo bit em cinco canais e decisão por voto, a 5×2-FSK multicanal com cinco bits em paralelo, e a 16-FSK com quatro bits por símbolo. Mesmo na melhor dessas formas, parte dos bits pode chegar com erro ou se perder, e na camada de enlace implementamos a correção antecipada de erros, do inglês *forward error correction* (FEC), o sincronismo de quadro por palavra de referência, a segmentação do arquivo em pacotes com verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), e a retransmissão automática, do inglês *automatic repeat request* (ARQ). Medimos cada recurso sobre gravações do mesmo enlace, para comparar as variantes sobre o mesmo ar. Na melhor configuração o enlace entregou cerca de 11 bytes por segundo com os quatro blocos de ensaio íntegros, e 12 blocos íntegros de 12 na campanha de redundância; um arquivo de 1334 bytes chegou idêntico em 21 pacotes de 21, sem reenvio.

**PALAVRAS-CHAVE:** Modem acústico. Modulação por chaveamento de frequência. Codificação convolucional. Canal acústico.

## 1 INTRODUÇÃO

<!--
Redigida 2026-09-06, condensando a introducao e a fundamentacao de 2026-09-05 em uma lauda. Quatro
paragrafos: os meios; o fio e o ar; o caso e o que exige; o que apresentamos. Numeros so na secao 2 e na 4.
-->

Levar bytes de uma máquina a outra tem vários meios, e cada um cobra a sua instalação. O cabo entrega megabytes por segundo e exige um conector livre em cada ponta. O rádio, no Wi-Fi ou no Bluetooth, exige um transceptor, um pareamento e a permissão de operar, que nem todo ambiente concede. O infravermelho exige linha de visada. O som audível não exige nenhuma das três coisas, pois o alto-falante e o microfone já vêm em qualquer computador ou telefone, e o que ele cobra é a taxa. A Tabela 1 põe os quatro meios lado a lado. (CITAR: comunicação acústica entre dispositivos, transferência de dados por áudio)

Tabela 1 - Meios de transmissão de dados entre duas máquinas próximas, pelo hardware que cada um exige. As taxas e os alcances são ordens de grandeza correntes de cada tecnologia; a linha do som audível traz o que esta bancada mediu.

| meio | hardware exigido | taxa típica | alcance | onde cabe |
|---|---|---|---|---|
| cabo | conector livre nas duas pontas | 10⁶ a 10⁹ B/s | o comprimento do cabo | quando as duas máquinas se tocam |
| rádio | transceptor, pareamento, permissão de operar | 10⁵ a 10⁷ B/s | dezenas de metros | quando o ambiente autoriza |
| infravermelho | emissor, receptor e linha de visada | 10³ a 10⁵ B/s | poucos metros, sem obstáculo | quando há visada direta |
| som audível | alto-falante e microfone, que a máquina já tem | 10⁰ a 10¹ B/s | a mesma sala | quando nada pode ser instalado |

<!-- (CITAR: taxas correntes de cada meio) na legenda ou no corpo. Linha do som audivel: resultados/14-FEC-REP e 15-PKT-ARQ. -->

A resposta clássica para pôr dados num canal de voz é a modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), em que a portadora comuta entre duas frequências e cada uma vale um valor do bit. O padrão Bell 202 fixa 1200 e 2200 Hz a 1200 símbolos por segundo, com os bytes enquadrados em 8N1, e o receptor decide o bit pelo sinal de um discriminador de frequência. No par de fios telefônico as duas frequências chegam no mesmo nível. No ar, o canal não é um fio. O som chega pelo caminho direto e pelas reflexões da sala, que se somam com fases dependentes da frequência, e a resposta vira um pente, com mais de dez decibéis entre frequências vizinhas. O alto-falante limita os picos e o microfone comprime, os dois relógios de amostragem são independentes, e a banda é a da fala, dividida com qualquer conversa. (CITAR: Bell 202, canal acústico em ambiente fechado, resposta em pente)

O caso deste artigo é o de duas máquinas comuns numa sala, sem nada a instalar, que precisam trocar poucos bytes com confiança. Ele exige três coisas. A decisão do receptor não pode depender da amplitude, pois num pente a amplitude de cada frequência é acidente da geometria da sala. O erro precisa ser reparável onde cai, pois uma fração grande dos bits chega errada e pedir de novo não converge quando quase todo bloco vem danificado. E a medição precisa comparar variantes sem que a sala entre na conta, pois duas execuções do mesmo código na mesma sala discordam. As ferramentas do campo contra esse canal são a multiplexação por divisão ortogonal de frequência, do inglês *orthogonal frequency division multiplexing* (OFDM), as varreduras de frequência e o chaveamento em múltiplas frequências, e adotamos as mais simples delas. (CITAR: OFDM acústico, chirp acústico, MFSK acústico)

Apresentamos um modem acústico que atende a esse caso e se expõe à aplicação como uma porta serial. As contribuições são o canal medido com os próprios tons do sistema, duas camadas sobre ele, a física com quatro formas de transmissão experimentadas no mesmo enlace e a de enlace com correção antecipada de erros e sincronismo de bloco por correlação, e o método de medição por gravação, que congela o canal e permite pontuar variantes sobre os mesmos segundos de ar. As quatro formas entraram na ordem em que o enlace as exigiu, da 2-FSK herdada da telefonia à 16-FSK com um tom por vez entre dezesseis, e essa ordem é o fio da seção Princípio de funcionamento. Verificamos o conjunto entre duas máquinas na mesma sala, com a transferência de um arquivo inteiro pelo ar.

## 2 PRINCÍPIO DE FUNCIONAMENTO

<!--
Redigida 2026-09-06. Mecanismo em palavras antes de qualquer equacao; a teoria minima de cada mecanismo
entra onde ele e usado. O canal primeiro, porque tudo o que segue e resposta a ele. Fronteira da fisica:
entrega simbolos e a verossimilhanca de cada bit; o enlace opera em bits, nunca em amostras.
-->

### 2.1 O meio acústico

<!-- Fonte: resultados/02-LVL-TONE, 03-CH-CHIRP (as duas direcoes), 12-13-SYNC. -->

Um alto-falante e um microfone de uso geral respondem bem na banda da fala e perdem eficiência nos extremos. Medida tom a tom entre as duas máquinas, com a mediana de três repetições por frequência, a banda útil vai de 550 a 3500 Hz. Acima de 4 kHz a relação sinal-ruído cai, 12 dB a 4000 Hz, 8 dB a 4500 Hz e cerca de zero a 5000 Hz, e acima de 6 kHz é negativa. O ultrassom, atraente por ser uma faixa silenciosa, fica portanto fora do alcance destes transdutores, e sobra a banda audível, dividida com tudo o que soa na sala.

Dentro da banda o sinal chega ao microfone pelo caminho direto e pelas reflexões nas superfícies da sala, cada uma atrasada pelo seu percurso. Cópias atrasadas somam em fase nas frequências cujo período cabe um número inteiro de vezes na diferença de percurso e se opõem nas intermediárias, de modo que a resposta em frequência é um pente, com máximos e nulos alternados ao longo da banda. Aqui a diferença entre vizinhos a 50 Hz de resolução chega a 13 a 18 dB, e a posição dos nulos depende da geometria e muda quando alguém se move. A Figura 1 mostra a resposta medida com os dezesseis tons da 16-FSK marcados sobre o pente. As reflexões tardias prolongam o som depois que a fonte cala, e enquanto essa cauda dura a energia do símbolo anterior ainda está no microfone quando o seguinte começa. Nesta bancada a cauda não é mensurável, o sinal para no piso de ruído, mas o projeto a antecipa porque outra sala pode tê-la.

<!-- FIGURA 1, aqui: resposta em frequencia medida, tom a tom, com os 16 tons marcados sobre o pente.
Legenda ABAIXO: o que se ve, a direcao do enlace, e o que notar (a distancia entre um maximo e o nulo
vizinho e pequena diante da banda util). -->

A cadeia analógica não é linear em toda a excursão. O alto-falante limita os picos e o microfone comprime quando o nível cresce, e a energia retirada do sinal reaparece como harmônicos e produtos de intermodulação dentro da mesma banda, indistinguíveis de sinal transmitido. Além desse ponto, aumentar o nível de transmissão piora a recepção. As duas máquinas amostram com osciladores próprios, de modo que o intervalo de símbolo recebido difere do transmitido por uma fração de amostra que se acumula ao longo de um bloco.

Disso decorrem três exigências. Um tom pode cair num nulo, então a decisão do receptor não pode depender da amplitude absoluta de nenhum tom. A amplitude que chega não é proporcional à que saiu, então o nível de operação tem de ser encontrado por medição. E o relógio de símbolo tem de ser recuperado do próprio sinal, não apenas o início da transmissão.

### 2.2 Modulação

Chamamos M-ária a modulação de ordem $M$, em que cada símbolo é um tom escolhido entre $M$ frequências e carrega $\log_2 M$ bits, e a taxa de bits é o produto de (1).

$$R_b = R_s \log_2 M \tag{1}$$

Nela, $R_b$ é a taxa de bits, $R_s$ é a taxa de símbolos em bauds e $M$ é o número de frequências do alfabeto. Com a taxa de símbolos presa pela banda e pelas reflexões, subir $M$ é o caminho para subir $R_b$. Em todas as quatro formas a informação está em qual frequência soou, e o que muda entre elas é quanto a decisão depende de quão forte ela chegou. A Figura 2 mostra o espectro de cada uma. (CITAR: modulação M-FSK, detecção não coerente)

<!-- FIGURA 2, aqui: quatro paineis de espectro, sinteticos, um por forma: dois tons; cinco pares com o
mesmo bit; cinco pares com bits distintos; dezesseis tons com um so soando. E figura de METODO, a legenda
tem de dize-lo para nao ser lida como medicao. -->

A 2-FSK usa os tons do padrão Bell 202, 1200 e 2200 Hz a 1200 símbolos por segundo, bytes em 8N1. O demodulador multiplica o sinal filtrado por uma cópia atrasada de um quarto de período em 1700 Hz e filtra o produto, cuja média tem um sinal para cada tom, e o bit é esse sinal. O limite é o limiar, pois um canal que atenue um tom mais do que o outro desloca a média e enviesa toda decisão no mesmo sentido.

A 5×2-FSK votada troca o limiar por comparação. Cinco pares de tons, 200 Hz dentro de cada par, carregam o mesmo bit a 100 símbolos por segundo, e cada par vota no tom mais forte e a maioria decide, de modo que o ganho cancela e um tom forte pelo motivo errado vale um voto só. A polaridade alterna ao longo da banda para que os dois símbolos tenham a mesma frequência média, e um limiar de presença sobre a razão vencedor/perdedor separa símbolo de sala vazia, porque cinco tons de ruído também elegem um bit. Custa ser doze vezes mais lenta.

A 5×2-FSK multicanal usa os mesmos pares com um bit distinto em cada, cinco bits por símbolo. O limite das duas formas de cinco pares é potência, pois o pico que o alto-falante aceita é fixo e cinco tons simultâneos recebem um quinto dele cada um, 14 dB a menos por tom.

A 16-FSK devolve essa potência. Um só tom soa por vez entre dezesseis, quatro bits por símbolo, vizinhos em código Gray para que a confusão mais provável custe um bit. O receptor mede a energia de cada tom, divide pelo piso corrente daquele tom e elege o maior, conforme (2).

$$\hat{s} = \arg\max_k \frac{E_k}{P_k} \tag{2}$$

Nela, $E_k$ é a energia no tom $k$ dentro do símbolo e $P_k$ é a média corrente dessa energia. Como cada tom fica em silêncio quinze símbolos em dezesseis, essa média é o piso de ruído naquela frequência, e um tom num nulo do pente é comparado com o próprio nulo. Os primeiros 35% de cada símbolo são descartados como guarda. A transmissão abre com um preâmbulo alternado, que dá ao relógio de símbolo transições para travar, e fecha com uma cauda ociosa, sem a qual o último byte fica preso no demodulador.

### 2.3 Sincronismo e correção de erros

<!-- Fonte: fec.py, xfer.py, recvfile.py, modem.chirp. Tabela 2 vem da simulacao contra erros de bit. -->

O relógio de símbolo vem de um gate antecipado/atrasado guiado pelo contraste da decisão, ou de duas varreduras de 80 ms que emolduram o quadro, recuperadas por filtro casado. A primeira varredura dá o início do quadro como índice absoluto e o intervalo entre as duas dá o período medido de (3).

$$T = \frac{n_2 - n_1}{N} \tag{3}$$

Nela, $n_1$ e $n_2$ são os índices dos dois picos e $N$ é o número de símbolos do quadro, conhecido das duas pontas. Os picos são ordenados por posição e não por altura, porque as varreduras são idênticas e o canal decide qual chega mais forte. No caminho codificado o demodulador entrega, em vez do bit, a verossimilhança logarítmica de cada bit, do inglês *log-likelihood ratio* (LLR), cujo sinal é o bit e cujo módulo é a confiança, quatro por símbolo na 16-FSK.

Num canal assim uma fração de 10 a 25% dos bits chega errada, e nessa faixa detectar não basta. A verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), diz que o bloco falhou, e a retransmissão automática, do inglês *automatic repeat request* (ARQ), só converge enquanto a chance de um bloco chegar inteiro não for pequena. O bit tem de ser reparado onde cai. Usamos correção antecipada de erros, do inglês *forward error correction* (FEC), com código convolucional de comprimento de restrição $K = 7$ a taxa 1/3 e decodificação de Viterbi com decisão suave sobre as LLR, mais entrelaçamento e uma repetição $r$ combinada entre as pontas. Dentro do bloco não há 8N1, pois o bloco tem comprimento fixo e nada nele desliza, ao contrário do fluxo de bytes, em que um bit de partida errado desloca todo o resto. A Tabela 2 dá a fração de bits errados que cada variante tolera, medida em simulação e não no ar. (CITAR: códigos convolucionais, Viterbi, decisão suave)

<!-- TABELA 2, aqui. Linhas: taxa 1/2 abrupta | taxa 1/2 suave | taxa 1/3 suave | taxa 1/3 suave, r = 2.
Coluna: fracao de bits errados ate a qual o bloco de 64 bytes chega inteiro (8%, 8%, 13%, 25%). Legenda
ACIMA, dizendo que e simulacao. -->

O bloco é localizado por uma palavra de referência de 31 bits, correlacionada sobre as LLR recebidas, nunca por contagem de símbolos, pois o gate consome números diferentes de amostras por símbolo enquanto ajusta. É a mesma correlação que resolve o alinhamento de nibble da 16-FSK, em que um símbolo a mais antes do bloco troca os nibbles de todos os bytes. Acima do bloco, o arquivo vai em pacotes com número de sequência, comprimento e CRC-16, reenvio pare-e-espere dirigido pelo receptor, transmissor sem estado. A aplicação vê uma porta serial virtual.

## 3 MÉTODO DE MEDIÇÃO

<!--
Redigida 2026-09-07. Orcamento ~350 palavras. Fonte: HEADER.md das pastas de resultados.
-->

A bancada são duas máquinas comuns na mesma sala, uma com Linux e outra com Windows, cada uma com a sua placa de som a 48 kHz, chamadas A e B ao longo do texto. A transmite por uma caixa Bluetooth e B grava pelo microfone interno do próprio computador, e o sentido se inverte quando o ensaio pede, o que se anota em cada número como A→B ou B→A. O programa é escrito em Python, com o processamento de sinal isolado de toda entrada e saída, de modo que o mesmo código que roda ao vivo pontua uma gravação sem alteração, e a aplicação enxerga o enlace como uma porta serial virtual. Um cabo serial liga as duas máquinas apenas como auxílio do ensaio, para sincronizar o início da transmissão e combinar a semente que gera a carga conhecida dos dois lados; os bytes pontuados viajam somente pelo ar, e o cabo nunca transporta dado do enlace.

Julgar uma ideia transmitindo-a mede a ideia e a sala ao mesmo tempo, e a sala não fica parada: duas execuções do mesmo código discordam. Por isso o ensaio grava o lado remoto transmitindo uma carga conhecida e guarda o áudio ao lado de um registro do que foi enviado, e a pontuação é feita depois, sobre o arquivo. Uma gravação é um canal congelado, então variantes do receptor são comparadas sobre os mesmos segundos de ar, e a comparação é sempre pareada, variante contra variante na mesma gravação, e não entre duas médias.

A pontuação usa duas réguas separadas e nunca as mistura. O acerto de bits é medido com o relógio travado no melhor deslocamento por força bruta, em todas as linhas, porque escolher o deslocamento pela posição que o sincronismo encontrou pontua as falhas acima dos acertos. O bloco íntegro é o número honesto ao lado dele, e passa pelo caminho completo, com sincronismo por correlação, decodificação de Viterbi e comparação dos bytes. O alinhamento tolera deslocamento, porque este enlace apaga bytes além de corrompê-los e um byte perdido desloca todos os seguintes. O ganho de transmissão é calibrado sobre uma rajada e não sobre um tom parado, pois a troca de tom a cada símbolo produz transientes com cerca de 2,5 vezes o pico de um tom contínuo, e uma calibração feita no tom deixa a rajada ceifada. Onde uma condição foi degradada de propósito, isso é dito ao lado do número. A Tabela 3 reúne os parâmetros mantidos fixos.

Tabela 3 - Parâmetros mantidos fixos ao longo dos ensaios. Onde um ensaio variou um deles, isso é dito ao lado do número.

| parâmetro | valor |
|---|---|
| taxa de amostragem | 48 kHz nas duas máquinas |
| taxa de símbolo | 100 bauds nas formas MFSK, 1200 bauds na 2-FSK |
| banda útil | 550 a 3500 Hz |
| alfabeto da 16-FSK | 16 tons, um soando por vez, vizinhos em código Gray |
| intervalo de guarda | 35% do símbolo, descartado antes da medida |
| código corretor | convolucional, $K = 7$, taxa 1/3, Viterbi de decisão suave |
| repetição | $r = 1$, salvo onde a redundância é o eixo variado |
| palavra de referência | 31 bits, localizada por correlação |
| bloco de ensaio | 48 bytes de carga aleatória, 192 bytes na campanha de sincronismo |

## 4 RESULTADOS EXPERIMENTAIS

<!--
Redigida 2026-09-07, direto das pastas de resultados. Cada numero traz a direcao e a pasta.
Divergencias corrigidas em relacao ao esqueleto anterior estao anotadas no fim de cada bloco.
-->

### 4.1 O que o meio faz com o sinal

<!-- Fonte: resultados/01-LVL-BASE, 01-LVL-BASE-A2B, 02-LVL-TONE, 03-CH-CHIRP, 03-CH-CHIRP-A2B, 12-13-SYNC. -->

Com nada transmitindo, o piso de ruído da sala na banda útil ficou em −62,6 dBFS no microfone de A e em −55,0 dBFS no de B, medido sobre gravações de oito segundos. Um tom parado de 1700 Hz enviado de B para A chegou à mediana de −21,8 dBFS, isto é, cerca de 57 dB acima desse piso, com 7,1 dB de espalhamento entre três repetições da mesma medida. Falta de sinal, portanto, não é o problema deste enlace em nenhum dos resultados que seguem.

A varredura de frequência, que seria o instrumento natural para levantar o pente, discordou de si mesma entre os dois sentidos: uma varredura de 300 a 6000 Hz deu relação sinal-ruído positiva em 76 dos 76 intervalos no sentido A→B e negativa em 74 dos 76 no sentido B→A, na mesma sala e com os mesmos transdutores, minutos depois. Medir uma frequência enviando aquela frequência, com a mediana de três repetições, deu margens saudáveis nos dois sentidos. A varredura é boa para achar a forma do pente e ruim para afirmar que um tom está morto, e os tons do sistema foram conferidos um a um.

O período de símbolo recebido foi medido em 479,99 amostras onde o nominal é 480, com os quatro valores individuais entre 479,899 e 480,070, o que corresponde a uma deriva entre os dois relógios da ordem de uma parte em vinte mil e a um símbolo inteiro de erro acumulado ao longo de um quadro de 192 bytes. A cauda de reverberação não foi mensurável nesta sala, pois o sinal para no piso de ruído depois que a fonte cala, de modo que a guarda de 35% do símbolo protege contra uma cauda que esta bancada não tem, e permanece por antecipação.

### 4.2 Nível de operação e saturação

<!-- Fonte: resultados/08-MARY-GAIN-A2B (caixa 1,00), 08B-MARY-GAIN-A2B (0,45), 16-SPK-A2B (0,45),
17-SPK-LEVEL-A2B (0,20 e 0,10). Sentido A->B, 16-FSK, repeticao 1, 48 bytes, 3 gravacoes por ponto. -->

O sentido A→B decodificava muito pior que o inverso, e a causa não estava na modulação. Com o ganho digital fixo em 0,5 e três gravações por ponto, baixando apenas o volume do alto-falante de A no sistema operacional, o acerto de bits foi de 79,9% com o alto-falante em 1,00, 83,2% em 0,45, 86,1% em 0,20 e 80,0% em 0,10, e os blocos íntegros foram 0, 0, 2 e 1 de 3. A curva é um U invertido com joelho em 0,20: acima dele a cadeia comprime, abaixo dele falta sinal. A Figura 4 mostra os quatro pontos.

O sinal de que a cadeia ainda comprime não é o pico recebido, e sim o ganho digital andar para trás. Com o alto-falante em 0,45, o ganho digital 1,0 leu 79,1% dos bits e nenhum bloco de três, enquanto o ganho 0,25 leu 86,0% e dois de três, com picos recebidos de apenas 0,10 a 0,38, muito abaixo de qualquer ceifamento no receptor. Com o alto-falante em 0,20 essa inversão desaparece, 86,5% em ganho 1,0 contra 86,1% em 0,5, que é o comportamento de uma cadeia linear. Corrigir o fader analógico levou o sentido A→B de nenhum bloco íntegro em doze gravações para cinco em nove, sem nenhuma alteração no processamento de sinal.

<!-- FIGURA 4, aqui: acerto de bits e blocos inteiros contra o volume do alto-falante de A, ganho digital
fixo em 0,5, tres gravacoes por ponto. Legenda ABAIXO, dizendo o sentido A->B e que os quatro pontos vem de
quatro pastas de campanha diferentes, medidas no mesmo dia. -->

### 4.3 As quatro formas de transmissão

<!-- Fonte: resultados/04-FSK-BASE, 05-MFSK-VOTE, 06-MFSK-PAR, 07-MARY-BASE, 08-MARY-GAIN, 14-FEC-REP. -->

A Tabela 4 põe as quatro formas lado a lado, no sentido B→A. Elas não foram medidas sobre uma cadeia congelada, pois entraram na ordem em que o enlace as exigiu e o alto-falante da máquina B foi trocado entre a segunda e a terceira, de modo que a coluna de resultado é o que cada forma entregou quando foi a candidata, e não um torneio simultâneo. A leitura que a tabela sustenta é ordinal, e é forte o bastante: a 2-FSK falha por um motivo diferente das demais e a 16-FSK é a única que entrega o bloco de forma repetível.

Tabela 4 - As quatro formas de transmissão no sentido B→A, com o que cada uma entregou quando foi a candidata. As linhas não compartilham a mesma cadeia analógica, e a condição de cada uma está na última coluna.

| forma | bits por símbolo | taxa de símbolo | resultado medido | condição |
|---|---|---|---|---|
| 2-FSK | 1 | 1200 bauds | 2,8% dos bytes certos em 3 gravações, preâmbulo nunca localizado | sem bloco codificado, por definição da camada |
| 5×2-FSK votada | 1, por voto de cinco pares | 100 bauds | 1 bloco íntegro de 3 | alto-falante antigo, distorção audível |
| 5×2-FSK multicanal | 5 | 100 bauds | nenhum bloco íntegro de 6 | cadeia saturada, dois ganhos digitais |
| 16-FSK | 4 | 100 bauds | 3 blocos íntegros de 3, e 11 de 12 na varredura de ganho | cadeia linear |

A 2-FSK não falha por falta de sinal. Com rms recebido de 0,07 a 0,08 e pico de 0,64 a 0,69, cerca de 40 dB acima do piso medido meia hora antes, o receptor entregou de 45 a 56 bytes para uma carga de 48 e acertou um ou dois deles, e o preâmbulo não foi localizado em nenhuma das seis leituras. É o retrato do modo de falha do enquadramento 8N1 sobre este canal: o detector de bit de partida encontra borda de descida em toda parte e produz uma quantidade plausível de bytes, todos errados. Baixar o limiar de silenciamento dez vezes levou o acerto de 2,8% para 4,9%, que é a diferença entre nada e nada.

As duas formas de cinco pares falham por potência, e não por decisão. O pico que o alto-falante aceita é fixo, então cinco tons simultâneos recebem um quinto dele cada um. A 16-FSK, com um tom por vez, chegou com rms de 0,027 a 0,031 na mesma bancada em que os cinco pares em paralelo chegavam a 0,051 a 0,065 com o dobro do ganho digital, e é a única das quatro que entregou blocos íntegros de forma repetível. A mesma aritmética aparece dentro da própria 16-FSK quando se troca o tom único por um acorde de três tons por nibble: o rms recebido cai de 0,034 a 0,039 para 0,022 a 0,024, cerca de 4,3 dB, que é dividir a amplitude por três, e os blocos íntegros caem de 3 de 3 para 2 de 3.

### 4.4 Redundância

<!-- Fonte: resultados/14-FEC-REP. B->A, 16-FSK, ganho 1.0, 48 bytes, quatro gravacoes por ponto. -->

Sobre a cadeia corrigida, com quatro gravações por ponto e um único eixo variado, a repetição $r$ de 1, 2 e 4 entregou os quatro blocos íntegros em todos os três pontos, a 11,3, 6,7 e 3,7 bytes por segundo, com 92,2%, 91,9% e 84,9% dos bits certos. A redundância extra não comprou nada aqui, e o enlace deve operar em $r = 1$, gastando o ar economizado em mais blocos. Sobre a cadeia saturada, antes da correção do fader, a mesma varredura dava nenhum bloco de seis em $r = 1$ e cinco de seis em $r = 2$, e a leitura de que a taxa 1/3 sozinha é fraca descrevia aquela cadeia e não o código.

O que a redundância ainda compra é a cauda e não a média. Uma das gravações em $r = 4$ leu 63,2% dos bits, mais de um terço errados, e ainda assim entregou o bloco inteiro, enquanto nenhuma gravação em $r = 1$ chegou perto dessa taxa de erro. A repetição alta é o ajuste para uma sala ruim, e não para o uso corrente.

### 4.5 Recuperação do relógio de símbolo

<!-- Fonte: resultados/12-13-SYNC. B->A, 16-FSK, repeticao 2, bloco de 192 bytes, 4 gravacoes,
`syncsweep on` nas duas pontas. As duas colunas saem do MESMO audio: comparacao pareada. -->

O bloco de 192 bytes, cerca de 24 segundos de ar, é onde a deriva entre os relógios se acumula o bastante para aparecer. Com as varreduras de sincronismo ligadas nas duas pontas, a mesma gravação foi decodificada pelos dois caminhos, o que torna a comparação pareada e sem sala nem momento diferentes entre as colunas. O gate antecipado/atrasado leu 95,31% dos bits e o par de varreduras leu 95,68%, e os quatro blocos chegaram inteiros pelos dois caminhos. As varreduras leram mais bits em três das quatro gravações e empataram na quarta, e o período que mediram ficou entre 479,899 e 480,070 amostras.

O ganho médio é pequeno porque este quadro não colapsou. O que as varreduras compram é o caso em que o gate perde o passo, pois elas dão o início do quadro como índice absoluto e o período como uma medida, em vez de uma correção acumulada símbolo a símbolo, ao custo de 160 ms em um quadro de 24 segundos. Elas ainda não foram levadas ao caminho de transferência de arquivo, que roda com o gate.

### 4.6 Transferência de um arquivo inteiro

<!-- Fonte: resultados/15-PKT-ARQ. B->A, 16-FSK, repeticao 1, ganho 1.0, syncsweep off. -->

Um arquivo de imagem de 1334 bytes atravessou o enlace em 21 pacotes de 64 bytes de carga, em 197 segundos, a 6,8 bytes por segundo, sem uma única retransmissão, e chegou idêntico ao original pela verificação de redundância cíclica e por comparação byte a byte. Com carga de 128 bytes foram 11 pacotes em 186 segundos, a 7,2 bytes por segundo, com três retransmissões. O pacote maior amortiza os 120 símbolos de preâmbulo que cada pacote paga, mas também falha mais, e as duas coisas quase se cancelam em 6% de ganho líquido; num canal um pouco pior a conta se inverte, porque uma retransmissão custa o pacote inteiro.

O mesmo ensaio, com o mesmo arquivo e o mesmo tamanho de pacote, entregava um pacote de 21 antes da correção da cadeia analógica, e nada mudou na segmentação nem no reenvio. Um protocolo que retenta até desistir precisa de uma probabilidade de sucesso por pacote que faça a retentativa convergir, e uma cadeia saturada não tem essa probabilidade para nenhum número de retentativas. Vinte e uma entregas em vinte e uma sem reenvio é um resultado forte e não mede com precisão a taxa de falha por pacote, que exigiria muito mais transferências.

### 4.7 O que não ajudou

<!-- Fonte: resultados/09-MARY-GAP, 10-MARY-BAND, 11-MARY-CHORD, 08-MARY-GAIN-A2B, INVESTIGACAO-A2B.md. -->

Três recursos foram medidos e descartados. O silêncio entre símbolos piora os bits em vez de melhorá-los, com 99,61%, 97,99% e 88,12% de acerto para intervalos de 0, 15% e 30% do símbolo, e nove blocos íntegros de nove nos três pontos, de modo que ele gasta até 30% do tempo de ar sem comprar nada. A largura da janela de integração por tom não mudou nada mensurável, com 99,84%, 99,87% e 99,94% para 0, 20 e 40 Hz. O acorde de três tons por nibble custa 4,3 dB de nível recebido, pela mesma divisão de potência que separa a 16-FSK das formas de cinco pares.

Um tom piloto por frequência, que aprenderia o ganho do canal em cada tom para dividir por ele, foi avaliado contra o divisor perfeito calculado do payload conhecido, e não se sustenta: dividir pelo ganho por tom leu 81,7% dos bits e um bloco de doze, contra 87,6% e quatro de doze ao dividir pelo *ruído* por tom, que é o que o receptor já estima sozinho sem piloto algum. A decisão sobre a presença de um tom quer a energia dele sobre o ruído naquela frequência, e não sobre o sinal.

Fica em aberto o estimador de piso na cadeia distorcida. A regra que o receptor usa hoje exclui o tom vencedor da atualização do próprio piso, o que é correto enquanto a maioria dos símbolos está certa e vira realimentação positiva quando não está. Uma correção que remove essa exclusão e limita o que um símbolo pode contribuir levou o sentido A→B de 79,1% para 90,2% dos bits e de nenhum bloco em doze para nove em doze sobre 27 gravações, e piorou nas gravações mais lineares da campanha. Ela está medida sobre gravações e ainda não no ar, e por isso não é o ajuste corrente.

## 5 CONSIDERAÇÕES FINAIS

<!-- Redigida 2026-09-07. Tres paragrafos, no passado, sem numero novo. -->

Apresentamos a transmissão de dados por som audível entre dois computadores comuns, começando pelo que o meio faz com o sinal e construindo sobre ele duas camadas. Na camada física comparamos quatro modulações de ordem M no mesmo enlace, da 2-FSK herdada da telefonia à 16-FSK com um tom por vez entre dezesseis, e a razão de cada passo foi a mesma: retirar da amplitude a decisão do receptor e devolver potência a cada tom. Na camada de enlace usamos correção antecipada de erros com decodificação de decisão suave, sincronismo de bloco por correlação e, acima dele, pacotes com verificação cíclica e retransmissão automática, com a aplicação enxergando uma porta serial.

O conjunto entregou blocos íntegros de forma repetível e transferiu um arquivo inteiro pelo ar, byte a byte idêntico, a uma taxa da ordem de um teclado lento e com o alto-falante e o microfone que a máquina já tem. O achado que mais pesou não foi de processamento de sinal: em ambos os sentidos, corrigir a linearidade da cadeia analógica valeu mais que qualquer alteração de código medida aqui, e um enlace que aparentava exigir redundância pesada passou a dispensá-la depois da correção. Uma inversão do ganho digital, em que reduzir o nível transmitido melhora a recepção, é o sinal barato de que a cadeia ainda comprime, e custa poucas gravações para ser lido.

Ficam três frentes. As varreduras de sincronismo ainda não foram levadas ao caminho de transferência de arquivo. O estimador de piso por tom tem uma correção medida sobre gravações e ainda não confirmada no ar, com sinal de que ela depende do regime de nível. E o ultrassom, atraente por ser uma banda silenciosa, ficou fora do escopo por limitação dos transdutores desta bancada, e não por argumento contrário à ideia.

## AGRADECIMENTOS

<!-- Obrigatoria pelo modelo. Preencher: instituicoes ou programas que deram suporte ao trabalho. -->

## FINANCIAMENTO

<!-- Obrigatoria pelo modelo. Se nao houver, o proprio modelo sugere a frase: "Esta pesquisa nao recebeu
financiamento externo especifico para o seu desenvolvimento". -->

## DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA

<!--
Obrigatoria (Portaria CNPq 2.664/2026). Manter atualizada: ferramenta usada e nao declarada e omissao;
declarada e nao usada e inverdade. Neste trabalho a IAG foi usada alem da revisao de texto (concepcao,
implementacao e analise), entao os dois modelos de frase do template NAO servem como estao: ambos
declaram uso restrito a levantamento de literatura e revisao linguistica. Redigir uma declaracao que diga
o uso real e a responsabilidade integral dos autores pelo conteudo final.
-->

## CONFLITO DE INTERESSES

Os autores declaram não haver conflito de interesses no desenvolvimento e na publicação deste trabalho.

## REFERÊNCIAS

<!--
ABNT autor-data, ordem alfabetica, uma referencia por linha. Nenhuma foi inventada; os marcadores
"(CITAR: ...)" no corpo dizem que aglomerado entra em cada ponto. Grupos necessarios:
- comunicacao acustica entre dispositivos, transferencia de dados por audio (1, P1)
- Bell 202, modems telefonicos, discriminador de frequencia (1, P2)
- canal acustico em ambiente fechado, resposta impulsiva de sala, resposta em pente (1 P3; 2.3)
- OFDM acustico, chirp acustico, MFSK acustico, estimativa de canal (1, P4)
- modulacao M-FSK, deteccao nao coerente, diversidade em frequencia (2.2)
- reverberacao, tempo de reverberacao, interferencia entre simbolos (2.3)
- CRC, ARQ, pare-e-espere, HDLC (2.4)
- codigos convolucionais, Viterbi, decisao suave, entrelacamento, codigos de repeticao (2.4)
-->
