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

ESTADO DO TEXTO: resumo aprovado 2026-09-05. Secoes 1 e 2 redigidas 2026-09-06, secao 3 em 2026-09-07,
  secao 4 em 2026-09-07, todas por revisar. Secao 5 e esqueleto. NENHUMA figura ou tabela existe ainda:
  Tabelas 1 a 5 e Figuras 1 a 5 estao marcadas em comentario no ponto onde entram. As figuras de campanha
  (espectros, resposta em pente) estao na maquina A e nao foram versionadas.
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

Este artigo apresenta a transmissão de dados por som audível entre dois computadores, com alto-falante e microfone comuns, expondo o enlace à aplicação como uma porta serial. O meio acústico impõe condições severas: a banda audível comporta poucas unidades de informação por segundo, aqui chamadas de símbolos, a amplitude que chega não é a que saiu, frequências vizinhas chegam com dezenas de decibéis de diferença, o eco de um símbolo invade o seguinte, o ruído e a fala ocupam a mesma banda, e o hardware também pode saturar e distorcer o sinal. Tratamos essas dificuldades em duas camadas. Na física, conferimos quatro modulações de ordem M, ditas M-árias, em que cada símbolo é um tom escolhido entre M frequências e carrega tantos bits quanto essa escolha permite: a 2-FSK binária, modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), e três por chaveamento em múltiplas frequências, do inglês *multiple frequency shift keying* (MFSK), a 5×2-FSK com o mesmo bit em cinco canais e decisão por voto, a 5×2-FSK multicanal com cinco bits em paralelo, e a 16-FSK com quatro bits por símbolo. Mesmo na melhor dessas formas, parte dos bits pode chegar com erro ou se perder, e na camada de enlace implementamos a correção antecipada de erros, do inglês *forward error correction* (FEC), o sincronismo de quadro por palavra de referência, a segmentação do arquivo em pacotes com verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), e a retransmissão automática, do inglês *automatic repeat request* (ARQ). Medimos cada recurso sobre gravações do mesmo enlace, para comparar as variantes sobre o mesmo ar. Na melhor configuração o enlace entregou cerca de 11 bytes por segundo com 12 blocos íntegros em 12, e um arquivo de 1334 bytes chegou idêntico em 21 pacotes de 21, sem reenvio.

**PALAVRAS-CHAVE:** Modem acústico. Modulação por chaveamento de frequência. Codificação convolucional. Canal acústico.

## 1 INTRODUÇÃO

<!--
Redigida 2026-09-06, condensando a introducao e a fundamentacao de 2026-09-05 em uma lauda. Quatro
paragrafos: os meios; o fio e o ar; o caso e o que exige; o que apresentamos. Numeros so na secao 2 e na 4.
-->

Levar bytes de uma máquina a outra tem vários meios, e cada um cobra a sua instalação. O cabo entrega megabytes por segundo e exige um conector livre em cada ponta. O rádio, no Wi-Fi ou no Bluetooth, exige um transceptor, um pareamento e a permissão de operar, que nem todo ambiente concede. O infravermelho exige linha de visada. O som audível não exige nenhuma das três coisas, pois o alto-falante e o microfone já vêm em qualquer computador ou telefone, e o que ele cobra é a taxa. A Tabela 1 põe os quatro meios lado a lado. (CITAR: comunicação acústica entre dispositivos, transferência de dados por áudio)

<!-- TABELA 1, aqui. Colunas: meio | hardware exigido | taxa tipica | alcance | onde cabe. Linhas: cabo,
radio, infravermelho, som audivel, esta por ultimo e julgada pela mesma regua. Legenda ACIMA da tabela. -->

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

