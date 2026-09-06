<!--
FONTE DO TEXTO. VII SIMECA / IFPR. Artigo do modem acustico.

Montagem: ./artigo/monta.sh  (gera artigo_modem.docx e artigo_modem.pdf; aceita --verifica, --sem-figuras)
Conversor: artigo/simeca-md (submodulo). Correcao no conversor se faz la, nunca por copia.
Estilo: artigo/estilo.md. Ler antes de redigir qualquer secao.

=== O MODELO DO EVENTO MANDA NA ESTRUTURA (lido de "Modelo de artigo - VII SIMECA", 2026-09-05) ===
Secoes numeradas obrigatorias, nesta ordem: 1 INTRODUCAO, 2 FUNDAMENTACAO TEORICA, 3 METODOLOGIA,
  4 RESULTADOS E DISCUSSOES, 5 CONSIDERACOES FINAIS. Os titulos 2 e 3 podem ser trocados conforme a
  necessidade dos autores; os outros tres, nao. Subdivisoes permitidas ate o terceiro nivel (3.1, 3.1.1),
  com o nome em maiusculas sem negrito.
Secoes nao numeradas obrigatorias: AGRADECIMENTOS, FINANCIAMENTO, DECLARACAO DE USO DE INTELIGENCIA
  ARTIFICIAL GENERATIVA, CONFLITO DE INTERESSES, REFERENCIAS.
Extensao: 4 a 10 laudas. O orcamento antigo de 5 laudas era suposicao nossa, nao exigencia do evento.
Resumo 150-300 palavras em paragrafo unico; 3 a 5 palavras-chave separadas por ponto final.
Ate 6 autores, ORCID obrigatorio para todos, com o link correto.
Legenda de figura ABAIXO do elemento; legenda de tabela ACIMA. Toda figura e toda tabela citada no texto
  pelo numero. Equacao centralizada e numerada a direita entre parenteses.
Citacao ABNT autor-data, narrativa ou entre parenteses; "et al." em italico e sem ponto em "et".

=== COMO O SUMARIO APROVADO EM 2026-09-05 CAI NESSE MOLDE ===
O autor aprovou 1 Introducao, 2 O meio, 3 Camada fisica, 4 Camada de enlace, 5 Bancada e resultados,
6 Consideracoes finais. Sao seis secoes numeradas onde o modelo tem cinco. A logica e preservada inteira
por subdivisao, sem perder nenhuma decisao:
  "O meio"           -> 2.3, dentro da fundamentacao teorica. Continua respondendo "com o que se esta
                        lidando" e continua abaixo da camada fisica, agora como teoria do canal.
  "Camada fisica"    -> 3.1
  "Camada de enlace" -> 3.2
  "Bancada"          -> 3.3 (sistema e metodo de medicao; a metodologia que o modelo pede)
  "Resultados"       -> 4
  "Consideracoes"    -> 5
A fundamentacao teorica que o modelo exige nao e desvio do plano: e onde entram os conceitos de terceiros
(simbolo, baud, 8N1, camadas, M-aria, FSK, o canal acustico, codigo convolucional, Viterbi, CRC, ARQ),
que estavam espalhados pela fisica e pelo enlace e ali disputavam espaco com o que construimos.

Orcamento revisto, em palavras de prosa, para 6 laudas (~750 palavras por lauda; figura ou tabela 150-250):
  resumo 200 | introducao 550 | fundamentacao 1250 | metodologia 1100 | resultados 900 | consideracoes 200
  mais 6 a 8 figuras ou tabelas. Total ~4200 de prosa + ~1400 de elementos = ~5600 equivalentes.
Contagem: wc -w artigo/artigo_modem.md  (inclui comentarios; descontar)

Convencoes: um paragrafo = uma linha; sem travessao na prosa; equacoes $...$ e $$...\tag{N}$$;
  figura como ![](figuras/x.png "escala") seguida da linha "Figura N - legenda";
  "Tabela N - legenda" na linha antes da tabela em pipes; numeracao e conferida, nao gerada.
