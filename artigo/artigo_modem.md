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
Por que uma secao propria: julgar uma ideia transmitindo mede a ideia e a sala ao mesmo tempo, e a sala nao
para. Orcamento ~350 palavras.
Hardware: as duas maquinas, placas de som, alto-falante e microfone de cada uma, taxa de amostragem 48 kHz.
Software: Python, com o processamento de sinal separado de toda entrada e saida (o mesmo codigo roda ao
  vivo e sobre gravacao), e a interface como porta serial virtual.
Cabo serial entre as maquinas: UMA frase, como auxilio do ensaio (sincronizar o inicio e combinar a carga
  conhecida gerada dos dois lados), deixando claro que os bytes pontuados viajaram so pelo ar. Nunca como
  recurso da comunicacao. Decisao do autor, 2026-09-05.
Metodo: gravacao do lado remoto transmitindo carga conhecida e pontuacao offline; um canal fixo permite
  comparar variantes sobre os mesmos segundos de ar. Pontuacao com alinhamento tolerante, porque o enlace
  derruba bytes e um byte perdido desloca o resto. Regua unica: bits no melhor deslocamento, blocos
  inteiros como numero separado. Comparacao pareada sobre a mesma gravacao. Calibrar ganho numa rajada e
  nao num tom, porque os transientes de troca de tom levam cerca de 2,5 vezes o pico de um tom parado.
  O que foi degradado de proposito e dito ao lado do numero.
Tabela candidata: parametros do enlace (fs, baud por camada, tons, K, r, tamanho de bloco, ganho, guarda),
  com a coluna de simbolos igual a do texto.
FIGURA CANDIDATA: foto ou diagrama da bancada.
-->

## 4 RESULTADOS EXPERIMENTAIS
<!--
Ordem: primeiro o que o meio e (identificacao), depois a operacao das camadas, na ordem em que a 2 as
introduziu. Cada paragrafo com a celula do estilo: Figura N mostra + condicao + numero com incerteza ou
repeticao + previsto contra medido + causa + o que aquele numero passou a alimentar. Cada numero diz de
qual direcao veio (B->A ou A->B).

4.a O meio ja esta em 2.1. Aqui so o que fecha ganchos: sem cauda de reverberacao mensuravel, a guarda de
    35% foi projetada contra uma cauda que esta bancada nao tem; o voto elege um bit do silencio (485 bytes
    decodificados de sala vazia); o microfone comprime ~3,5 dB ao longo da rajada; periodo de simbolo
    medido 479,96 +- 0,07 amostras onde o nominal e 480. resultados/02, 03, 12-13-SYNC.

4.b Nivel e saturacao. Ganho digital MENOR ganha. A->B a ganho 0,5 fixo, alto-falante 1,00 / 0,45 / 0,20 /
    0,10: 82,3% / 85,1% / 88,0% / 82,2% de bits, blocos 0/3, 0/3, 3/3, 1/3. U invertido com joelho em
    0,20. A inversao do ganho digital em 0,45 (81,4% a 1,0 contra 89,1% a 0,25, picos recebidos so
    0,10-0,19) some em 0,20. Levou A->B de 0 de 12 a 8 de 9. resultados/17-SPK-LEVEL-A2B, 16-SPK-A2B.
    FIGURA: bits certos e blocos inteiros contra nivel do alto-falante.

4.c As quatro formas no mesmo enlace. Tabela: forma | bits por simbolo | taxa | medido no ar. 2-FSK nunca
    entregou uma mensagem; 5x2-FSK votada 1,8 B/s 4/4; 5x2-FSK multicanal 5,9 B/s 5/9; 16-FSK repeticao 2
    e ganho 0,5 9,4 B/s 9/11; 16-FSK repeticao 1 em cadeia linear 11,3 B/s 12/12. A 16-FSK recebe 0,14 rms
    onde os cinco canais simultaneos recebiam 0,07-0,09, que e a troca de potencia de 2.2 medida. resultados/04 a 08,
    11, 14.

4.d Redundancia. Cadeia saturada: repeticao 1 0/6 e 1/6, repeticao 2 2/6 e 5/6, repeticao 4 4/7. Cadeia
    corrigida, 48 bytes, quatro gravacoes por ponto: repeticao 1, 2 e 4 todas 4 de 4, a 11,3 / 6,7 /
    3,7 B/s. Redundancia compra a cauda e nao a media (uma gravacao a repeticao 4 leu 64% dos bits e ainda
    entregou o bloco). resultados/14-FEC-REP.

4.e Relogio de simbolo. Oito gravacoes: gate 87,7% e 5/8; melhor deslocamento (oraculo) 89,3% e 7/8;
    varredura da frente 88,4% e 8/8; duas varreduras com periodo medido 89,0% e 8/8. O gate nao e ruim na
    media, ele colapsa (49,0% onde o relogio congelado leu 84,9%). Pareado: as varreduras leem mais bits
    em 59 de 60. Parte na auto-captura Bluetooth, canal diferente, dizer. resultados/12-13-SYNC.

4.f Arquivo inteiro. testcard.bmp, 1334 bytes, 21 de 21 pacotes de 64 bytes sem retransmissao a 6,8 B/s;
    11 de 11 a 7,2 B/s com 128 bytes (3 retransmissoes). Pacote maior amortiza o preambulo e falha mais;
    quase empata. Antes entregava 1 de 21, e nada na subdivisao ou no reenvio mudou: foi a correcao
    analogica. Zero retransmissoes em 21 e resultado forte mas nao mede a taxa de falha por pacote com
    precisao. resultados/15-PKT-ARQ.

4.g O que nao ajudou e o que ficou fora: silencio entre simbolos, banda de integracao e acorde por nibble
    (custam ou nao medem nada); piloto por tom medido e morto; a correcao do estimador de piso, boa na
    cadeia distorcida e pior na linear (0 de 3 contra 2 de 3), ainda nao no ar. Curto, cada um com o
    numero e a pasta. resultados/09, 10, 11, INVESTIGACAO-A2B.md.
-->

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