<!-- Fonte: resultados/02-LVL-TONE e 02-LVL-TONE-A2B (tom pisado, unica frequencia medida assim),
03-CH-CHIRP-A2B (varredura), 12-13-SYNC.
CORRIGIDO 2026-09-07. O texto anterior dizia "medida tom a tom [...] a banda util vai de 550 a 3500 Hz" e
"acima de 4 kHz a SNR cai, 12 dB a 4000, 8 dB a 4500, zero a 5000, negativa acima de 6 kHz". Nada disso
tem origem em resultados/: o 02-LVL-TONE mede UMA frequencia, 1700 Hz, e os numeros de 4/4,5/5/6 kHz nao
aparecem em HEADER nenhum. A varredura A->B, repontuada em 2026-09-07 sobre a copia float32 local, mede o
contrario: 58,3 dB a 4012 Hz, 55,3 a 4462, 46,0 a 4988, e os melhores pontos de toda a varredura ficam
entre 4,1 e 4,4 kHz. O que cai com a frequencia e o NIVEL, nao a SNR, porque o piso cai mais rapido.
As duas varreduras discordam (A->B: 76 de 76 bins positivos; B->A: 74 de 76 negativos) e o proprio HEADER
do B->A explica: 4,0 s contra 6,0 s, pouca energia por Hz. Pela doutrina do projeto (medir uma frequencia
mandando aquela frequencia) nenhuma varredura decide SNR, e so o tom pisado decide, em 1700 Hz.
O argumento do ultrassom foi refundado no nivel e na regiao nao exercitada, que e o que os dados sustentam.
Numeros do pente recalculados a 50 Hz sobre a varredura A->B: degrau entre vizinhos com mediana 2,5 dB,
p90 6,5 dB, maximo 13,0 dB; excursao de 27,6 dB dentro de 550-3500 Hz; os 16 tons caem entre -5,7 e
-27,8 dB. O "13 a 18 dB" anterior valia como maximo e exagerava cinco vezes como faixa tipica. -->

Um alto-falante e um microfone de uso geral respondem bem na banda da fala e perdem eficiência nos extremos. Colocamos os tons entre 550 e 3500 Hz, e nessa faixa a resposta medida varia 28 dB entre o melhor e o pior ponto. Acima de 3500 Hz o nível fica de 12 a 20 dB abaixo dela.

Medimos a relação sinal-ruído mandando o próprio tom, e só em 1700 Hz, onde ela é de 57,3 dB no sentido B→A e 51,6 dB no sentido A→B. Acima de 4 kHz não há medida por tom pisado, e as duas varreduras de que dispomos discordam entre si nessa região, de modo que a faixa não foi exercitada. O ultrassom fica fora do escopo deste trabalho por essa razão e pela queda de nível dos transdutores, não por uma medida de ruído que o sustente. Sobra a banda audível, dividida com tudo o que soa na sala.

Dentro da banda o sinal chega ao microfone pelo caminho direto e pelas reflexões nas superfícies da sala, cada uma atrasada pelo seu percurso. Cópias atrasadas somam em fase nas frequências cujo período cabe um número inteiro de vezes na diferença de percurso e se opõem nas intermediárias, de modo que a resposta em frequência é um pente, com máximos e nulos alternados ao longo da banda. Aqui o degrau entre vizinhos a 50 Hz de resolução tem mediana de 2,5 dB e chega a 13 dB, e a posição dos nulos depende da geometria e muda quando alguém se move.

A Figura 1 mostra a resposta medida com os dezesseis tons da 16-FSK marcados sobre o pente. Os tons caem em pontos distintos dele, de 5,7 a 27,8 dB abaixo do melhor ponto da varredura, e essa excursão de 22 dB entre o tom mais forte e o mais fraco é a razão de a decisão do receptor não poder depender da amplitude absoluta de nenhum deles.

![Figura 1 - Resposta em frequência medida por varredura de 300 a 6000 Hz no sentido A→B, em bins de 50 Hz, com os dezesseis tons da 16-FSK marcados. A faixa clara é a região de 550 a 3500 Hz onde os tons foram colocados. A distância entre um máximo e o nulo vizinho é pequena diante da largura da faixa útil, e os tons caem em pontos distintos do pente.](figuras/resposta-canal.png "0.85")