Processo: o autor conduz trecho a trecho. Nenhum paragrafo redigido sem pedido.
Nenhum numero entra sem origem em resultados/<pasta>. Quando houver fatos.md, ele passa a ser a ficha.
CITACOES: nenhuma referencia foi inventada. Onde o estilo pede aglomerado de citacoes ha um marcador
  "(CITAR: ...)" dizendo que tipo de fonte entra ali. Trocar por citacao real antes de submeter.

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

ESTADO DO TEXTO: resumo aprovado 2026-09-05. Secoes 1 e 2 redigidas 2026-09-05, por revisar.
  Secoes 3, 4 e 5 sao esqueleto.
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
Redigida 2026-09-05. Funil de seis paragrafos, um passo por paragrafo, aglomerado de citacoes no fim de
cada um (estilo.md, secao 1). P1 os meios; P2 a heranca telefonica; P3 o que o ar faz; P4 as ferramentas
do campo; P5 o caso e o que ele exige; P6 as contribuicoes, a cronologia e o anuncio da verificacao.
A cronologia das quatro formas e anunciada aqui em uma frase e desenvolvida em 3.1; os numeros que
motivaram cada passo ficam na 4.
-->

Levar bytes de uma máquina a outra é problema resolvido por vários meios, e cada um cobra o seu preço de instalação. O cabo, na porta serial, no barramento serial universal ou na rede Ethernet, entrega da ordem de megabytes por segundo e exige um conector livre em cada ponta e o cabo entre elas. O rádio, no Wi-Fi ou no Bluetooth, dispensa o cabo e exige um transceptor, um pareamento prévio e a permissão de operar, que nem todo ambiente concede. O infravermelho dispensa o pareamento e exige linha de visada. O som audível não exige nenhuma das três coisas, pois o alto-falante e o microfone já vêm montados em qualquer computador ou telefone, o par não precisa de cadastro nem de instalação, e o alcance é o da sala. O que ele cobra é a taxa, e a Tabela 1 põe os quatro meios lado a lado. (CITAR: comunicação acústica entre dispositivos, transferência de dados por áudio)

<!-- TABELA 1, aqui. Colunas: meio | hardware exigido | taxa tipica | alcance | onde cabe. Linhas: cabo,
radio, infravermelho, som audivel. Ultima coluna em prosa, no formato de tabela comparativa do estilo.md;
a linha do som audivel vai por ultimo e e julgada pela mesma regua. Legenda ACIMA da tabela. -->

Pôr dados num canal feito para voz é problema antigo, e a resposta clássica é a modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), em que o transmissor comuta a portadora entre duas frequências e cada uma representa um valor do bit. O padrão Bell 202 fixa esse arranjo em 1200 e 2200 Hz a 1200 símbolos por segundo, e os bytes viajam enquadrados em 8N1, um bit de partida, oito de dados e um de parada. O receptor não precisa recuperar a portadora, pois basta um discriminador que responda à frequência instantânea, e o sinal da tensão de saída dá o bit. Sobre o par de fios telefônico esse arranjo funciona há décadas, com a linha entregando as duas frequências no mesmo nível e sem eco. No ar, o canal não é um fio. (CITAR: Bell 202, modems telefônicos, discriminador de frequência)

Entre um alto-falante e um microfone o som chega por muitos caminhos, o direto e as reflexões nas paredes, no piso e na mesa, e as cópias atrasadas se somam à direta com fases que dependem da frequência, o que reforça umas faixas e cancela outras. A resposta resultante é um pente, com mais de dez decibéis entre frequências vizinhas separadas por algumas dezenas de hertz, e um tom que caia num vale chega enterrado no ruído. As reflexões mais longas prolongam cada símbolo sobre o seguinte. A amplitude que chega não é a que saiu, pois o alto-falante limita os picos e o microfone comprime, e os dois relógios de amostragem são independentes, de modo que o intervalo de símbolo recebido não é exatamente o transmitido. A banda ainda é a da fala, dividida com qualquer conversa na sala. Nada disso acontece num fio. (CITAR: canal acústico em ambiente fechado, resposta impulsiva de sala, resposta em pente)