As reflexões tardias prolongam o som depois que a fonte cala, e enquanto essa cauda dura a energia do símbolo anterior ainda está no microfone quando o seguinte começa. Nesta bancada a cauda não é mensurável, o sinal para no piso de ruído, mas o projeto a antecipa porque outra sala pode tê-la.

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
Redigida 2026-09-07. Fonte: resultados/12-13-SYNC (comparacao pareada), resultados/14-FEC-REP (formato de
campanha), ../CLAUDE.md (calibracao na rajada, pontuacao com alinhamento tolerante, regua unica).
Decisoes do autor, 2026-09-07: a auto-captura de uma maquina so fica FORA do artigo; o hardware e descrito
como dois notebooks e uma caixa de som de teste, sem modelo; a figura da bancada e simples, a fazer.
Cabo serial: uma mencao so, no paragrafo da carga, como auxilio do ensaio. Nunca como recurso do enlace.
-->

Uma variante julgada pela transmissão é medida junto com a sala, e a sala não se repete, pois duas execuções do mesmo código no mesmo cômodo discordam. Gravamos a máquina remota transmitindo uma carga conhecida e pontuamos a gravação depois. Um canal congelado em disco deixa comparar variantes sobre os mesmos segundos de ar, e a diferença entre duas leituras passa a ser do receptor.

A bancada é de dois notebooks numa sala comum, com uma caixa de som de teste ligada à máquina que transmite e o microfone interno da que recebe, ambas amostrando a 48 kHz. A Figura 3 mostra o arranjo e a Tabela 3 reúne os parâmetros do enlace.

<!-- FIGURA 3, aqui: bancada, desenho simples. Os dois notebooks, a caixa ligada ao que transmite, o
microfone interno do que grava, e o cabo serial tracejado, rotulado como controle. Legenda ABAIXO.
TABELA 3, antes da figura: parametros do enlace. Amostragem, taxa de simbolos por forma, tons, guarda,
comprimento de restricao, taxa do codigo, repeticao, tamanho de bloco, ganho. Legenda ACIMA. -->

O programa é escrito em Python, com o processamento de sinal separado de toda entrada e saída de áudio. O mesmo código demodula o fluxo ao vivo e a gravação, de modo que a variante pontuada em disco é a que opera no enlace.

A carga é uma sequência aleatória de comprimento fixo, gerada nas duas máquinas a partir de uma semente combinada por um cabo serial, que também sincroniza o início da transmissão. Os bytes pontuados trafegaram apenas pelo ar.

A pontuação alinha o recebido ao transmitido antes de comparar. O enlace perde bytes inteiros, e um byte perdido desloca todos os seguintes, de modo que a comparação posição a posição pontua em torno de metade um enlace quase perfeito. Reportamos a fração de bits certos no melhor deslocamento, a mesma régua em todas as condições, e os blocos recuperados inteiros como número separado.

Variantes que diferem apenas no receptor são pontuadas sobre a mesma gravação, e não por duas médias. Com a sala e o instante iguais nas duas colunas, poucas repetições bastam para distinguir uma da outra.

O nível de transmissão é calibrado sobre uma rajada de dados e não sobre um tom contínuo. A troca de tom a cada símbolo produz transientes de cerca de 2,5 vezes o pico de um tom parado, e uma cadeia calibrada por tom satura na transmissão real sem que nenhum medidor acuse. O volume analógico e o ganho digital chegam ao alto-falante por caminhos distintos, e variar um com o outro fixo separa a saturação da falta de nível.

Cada campanha varre um eixo por vez, com três a doze gravações por ponto, e guarda o áudio, a tabela de resultados e a versão do código que os produziu. Uma fração de bits certos é afirmação sobre o receptor tanto quanto sobre o canal, e o receptor mudou ao longo do trabalho.

Não variamos a distância entre a caixa e o microfone nem o cômodo, e a dependência da geometria não foi levantada. Cada número da seção Resultados experimentais diz a direção em que o enlace operou, e traz ao lado a condição degradada de propósito, quando houve.

## 4 RESULTADOS EXPERIMENTAIS

<!--
Redigida 2026-09-07. Ordem segue a da secao 2: meio, nivel da cadeia, as quatro formas, relogio de
simbolo, redundancia, arquivo, e o que ficou fora. O esqueleto trazia redundancia antes de relogio; a 2.3
introduz sincronismo primeiro, e resultado segue a ordem da teoria.
REGUA UNICA: acerto de bits pelo gate, que e a coluna `acerto_bits` de todos os `resultado.csv`.
Conferido em 2026-09-07 rodando `align.py` sobre a 08: ele reporta "gate early/late, como esta hoje 79,1%",
que e a media do `resultado.csv` da mesma pasta -- a coluna e mesmo a do gate, como o HEADER da 08 rotula.
(O docstring do `resultado.py` diz "best brute-forced slide"; e o docstring que esta errado.)
O CLAUDE.md da raiz reporta a serie de nivel A->B pela regua do `align.py` (relogio travado), cerca de 2
pontos acima, e com 3/3 no joelho onde o csv traz 2/3. Os numeros aqui sao os das pastas.
VERIFICACAO 2026-09-07: as 42 gravacoes A->B (08, 08B, 16, 17) foram repontuadas com o codigo de hoje
sobre as copias float32 locais de `captures/`, e as 42 reproduzem o publicado ate a segunda decimal, com
os mesmos blocos. O piloto da 4.g tambem foi refeito (`align.py` na 08): 81,7% e 1 de 12 contra 87,6% e
4 de 12, identico ao publicado. Os numeros B->A nao puderam ser reconferidos: o audio esta na maquina A.
Fontes, por paragrafo: 02-LVL-TONE e INVESTIGACAO-A2B.md; 07-MARY-BASE, 08-MARY-GAIN-A2B,
08B-MARY-GAIN-A2B, 16-SPK-A2B, 17-SPK-LEVEL-A2B; 04-FSK-BASE, 05-MFSK-VOTE, 06-MFSK-PAR, 07-MARY-BASE;
12-13-SYNC; 14-FEC-REP; 15-PKT-ARQ; 09-MARY-GAP, 10-MARY-BAND, 11-MARY-CHORD, 08-MARY-GAIN-A2B.
FIGURAS PENDENTES: as `figuras/` das campanhas estao na maquina A (Linux) e nao foram versionadas
(`.gitignore` ignora `figuras/` e `*.wav`), entao nao ha como gerar aqui. Figura 4 e Figura 5 abaixo estao
marcadas e sem arquivo.
-->

O tom de 1700 Hz chega ao microfone 57,3 dB acima do piso no sentido B→A, mediana de três repetições, e 51,6 dB acima dele no sentido A→B, mediana de cinco. Nenhum resultado desta seção é falta de sinal.

A cauda de reverberação não é mensurável nesta sala, pois o nível para no piso quando a fonte cala. A guarda de 35% de cada símbolo defende contra um transiente que esta bancada não tem.

O microfone comprime cerca de 3,5 dB ao longo de uma rajada no sentido A→B. É um ganho global, que multiplica os dezesseis tons igualmente e não desloca a comparação de (2).

A cadeia analógica domina todos os números que seguem. Medimos a 16-FSK duas vezes no sentido B→A, com o mesmo ganho digital de 1,0, o mesmo bloco de 48 bytes e dezoito minutos de intervalo, antes e depois de baixar o volume do alto-falante que transmite e o ganho de captura de quem grava.

A cadeia saturada entregou 1 bloco inteiro de 3, com o sinal chegando a rms 0,48, pico 1,000 e 9,65% das amostras acima de 0,99. A corrigida entregou 3 de 3, com rms 0,027 a 0,031 e pico 0,14 a 0,20.

Reduzir em 24 dB o nível recebido triplicou a entrega, o que não é resultado sobre amplitude e sim sobre linearidade. A energia que o limitador retira do sinal reaparece como produto de intermodulação dentro da mesma banda, onde o receptor não a distingue de tom transmitido.

Varrer o volume analógico com o ganho digital fixo separa a saturação da falta de nível, já que os dois chegam ao alto-falante por caminhos distintos. A Figura 4 mostra a varredura no sentido A→B, com ganho digital 0,5, repetição 1 e três gravações por ponto.

O alto-falante em 1,00 leu 79,9% dos bits e nenhum bloco de 3, em 0,45 leu 83,2% e nenhum de 3, em 0,20 leu 86,1% e 2 de 3, e em 0,10 leu 80,0% e 1 de 3. É um U invertido com joelho em 0,20, que comprime acima e fica sem sinal abaixo.