A comunicação acústica entre dispositivos é campo ativo, e as ferramentas que ele usa contra esse canal são conhecidas. A multiplexação por divisão ortogonal de frequência, do inglês *orthogonal frequency division multiplexing* (OFDM), reparte a banda em muitas subportadoras estreitas e trata cada uma como se fosse plana, ao custo de uma estimativa de canal que informe o ganho de cada subportadora. As varreduras de frequência trocam banda por robustez de detecção e servem bem ao sincronismo. O chaveamento em múltiplas frequências decide por energia em cada tom e dispensa a fase. São as ferramentas do campo, e adotamos as mais simples delas. (CITAR: OFDM acústico, chirp acústico, MFSK acústico, estimativa de canal)

O caso que nos interessa é o de duas máquinas comuns numa sala, sem nada a instalar em nenhuma das duas, que precisam trocar poucos bytes com confiança. Ele exige três coisas ao mesmo tempo. A decisão do receptor não pode depender da amplitude, pois num pente a amplitude de cada frequência é acidente da geometria da sala e muda quando alguém se move. O erro precisa ser reparável onde cai, pois uma fração grande dos bits chega errada e pedir de novo não resolve quando quase todo bloco vem danificado. E a medição precisa de um jeito de comparar variantes sem que a sala entre na conta, pois duas execuções do mesmo código na mesma sala discordam entre si.

Apresentamos um modem acústico que atende a esse caso e o expõe à aplicação como uma porta serial. As contribuições são a caracterização do meio, medida com os próprios tons do sistema, a implementação de duas camadas sobre ele, a física com quatro formas de transmissão experimentadas no mesmo enlace e a de enlace com correção antecipada de erros e sincronismo de bloco por correlação, e o método de medição por gravação, que congela o canal e permite pontuar variantes sobre os mesmos segundos de ar. As quatro formas entraram na ordem em que o enlace as exigiu, e essa ordem é o fio deste artigo, pois partimos da 2-FSK herdada da telefonia, passamos ao chaveamento em múltiplas frequências repartindo o mesmo bit por cinco canais quando a decisão por amplitude se mostrou refém da inclinação do canal, e chegamos à 16-FSK, com um tom por vez entre dezesseis, quando ficou claro que soar vários tons ao mesmo tempo divide a potência entre eles. Verificamos o conjunto entre duas máquinas na mesma sala, com a transferência de um arquivo inteiro pelo ar.

## 2 FUNDAMENTAÇÃO TEÓRICA

<!--
Redigida 2026-09-05. Teoria de terceiros, sem numero desta bancada; numero so para fixar ordem de
grandeza que a deducao precise. Quatro subsecoes: 2.1 os conceitos de comunicacao de dados que o resto
usa; 2.2 o principio M-ario e a deteccao; 2.3 o meio (era a secao 2 do sumario aprovado); 2.4 a teoria de
correcao e reenvio. Cada uma fecha com gancho para a 3 ou para a 4.
-->

### 2.1 SÍMBOLOS, TAXA E ENQUADRAMENTO DE BYTE

Um sistema de comunicação digital transmite símbolos, e um símbolo é o menor trecho de sinal que o receptor decide inteiro. A taxa de símbolos, medida em bauds, é quantos deles cabem em um segundo, e não se confunde com a taxa de bits, pois quando o transmissor escolhe cada símbolo entre $M$ formas de onda distinguíveis, cada decisão do receptor resolve $\log_2 M$ bits. A taxa de bits é o produto das duas, conforme (1).

$$R_b = R_s \log_2 M \tag{1}$$

Nela, $R_b$ é a taxa de bits, $R_s$ é a taxa de símbolos em bauds e $M$ é o número de formas de onda do alfabeto. Num canal em que a taxa de símbolos está presa pela banda disponível e pela duração das reflexões, aumentar $M$ é o único caminho para subir $R_b$ sem encurtar o símbolo, e é por ele que as quatro formas de transmissão da seção 3.1 se sucedem.

Acima dos símbolos, os bytes precisam de fronteiras, pois um receptor que apenas acumula bits não sabe onde termina um e começa o outro. O enquadramento assíncrono 8N1 resolve isso byte a byte: a linha repousa em um nível, um bit de partida marca a borda, seguem oito bits de dados e um bit de parada devolve a linha ao repouso. Custa dez bits transmitidos para cada oito úteis e dispensa qualquer relógio comum entre as pontas, e é o enquadramento das portas seriais, razão pela qual um modem que o adote se apresenta ao sistema operacional como uma porta serial sem que a aplicação saiba que o meio é o ar. O preço está na fronteira, pois um bit de partida lido errado desloca o alinhamento de todos os bytes seguintes, de modo que um único bit corrompido não corrompe um byte e sim todo o resto da transmissão.

<!-- FIGURA CANDIDATA, nao commitada: o quadro 8N1 no tempo (repouso, bit de partida, oito de dados, bit
de parada) e, abaixo, o mesmo fluxo com o bit de partida perdido, mostrando o deslocamento se propagando
pelos bytes seguintes. Vale se sobrar espaco, porque e o argumento que justifica o bloco de tamanho fixo
em 3.2. Decisao do autor. -->

Esses dois níveis, o que leva sinal a bits e o que leva bits a bytes corretos, são camadas, e cada camada oferece um serviço ao nível de cima e ignora como o de baixo o cumpre. A camada física leva amostras a símbolos e símbolos a bits. A camada de enlace recebe bits, delimita blocos, verifica, corrige e reenvia o que não chegou, e entrega bytes corretos. Acima delas a aplicação vê a porta serial e nada mais, o que permite trocar toda a camada física sem tocar em quem a usa.

### 2.2 MODULAÇÃO M-ÁRIA POR CHAVEAMENTO NA FREQUÊNCIA

Chama-se M-ária a modulação de ordem $M$, em que cada símbolo é uma forma de onda escolhida entre $M$ alternativas. Quando as alternativas são frequências, a modulação é por chaveamento na frequência, e o caso binário, com $M$ igual a dois, é a FSK do modem telefônico. Acima de duas frequências fala-se em chaveamento em múltiplas frequências, do inglês *multiple frequency shift keying* (MFSK). A informação está em qual frequência soou, nunca em quão forte ela chegou, e é essa propriedade que interessa num canal cuja amplitude é acidente da sala. (CITAR: modulação M-FSK, detecção não coerente)

A detecção tem duas naturezas, e elas não se comportam do mesmo modo sob um canal desigual. No caso binário basta um discriminador de frequência, que produz uma tensão proporcional ao desvio da portadora e decide o bit pelo sinal dessa tensão, o que é barato e dispensa recuperação de portadora, mas amarra a decisão a um limiar, pois se o canal atenua uma das duas frequências mais do que a outra o desvio médio se desloca e todas as decisões passam a errar no mesmo sentido. Acima de duas frequências a decisão passa a ser por comparação, medindo a energia recebida em cada uma das $M$ frequências do alfabeto e elegendo a maior, e uma comparação é relativa, de modo que um ganho comum a todas as frequências não altera quem vence.

Uma decisão por comparação não fica imune ao pente, pois ela compara frequências diferentes e o pente as trata de modo diferente. A resposta clássica é a diversidade em frequência, em que o mesmo bit não é confiado a uma única frequência e sim repetido em várias, afastadas o bastante para que o canal as trate de forma independente, e o receptor combina as observações. Repetir o bit em tons simultâneos custa potência, pois o pico de amplitude que o alto-falante aceita é fixo e cada tom recebe uma fração dele. Entre observações independentes e potência por tom há uma troca, e é ela que ordena as quatro formas de transmissão desenvolvidas na seção 3.1, a 2-FSK com um tom entre dois, a 5×2-FSK votada e a 5×2-FSK multicanal com cinco canais binários simultâneos, e a 16-FSK com um tom entre dezesseis. (CITAR: diversidade em frequência, combinação de diversidade)