<!-- FIGURA 4, aqui: bits certos e blocos inteiros contra o volume do alto-falante, sentido A->B, ganho
digital 0,5, tres gravacoes por ponto. Barras de blocos e linha de bits, dois eixos. Legenda dentro do
alt, dizendo que o eixo e o volume ANALOGICO e que o ganho digital esta fixo. Fonte: 08, 08B, 17.
Os audios das tres campanhas estao em captures/ nesta maquina, entao esta figura e gerada aqui. -->

O sinal de que a cadeia ainda comprime é o ganho digital andar para trás. Com o alto-falante em 0,45 o ganho de 1,0 leu 79,1% dos bits e nenhum bloco de 3, contra 86,0% e 2 de 3 no ganho de 0,25, com picos recebidos entre 0,10 e 0,38, muito abaixo do que o receptor poderia ceifar.

Em 0,20 essa inversão desaparece, 86,5% em ganho 1,0 contra 86,1% em 0,5 e 82,4% em 0,25, que é o comportamento de uma cadeia linear. A correção levou o sentido A→B de nenhum bloco inteiro em doze gravações a 2 de 3, sem que uma linha do processamento mudasse.

<!-- TABELA 4, antes do paragrafo seguinte: as quatro formas. Colunas: forma | bits por simbolo | taxa
util | condicao medida | blocos inteiros. A coluna de condicao e obrigatoria, as campanhas nao sao
pareadas: a 2-FSK e a 5x2-FSK votada usaram a caixa antiga em P2, a multicanal e a 16-FSK a Bluetooth, e
so a 16-FSK tem ponto em cadeia corrigida. Legenda ACIMA. -->

As quatro formas foram medidas no mesmo sentido B→A, com 48 bytes aleatórios e três gravações cada, e a Tabela 4 as reúne com a condição de cada uma, que não é a mesma.

A 2-FSK acertou 2,8% dos bytes e não localizou o preâmbulo em nenhuma das seis leituras, com o sinal 40 dB acima do piso. O receptor entregou de 45 a 56 bytes de um payload de 48 e acertou um ou dois, porque o detector de bit de partida encontra borda de descida em toda parte e produz uma quantidade plausível de bytes, todos errados. Contagem certa, conteúdo lixo.

As duas formas de cinco pares recuperaram bloco inteiro de forma esparsa, 1 de 3 na votada e nenhum de 6 na multicanal, chegando com rms entre 0,051 e 0,080.

No mesmo ganho digital de 1,0 a 16-FSK chegou com rms 0,48 e pico 1,000, ou seja, concentrar num tom só a potência repartida em cinco levou a mesma cadeia ao limitador. É a troca de potência de 2.2, medida pelo lado do custo.

Calibrada no joelho da Figura 4, a 16-FSK entrega 3 blocos de 3. A Figura 5 mostra o espectro recebido de uma dessas gravações, com o tom transmitido e o tom decidido sobrepostos símbolo a símbolo.

<!-- FIGURA 5, aqui: espectro recebido de uma gravacao 16-FSK em cadeia linear (07-MARY-BASE, bateria 3),
com o painel do tom transmitido e o do tom decidido sobrepostos, grade de simbolo e rotulo de nibble.
Gerada por `spectro.py --fundido`. Legenda dentro do alt: o que e cada camada de cor e onde ler a
concordancia. O AUDIO ESTA NA MAQUINA A (a 07 e B->A) e nao foi versionado. Alternativa, se ele nao vier:
usar uma gravacao do joelho da 17-SPK-LEVEL-A2B, que esta aqui e e a mesma condicao da Figura 4. -->

O par de varreduras mede o período de símbolo em 479,99 ± 0,07 amostras sobre quatro gravações de 192 bytes no sentido B→A, contra 480,00 nominais. Vinte e quatro segundos de quadro não acumularam deriva mensurável entre os dois relógios.

O gate ficou a 0,1 ponto de um oráculo que recebeu o deslocamento correto, 95,31% contra 95,4% dos bits. As duas varreduras leram 95,68%, ganhando em três das quatro gravações e empatando na quarta, com 4 blocos de 4 em todas as leituras.

A varredura de abertura sozinha ficou abaixo do gate, 93,6%, pois acerta o início dentro de um oitavo de símbolo e congela ali. O valor do mecanismo está no par, que reposiciona cada janela pelo período medido de (3).