### 2.3 O MEIO ACÚSTICO

Um alto-falante e um microfone de uso geral respondem bem na banda da fala e da música e perdem eficiência nos extremos, de modo que a faixa útil para dados começa acima de algumas centenas de hertz, onde o alto-falante ainda move ar com eficiência, e termina poucos quilohertz adiante, onde a resposta cai e o ruído a alcança. O ultrassom seria atraente, pois a sala é silenciosa acima da audição e nenhuma conversa ocupa aquela faixa, e o que impede não é o argumento e sim o transdutor, que não chega lá com nível utilizável. Sobra a banda audível, dividida com tudo o que soa no ambiente.

O sinal que chega ao microfone é a soma do caminho direto com as reflexões nas superfícies da sala, cada uma atrasada pelo seu percurso. Duas cópias atrasadas somam em fase nas frequências cujo período cabe um número inteiro de vezes na diferença de percurso, e se opõem nas frequências intermediárias, de modo que a resposta em frequência entre os dois transdutores não é uma curva suave e sim um pente, com máximos e nulos alternados ao longo da banda. A posição dos nulos depende da geometria e muda quando alguém se move. Uma frequência escolhida por qualquer critério pode cair num nulo, e nesse caso o tom transmitido chega mais fraco do que o ruído no mesmo ponto do espectro, o que faz um detector por comparação de energia responder ao acaso naquela frequência. A Figura 1 mostra o mecanismo.

<!-- FIGURA 1, aqui. Esquema em dois paineis, sintetico e sem nenhum numero medido: (a) alto-falante,
microfone, o caminho direto e duas reflexoes de percursos diferentes; (b) o modulo da resposta em
frequencia resultante da soma, o pente, com um tom marcado sobre um maximo e outro sobre um nulo.
E figura de mecanismo. A resposta MEDIDA desta bancada e outra figura, na secao 4, e a legenda das duas
tem de deixar claro qual e qual. Legenda ABAIXO do elemento; dizer o que se ve, que e sintetica, e o que
notar (a distancia em frequencia entre um maximo e o nulo vizinho e pequena diante da banda util). -->

As reflexões tardias prolongam o som depois que a fonte cala, e essa cauda é a reverberação. Enquanto ela dura, a energia do símbolo anterior ainda está no microfone quando o seguinte começa, e o detector mede a soma dos dois, que é a interferência entre símbolos. O efeito não pesa igual sobre todas as formas de transmissão, pois quando o símbolo anterior usa um tom que o atual não usa, a cauda do anterior compete diretamente com o atual na comparação de energia, ao passo que quando todos os tons decaem juntos a comparação se preserva. A defesa direta é o intervalo de guarda, um trecho inicial de cada símbolo que o receptor descarta em vez de medir, e ele custa taxa em proporção ao que descarta. Quanto de cauda cada sala impõe é grandeza a medir, e a seção 4 traz a desta bancada. (CITAR: reverberação, tempo de reverberação, interferência entre símbolos)

Nem o alto-falante nem o microfone são lineares em toda a excursão. O alto-falante limita os picos, por proteção do amplificador ou por saturação do próprio transdutor, e o microfone comprime quando o nível cresce, de modo que a amplitude que chega deixa de ser proporcional à que saiu assim que a cadeia entra nessa região. A energia que a limitação retira do sinal não desaparece, ela reaparece como harmônicos e como produtos de intermodulação, que caem sobre outras frequências da mesma banda e ali são indistinguíveis de sinal transmitido. O sintoma é contraintuitivo, pois a partir desse ponto aumentar o ganho de transmissão passa a piorar a recepção, e é uma inversão que a seção 4 mede nas duas direções do enlace.

As duas máquinas amostram com osciladores próprios, e nenhuma diferença de fabricação entre eles é nula. Se o transmissor produz símbolos com uma duração e o receptor conta amostras supondo outra, a janela de medida escorrega um pouco a cada símbolo e, depois de alguns milhares deles, passa a medir o símbolo errado. Um enlace acústico precisa portanto recuperar o relógio de símbolo do próprio sinal recebido, e não apenas localizar o início da transmissão.

### 2.4 CORREÇÃO DE ERROS, DELIMITAÇÃO DE BLOCO E RETRANSMISSÃO

Um canal que erra bits obriga a escolher entre detectar e corrigir. A verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), acrescenta ao bloco o resto de uma divisão polinomial que quase nunca coincide por acaso, e com ela o receptor sabe se o bloco chegou íntegro, mas não sabe onde está o dano nem como desfazê-lo. A retransmissão automática, do inglês *automatic repeat request* (ARQ), completa a detecção pedindo de novo o que falhou, e ela converge enquanto a probabilidade de um bloco chegar inteiro não for pequena demais, pois o número esperado de tentativas é o inverso dessa probabilidade. Quando a fração de bits errados é alta o bastante para que quase todo bloco falhe, pedir de novo não termina em nenhum número de tentativas. (CITAR: CRC, ARQ, pare-e-espere, HDLC)

A correção antecipada de erros, do inglês *forward error correction* (FEC), age antes do dano, pois o transmissor envia mais bits do que os da mensagem, escolhidos de modo que ela continue recuperável a partir de uma versão danificada, e o receptor repara sem pedir nada. Num código convolucional essa redundância é gerada por uma máquina de estados, em que cada bit de entrada produz vários bits de saída a partir dele e dos $K-1$ anteriores, de modo que cada bit da mensagem influencia um trecho inteiro do fluxo transmitido, e o comprimento de restrição $K$ mede esse alcance. A decodificação é a busca do caminho mais provável nessa máquina de estados, feita pelo algoritmo de Viterbi, que percorre a treliça de estados guardando em cada um apenas o melhor caminho que chega até ele. (CITAR: códigos convolucionais, Viterbi)

O decodificador pode ser alimentado de duas formas, e a diferença entre elas é grande. Na decisão abrupta o demodulador entrega apenas o bit que julgou, e descarta o quanto julgou. Na decisão suave ele entrega, para cada bit, a razão de verossimilhança logarítmica, do inglês *log-likelihood ratio* (LLR), um número cujo sinal é o bit e cujo módulo é a confiança, de modo que o Viterbi pondera cada trecho pela evidência que o sustenta e um bit lido com pouca margem deixa de arrastar o caminho inteiro. É a interface natural entre as duas camadas, pois o demodulador já calcula essa margem para poder decidir, e entregá-la em vez de descartá-la não custa processamento nem banda. (CITAR: decisão suave, ganho de codificação)

Duas construções acompanham o código. O entrelaçamento embaralha a ordem dos bits antes de transmitir e a desfaz na recepção, de modo que uma rajada de erros contígua no ar chega ao decodificador como erros esparsos, que é a situação para a qual o código foi projetado. A repetição envia cada bit codificado mais de uma vez, e o que ela compra depende inteiramente de onde as cópias caem, pois cópias que trafeguem na mesma frequência de um pente compartilham o mesmo nulo e falham juntas. (CITAR: entrelaçamento, códigos de repetição)

Falta ao bloco saber onde ele começa. Um bloco de comprimento fixo não traz bit de partida em cada byte e por isso não desliza como o 8N1 desliza, o que é a sua vantagem, e em troca ele precisa ser localizado inteiro. A solução é abrir o bloco com uma palavra de referência conhecida pelas duas pontas e procurá-la por correlação sobre o fluxo recebido, deslizando a palavra conhecida posição a posição e tomando aquela de maior coincidência, o que continua funcionando com parte da palavra corrompida. Contar símbolos desde o início da transmissão não serve, pois qualquer recuperação de relógio consome números diferentes de amostras por símbolo enquanto ajusta, e o erro acumulado desloca o bloco.

## 3 O MODEM ACÚSTICO E O MÉTODO DE MEDIÇÃO