A margem de 0,37 ponto entre o gate e o par é menor que a diferença entre duas gravações vizinhas do mesmo ajuste, e quatro repetições não a resolvem. Um ensaio de sincronismo só separa métodos num canal em que algo falha, e aqui nada falhou.

<!-- TABELA 5, antes do paragrafo seguinte: repeticao 1 / 2 / 4. Colunas: repeticao | tempo de ar | taxa
util | bits certos | blocos inteiros. Valores 4,26 / 7,19 / 13,04 s; 11,3 / 6,7 / 3,7 B/s; 92,2 / 91,9 /
84,9%; 4 de 4 nos tres. Legenda ACIMA. Fonte: 14-FEC-REP. -->

A Tabela 5 varre a repetição em três pontos, com quatro gravações cada, no sentido B→A e na cadeia corrigida. Os doze blocos saíram inteiros nos três pontos, e a repetição 1 é 2,2 vezes mais rápida que a 2, de modo que a redundância não compra nada nesta bancada.

Na cadeia saturada a mesma varredura recuperava 1 bloco de 6 na repetição 1 contra 5 de 6 na 2. O que a redundância comprava ali era a saturação, não o canal.

O que ela ainda compra é a cauda e não a média. Uma gravação em repetição 4 leu 63,2% dos bits, um terço deles errados, e ainda entregou o bloco inteiro, num nível de erro que nenhuma gravação em repetição 1 ou 2 alcançou.

Transferimos um arquivo de 1334 bytes com reenvio pare-e-espere dirigido pelo receptor. Com carga de 64 bytes chegaram 21 pacotes de 21 em 197 s, 6,8 bytes por segundo, sem uma única retransmissão. Com 128 bytes chegaram 11 de 11 em 186 s, 7,2 bytes por segundo, com três retransmissões. O arquivo confere byte a byte contra o original nos dois casos.

O pacote maior amortiza os 120 símbolos de preâmbulo que cada um paga e em compensação falha mais, e as duas coisas quase se cancelam em 6% de ganho líquido.

A taxa do arquivo fica abaixo dos 11,3 bytes por segundo da camada porque paga preâmbulo por pacote, cabeçalho e verificação, e o intervalo de controle de cerca de 3 s entre um pacote e o seguinte. Nada disso é perda no ar.

Três ajustes do receptor foram medidos e não se pagam. O silêncio entre símbolos leva os bits de 99,61% a 88,12% quando cresce de zero a 30% do símbolo, com 9 blocos inteiros de 9 nos três pontos, e gasta tempo de ar para piorar a leitura.

A largura da janela de medida por tom não muda nada entre 0 e 40 Hz, de 99,84% a 99,94%. O acorde de três tons por nibble perde cerca de um ponto de bits, pelo nível que a divisão por três custa.

Um piloto por tom foi avaliado sobre as doze gravações do sentido A→B contra um divisor perfeito de ganho e leu 81,7% dos bits e 1 bloco de 12, abaixo dos 87,6% e 4 de 12 do piso de ruído que o receptor já estima sozinho.

A correção do estimador de piso melhora a cadeia distorcida e piora a linear, e não foi medida no ar. Não variamos a distância entre o alto-falante e o microfone nem o cômodo, e a dependência da geometria não foi levantada.

## 5 CONSIDERAÇÕES FINAIS

<!--
Tres paragrafos, no passado, sem numero novo, os mesmos do resumo.
1. O que se apresentou: o meio e as duas camadas construidas sobre ele, com o mecanismo de cada uma.
2. O que a estrutura fez: 11,3 B/s a 12 de 12; arquivo inteiro 21 de 21; e a observacao de que a
   linearidade da cadeia pesou mais que qualquer mudanca de codigo, nas duas direcoes. Situar de volta
   entre os meios da Tabela 1: taxa de um teclado lento, hardware de qualquer maquina, para o caso
   descrito na introducao.
3. Passo seguinte e fronteira: varreduras no caminho de arquivo (nao medido); estimador de piso a medir no
   ar; ultrassom fora do escopo por transdutor e nao por argumento.
-->

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