<!--
Titulo 3 renomeado a partir de METODOLOGIA, que o modelo permite. Aqui entra o que construimos e como
medimos: 3.1 era "3 Camada fisica" do sumario aprovado, 3.2 era "4 Camada de enlace", 3.3 e a parte de
sistema e metodo que abria "5 Bancada e resultados". Os numeros medidos ficam todos na 4.
-->

### 3.1 CAMADA FÍSICA

<!--
O que se construiu sobre o meio para transformar bits em som e som em simbolos. Fronteira: entrega
simbolos e a verossimilhanca de cada bit, e nao sabe o que os bits significam. Mecanismo em palavras antes
de qualquer equacao. Sem adiantar os numeros da 4. Ordem cronologica, cada forma nascendo do limite da
anterior, que e o fio anunciado na introducao.
- 2-FSK: tons do padrao Bell 202, 1200/2200 Hz, 1200 baud, bytes em 8N1; discriminador de atraso e
  multiplicacao (equacao candidata D = fs/(4 f_c)), bit pelo sinal; squelch quadratico. Limite que empurra
  para a seguinte: qualquer inclinacao do canal enviesa toda decisao no mesmo sentido.
- 5x2-FSK votada, 100 baud: cinco pares de tons a 200 Hz, mesmo bit em todos, um voto por par, maioria
  decide; o ganho cancela. Limiar de presenca, porque um voto e uma razao e ruido puro elege um bit.
  Conjuntos de tons escolhidos contra harmonicos cruzados. Limite: doze vezes mais lenta.
- 5x2-FSK multicanal: os mesmos cinco pares, um bit distinto em cada, cinco bits por simbolo; palavra de
  sincronismo lida por voto entre os pares; repeticao espalhada por pares diferentes; polaridade alternada
  ao longo da banda para que os dois simbolos tenham a mesma frequencia media. Limite: o acorde divide a
  amplitude por cinco.
- 16-FSK: um tom por vez entre dezesseis, quatro bits por simbolo, Gray entre vizinhos; cada tom dividido
  pelo seu piso corrente (silencioso 15 simbolos em 16, entao o piso e mesmo o ruido). Guarda de 35%.
  Existe por potencia. Equacao candidata: pontuacao do tom k = E_k / piso_k, decisao argmax.
- Preambulo alternado e cauda ociosa, e por que nenhum dos dois e opcional.
- Relogio de simbolo: gate early/late guiado pelo contraste da decisao; e as duas varreduras de 80 ms que
  bracketam o quadro, dando o inicio como indice absoluto e o periodo medido entre elas. Ordenar os picos
  por posicao, nao por altura. Equacao candidata: periodo = (n2 - n1) / simbolos do quadro.
- O que a fisica entrega para cima: no caminho sem codigo, o bit; no codificado, a LLR, quatro por simbolo
  na 16-FSK.
FIGURA CANDIDATA (a que o autor pediu, "os espectros de cada metodo"): quatro paineis de espectro,
  sinteticos, um por forma de transmissao, mostrando dois tons, cinco pares com o mesmo bit, cinco pares
  com bits distintos, e dezesseis tons com apenas um soando. E figura de METODO e nao de resultado, e a
  legenda tem de dize-lo, para nao ser lida como medicao.
FIGURA CANDIDATA: diagrama de blocos do modulador e do demodulador 16-FSK.
-->

### 3.2 CAMADA DE ENLACE

<!--
O que se construiu sobre os simbolos para entregar bytes corretos: achar o bloco, reparar, conferir,
reenviar. Opera em bits e verossimilhancas, nunca em amostras. Subdivisao e reenvio sao enlace, ao modo
de HDLC, nao transporte. A teoria de cada mecanismo ja esta em 2.4; aqui so a escolha e o parametro.
- Por que corrigir e nao so detectar, fechando o gancho de 2.4 sobre a fracao de bits errados medida.
- Bloco de tamanho fixo, sem 8N1 dentro.
- Palavra de referencia de 31 bits achada por correlacao sobre as LLRs; e ela que resolve o alinhamento de
  nibble da 16-FSK. NAO chamar de m-sequencia (medido 2026-09-05: nao e uma).
- Convolucional K=7, Viterbi suave, entrelacamento, repeticao r combinada entre os dois lados.
  Tabela candidata: taxa de erro tolerada por variante (abrupta 8%, suave 8%, 1/3 suave 13%, 1/3 x2 25%),
  vinda da simulacao contra erros de bit; dizer que e simulada e nao medida no ar.
- Pacote: byte de sincronismo, numero de sequencia, comprimento, CRC-16; cabecalho de 3 bytes, cauda de 2.
- Subdivisao do arquivo e reenvio pare-e-espere dirigido pelo receptor, transmissor sem estado.
- Acima: a aplicacao ve uma porta serial virtual.
Fonte: fec.py, xfer.py, recvfile.py.
-->

### 3.3 BANCADA E MÉTODO DE MEDIÇÃO

<!--
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

## 4 RESULTADOS E DISCUSSÕES

<!--
Ordem: primeiro o que o meio e (identificacao), depois a operacao das camadas, na ordem em que a 3 as
introduziu. Cada paragrafo com a celula do estilo: Figura N mostra + condicao + numero com incerteza ou
repeticao + previsto contra medido + causa + o que aquele numero passou a alimentar. Cada numero diz de
qual direcao veio (B->A ou A->B).

4.a O meio medido. Tom a tom (mediana de tres), nao por varredura: a varredura errou (1700 Hz a -27 dB na
    varredura, +50 dB no tom parado). Banda util 550-3500 Hz; acima de 4 kHz a SNR cai (12 dB a 4000, 8 a
    4500, ~0 a 5000), acima de 6 kHz e negativa. Pente com 13-18 dB entre vizinhos a 50 Hz. Sem cauda de
    reverberacao mensuravel: o sinal para no piso de ruido, o que fecha o gancho de 2.3 PELA NEGATIVA e
    precisa ser dito assim, porque o intervalo de guarda foi projetado contra uma cauda que esta bancada
    nao tem. Um voto elege um bit do silencio (485 bytes decodificados de sala vazia). Microfone comprime
    ~3,5 dB ao longo da rajada. Periodo de simbolo medido 479,96 +- 0,07 amostras onde o nominal e 480.
    resultados/02-LVL-TONE, 03-CH-CHIRP (as duas direcoes), 12-13-SYNC.
    FIGURA: resposta em frequencia medida, com os 16 tons marcados sobre o pente. Esta e a medida; a
    Figura 1 e o esquema. A legenda tem de separar as duas.

4.b Nivel e saturacao. Ganho digital MENOR ganha. A->B a ganho 0,5 fixo, alto-falante 1,00 / 0,45 / 0,20 /
    0,10: 82,3% / 85,1% / 88,0% / 82,2% de bits, blocos 0/3, 0/3, 3/3, 1/3. U invertido com joelho em
    0,20. A inversao do ganho digital em 0,45 (81,4% a 1,0 contra 89,1% a 0,25, picos recebidos so
    0,10-0,19) some em 0,20. Levou A->B de 0 de 12 a 8 de 9. resultados/17-SPK-LEVEL-A2B, 16-SPK-A2B.
    FIGURA: bits certos e blocos inteiros contra nivel do alto-falante.

4.c As quatro formas no mesmo enlace. Tabela: forma | bits por simbolo | taxa | medido no ar. 2-FSK nunca
    entregou uma mensagem; 5x2-FSK votada 1,8 B/s 4/4; 5x2-FSK multicanal 5,9 B/s 5/9; 16-FSK repeticao 2
    e ganho 0,5 9,4 B/s 9/11; 16-FSK repeticao 1 em cadeia linear 11,3 B/s 12/12. A 16-FSK recebe 0,14 rms
    onde os cinco canais simultaneos recebiam 0,07-0,09, que e a troca de 2.2 medida. resultados/04 a 08,
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
