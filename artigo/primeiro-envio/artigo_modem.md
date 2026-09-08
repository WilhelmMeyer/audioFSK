# Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele

**AUTORES:**

1. Winderson Nascimento Da Cruz | 0009-0007-0636-7160 | IFPR, Campus Jacarezinho | windersoncruz00@gmail.com
2. Jefferson Wilhelm Meyer Soares | 0000-0003-3372-9298 | IFPR, Campus Jacarezinho | jefferson.soares@ifpr.edu.br

**DOI:** https://doi.org/10.5281/zenodo.XXX

## RESUMO

Este artigo apresenta a transmissão de dados por som audível entre dois computadores, com alto-falante e microfone comuns, e o enlace exposto à aplicação como uma porta serial. O meio acústico impõe condições severas. Comporta poucas unidades de informação por segundo, aqui chamadas de símbolos, a amplitude que chega não é a que saiu, frequências vizinhas chegam com vários decibéis de diferença, o eco de um símbolo invade o seguinte, o ruído e a fala ocupam a mesma banda, e o hardware pode saturar e distorcer o sinal. Tratamos essas dificuldades em duas camadas. Na física, comparamos quatro modulações por chaveamento na frequência: a 2-FSK, do inglês *frequency shift keying* (FSK), a 5×2-FSK votada, com o mesmo bit em cinco canais e decisão por maioria, a 5×2-FSK multicanal, com cinco bits em paralelo, e a 16-FSK, com quatro bits por símbolo. Como ainda chegam bits errados, na camada de enlace implementamos correção antecipada de erros, sincronismo de quadro por palavra de referência, pacotes com verificação de redundância cíclica e retransmissão automática. Medimos cada recurso sobre gravações do mesmo enlace. Na melhor configuração o enlace entregou cerca de 11 bytes por segundo com 4 blocos íntegros em 4, e um arquivo de 1334 bytes chegou idêntico em 21 pacotes de 21, sem reenvio.

**PALAVRAS-CHAVE:** Modem acústico. Modulação por chaveamento de frequência. Codificação convolucional. Canal acústico.

## 1 INTRODUÇÃO

A modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), põe dados num canal de voz comutando a portadora entre duas frequências, uma para cada valor do bit. O padrão Bell 202 fixa essas duas frequências em 1200 e 2200 Hz, com transições a 1200 símbolos por segundo, e foi desenvolvido pela AT&T para a rede telefônica (FINNEGAN; BENSON, 2014). Um canal projetado para conduzir voz passa a conduzir bytes sem que nada no meio precise mudar.

O Bell 202 permanece em uso industrial. O protocolo de transdutor remoto endereçável em barramento, do inglês *Highway Addressable Remote Transducer* (HART), superpõe um sinal FSK de 1200 bits por segundo à malha de 4 a 20 mA que liga o transmissor de campo ao sistema de controle, sem perturbar o valor analógico que ela já carrega (WU, 2023). O instrumento antigo filtra o sinal digital e continua medindo como antes, o que permitiu instalar o protocolo sem trocar os equipamentos já em campo.

O mesmo princípio vale no ar, e Lopes e Aguiar (2001) já observavam por que quase ninguém o usa assim. A comunicação entre máquinas sempre foi mantida longe do som audível por duas boas razões, a taxa baixa diante do fio e do rádio e o incômodo do som. A contrapartida é que o canal de áudio existe em cada aparelho, o que o torna uma opção barata de transferir informação entre dispositivos próximos, sem instalar nada.

O ar, porém, não é o par de fios. O som viaja mais de 87000 vezes mais devagar que a onda eletromagnética, de modo que as reflexões se espalham por dezenas de milissegundos, e o multipercurso em ambiente fechado é a maior degradação dos esquemas acústicos publicados (PUTZ *et al.*, 2026). Na mesma revisão, de 31 estudos e mais de 11000 transmissões em aparelhos reais, os produtos comerciais entregam de 10 a 200 bits por segundo, que é a ordem de grandeza a esperar do meio.

Apresentamos um modem acústico que leva bytes de um computador a outro por som audível, com alto-falante e microfone comuns, e que se expõe à aplicação como uma porta serial. Partimos das duas frequências do Bell 202 e chegamos a dezesseis tons com correção de erros, e cada passo respondeu a um limite que medimos no ar. Verificamos o conjunto entre duas máquinas, transferindo um arquivo inteiro pelo ar. No arranjo da Figura 1, uma máquina converte os bytes em som e o emite pelo alto-falante, a outra capta pelo microfone e reconstrói os bytes.

![](figuras/bancada.png "0.95")
Figura 1 - O sistema. Os dados saem de uma máquina como som, atravessam o ar e são reconstruídos na outra a partir do que o microfone capta.

## 2 PRINCÍPIO DE FUNCIONAMENTO

### 2.1 O meio acústico

Transmitir pelo ar é converter a sequência de amostras em variação de pressão, deixá-la viajar a 343 m/s e reconvertê-la em amostras do outro lado. Entre um conversor e outro estão o amplificador, o alto-falante, o ar, as superfícies que refletem e o microfone.

O ruído do ambiente ocupa a mesma faixa de frequência, vindo do tráfego, de máquinas e da fala, em componentes contínuos e em rajada (PUTZ *et al.*, 2026). Ele também não é plano, e os resultados o medem concentrado na metade inferior dessa faixa, de modo que dois tons não disputam com o mesmo fundo.

Um alto-falante e um microfone de uso geral respondem bem na faixa da fala e perdem eficiência nos extremos. Colocamos os tons entre 700 e 3325 Hz, dentro dessa região, e mesmo ali a resposta está longe de ser plana, como os resultados mostram.

O ultrassom fica fora deste trabalho. Exigir inaudibilidade reduz a faixa disponível a menos de 4 kHz, onde o hardware de áudio é seletivo (PUTZ *et al.*, 2026), e a absorção do ar cresce com a frequência e encurta o alcance.

Dentro dessa faixa o sinal chega ao microfone pelo caminho direto e pelas reflexões nas superfícies ao redor, cada uma atrasada pelo percurso que fez. Uma cópia atrasada reforça o som direto em certas frequências e o cancela em outras, conforme a diferença de percurso, e a resposta do canal é um pente de máximos e nulos que a geometria da sala fixa (KUTTRUFF, 2016). Frequências separadas por dezenas de hertz chegam a diferir vários decibéis, e a posição dos nulos muda quando alguém se move, que é a razão de Lopes e Aguiar (2001) não confiarem em muitos níveis de amplitude no ar.

As mesmas reflexões, vistas no tempo, são a reverberação, e enquanto a cauda dura a energia de um símbolo invade o seguinte. Em ambiente fechado o espalhamento chega a dezenas de milissegundos, absorvido por intervalo de guarda (PUTZ *et al.*, 2026). Nesta bancada o som também não cessa junto com a fonte, e os resultados medem o que sobra sem isolar a origem.

A cadeia analógica também não é linear. O cone do alto-falante tem excursão limitada e o amplificador, tensão limitada, então os picos são achatados quando o nível cresce, e o microfone comprime do mesmo modo na outra ponta. A energia retirada dos picos reaparece como harmônicos e intermodulação dentro da própria faixa de trabalho, onde nenhum filtro os separa do sinal, e passado esse ponto subir o nível piora a recepção. Não é particularidade desta bancada. Putz *et al.* (2026) mediram distorção não linear na maioria dos aparelhos acima de cerca de 75% do volume máximo.

Disso decorrem duas exigências. A decisão do receptor não pode depender da amplitude absoluta de nenhum tom, e o nível de operação tem de ser encontrado por medição.

### 2.2 O sistema em duas camadas

Chamamos M-ária a modulação de ordem $M$, em que cada símbolo é um tom escolhido entre $M$ frequências e carrega $\log_2 M$ bits (PROAKIS; SALEHI, 2008), e a taxa de bits é o produto de (1).

$$R_b = R_s \log_2 M \tag{1}$$

Nela, $R_b$ é a taxa de bits, $R_s$ é a taxa de símbolos em bauds e $M$ é o número de frequências. Subir $M$ é o caminho para subir $R_b$, com a taxa de símbolos presa pela faixa disponível e pelas reflexões. Construímos quatro formas, e o que muda entre elas é quanto a decisão depende da amplitude. Elas ocupam as duas famílias que Lopes e Aguiar (2001) já haviam formulado, a de um tom por símbolo e a de $k$ tons simultâneos.

A 2-FSK usa os dois tons do padrão Bell 202, 1200 e 2200 Hz, e um bit por símbolo. A 5×2-FSK votada soa cinco pares de tons a cada símbolo, todos carregando o mesmo bit, e a maioria decide.

A 5×2-FSK multicanal usa os mesmos dez tons com um bit distinto em cada par, cinco bits por símbolo. A 16-FSK acende um tom entre dezesseis, quatro bits por símbolo.

O detector decide quais frequências estão presentes. Nas três formas de mais de dois tons ele não compara com um limiar, e sim uma frequência com outra, e a decisão fica indiferente à amplitude com que o som chegou.

Nenhuma dessas formas entrega todos os bits certos sobre este canal, e por isso o sistema tem uma segunda camada. Os dados vão em blocos de tamanho fixo, codificados por um código convolucional e decodificados pelo algoritmo de Viterbi (VITERBI, 1967), e cada bloco é localizado no fluxo por uma palavra de referência.

Acima do bloco o arquivo é partido em pacotes com soma de verificação, pedidos um a um pelo receptor e reenviados enquanto a soma não fechar, que é o arranjo pare-e-espere dos protocolos de enlace (TANENBAUM; WETHERALL, 2011).

A camada física entrega ao enlace a verossimilhança de cada bit, e não o bit, de modo que o corretor recebe também a confiança de cada decisão. Acima das duas a aplicação vê uma porta serial virtual.

## 3 CAMADA FÍSICA

A camada física converte símbolos, de um a cinco bits conforme a forma, em variação de amplitude em frequências fixadas de antemão, e faz o caminho inverso na recepção.

A 2-FSK usa os dois tons do padrão Bell 202 a 1200 símbolos por segundo, sai do modulador com fase contínua e leva cada byte em 8N1.

A detecção é por atraso e produto: um passa-faixa Butterworth de quarta ordem entre 800 e 2600 Hz limpa o sinal, multiplicado por uma cópia de si mesmo atrasada de sete amostras, um quarto de período em 1700 Hz, e um passa-baixa em 1800 Hz filtra o produto, positivo para um tom e negativo para o outro. O bit é o sinal desse produto filtrado. Um canal que atenue um tom mais que o outro desloca a média para um dos lados e enviesa todas as decisões no mesmo sentido.

A 5×2-FSK votada compara dentro de cada par, a 100 símbolos por segundo, com 200 Hz entre os dois tons, pouco o bastante para que o canal os trate quase igual. Como uma razão entre dois ruídos ainda elege um dos tons, o caminho sem correção descarta o símbolo quando a mediana das cinco razões fica abaixo de 1,3.

Alto-falante e microfone distorcem, e a distorção fabrica harmônicos dos tons transmitidos. Um harmônico que caia sobre um tom do outro acorde é energia a favor do bit errado, e os dez tons foram escolhidos para que isso não aconteça.

Nas duas formas de cinco pares o modulador divide a amplitude por cinco, e cada tom parte 14 dB abaixo do que partiria sozinho.

A 16-FSK soa um tom por vez, que recebe portanto toda a amplitude disponível. São dezesseis tons de 888 a 3325 Hz, espaçados 162 Hz, quatro bits por símbolo e os valores em código Gray. O receptor mede a energia de cada tom, divide pelo piso corrente daquela frequência e elege o maior, conforme (2).

$$\hat{s} = \arg\max_k \frac{E_k}{P_k} \tag{2}$$

Nela, $E_k$ é a energia no tom $k$ e $P_k$ é a média corrente dessa energia, com fator 0,02 e sem o tom de maior energia do símbolo. Como cada tom fica em silêncio quinze símbolos em dezesseis, essa média é o piso de ruído naquela frequência.

O relógio das três formas de 100 bauds vem de uma malha de adiantamento e atraso. A cada símbolo o receptor pontua três janelas deslocadas de um oitavo de símbolo, e corrige o instante do seguinte em um trinta e dois avos.

As primeiras 72 amostras de 480, 1,5 ms, são descartadas como guarda, e a decisão se faz sobre as 408 restantes, onde a energia do símbolo anterior já decaiu.

O preâmbulo é alternado, porque a malha trava em transições, e a transmissão fecha com uma sequência ociosa. O demodulador mantém pouco mais de um símbolo em memória, e sem ela o último byte não chega a ser decidido.

Na 16-FSK a saída é a verossimilhança logarítmica de cada bit do símbolo, do inglês *log-likelihood ratio* (LLR), dada por (3).

$$\Lambda_j = \max_{b_j(v)=1} \ln \frac{E_{g(v)}}{P_{g(v)}} - \max_{b_j(v)=0} \ln \frac{E_{g(v)}}{P_{g(v)}} \tag{3}$$

Nela, $v$ percorre os dezesseis valores de quatro bits, $b_j(v)$ é o bit $j$ de $v$, $g(v)$ é o tom que o código Gray atribui a $v$, e $E$ e $P$ são os de (2).

A camada física entrega uma sequência contínua de confianças, sem nenhuma marca de onde um byte começa. Como cada símbolo carrega quatro bits, ou meio byte, começar a leitura um símbolo antes ou depois troca as duas metades de todos os bytes. O começo certo é encontrado pela palavra de referência de 31 bits que precede o bloco codificado, correlacionada contra o sinal dos valores recebidos.

## 4 CAMADA DE ENLACE

A camada de enlace recebe da física um número por bit, a confiança com que ele chegou, e devolve os bits da mensagem.

O canal entrega uma fração dos bits errada, e quase nenhuma mensagem chega limpa. O receptor tem de corrigir esses erros com o que já recebeu.

A aplicação pode usar o modem como linha serial comum, com o enquadramento 8N1, em que cada byte viaja entre um bit de partida e um de parada. Sobre este canal ele não basta: um bit de partida corrompido desloca todos os bytes seguintes, e nada no enquadramento percebe isso.

No caminho corrigido a mensagem vai em blocos de comprimento combinado entre as duas pontas. O receptor sabe quantos bits esperar, então não precisa de marcas no fluxo para saber onde cada byte começa, e um bit trocado não desloca os seguintes. Sobre esses blocos utilizamos recursos já apresentados em outros trabalhos e de uso corrente em sistemas de transmissão de dados:

- código convolucional;
- decodificação de Viterbi com decisão suave;
- repetição do bloco;
- entrelaçamento;
- palavra de sincronismo;
- verificação de redundância cíclica;
- retransmissão automática.

A correção antecipada de erros, do inglês *forward error correction* (FEC), é um código convolucional de comprimento de restrição 7, com polinômios geradores 171, 133 e 165 em octal, três bits codificados por bit de entrada. Seis bits de cauda o fecham no estado zero, de onde o decodificador parte.

O decodificador é um Viterbi de decisão suave. Cada bit chega como uma verossimilhança logarítmica e a métrica de cada ramo da treliça é a soma em (4).

$$\mu = \sum_{j=1}^{n} (2c_j - 1) L_j \tag{4}$$

Nela, $c_j$ é o $j$-ésimo bit que o ramo emitiria, $L_j$ é a verossimilhança recebida na mesma posição e $n$ é o número de bits codificados por passo. Um bit duvidoso quase não move $\mu$, e o percurso segue os bits de que o receptor está seguro.

A redundância por repetição replica o bloco e o decodificador soma as cópias, pois observações independentes do mesmo bit se somam. Os dois lados têm de concordar nela, já que a divergência é indetectável e se lê como canal ruim.

Um entrelaçador por transposição de matriz, com profundidade 16, vem depois da repetição e não antes, para que as cópias de um bit caiam distantes no tempo.

O bloco é localizado por uma palavra de referência de 31 bits, que viaja sem codificação à frente dele, achada por correlação contra o sinal dos valores recebidos, e não por contagem de símbolos. O número de amostras que a malha consome em cada símbolo muda enquanto ela corrige, e a contagem acumula deslocamento ao longo do bloco. É a mesma correlação que resolve o alinhamento de símbolo da 16-FSK.

Acima do bloco corrigido, o arquivo vai em pacotes de doze bytes de guia, um byte de sincronismo, número de sequência, comprimento, carga de até 255 bytes e dois bytes de verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC).

O corpo e o CRC são somados a uma sequência pseudoaleatória fixa, dependente da posição e idêntica nas duas pontas, que desfaz padrões repetidos capazes de privar o relógio de transições. No caminho codificado o efeito é indireto, pois esses bytes ainda passam pelo codificador e pelo entrelaçador antes de virar som.

A retransmissão automática, do inglês *automatic repeat request* (ARQ), é dirigida pelo receptor, e só compensa porque o bloco corrigido já chega quase sempre inteiro. Ele pede um pacote, espera a resposta chegar e só então pede o seguinte, e descarta o áudio capturado antes de o pedido sair. São até quatro tentativas por pacote, o que não chega vira zeros, que preservam o deslocamento dos bytes seguintes, e um CRC de 32 bits sobre o arquivo decide se ele vale.

No caminho da porta serial virtual nada disso se aplica. Ele existe para que os programas já escritos para uma linha serial funcionem sem alteração, e ali um byte corrompido chega corrompido.

## 5 RESULTADOS EXPERIMENTAIS

Os ensaios usam duas máquinas na mesma sala, cada uma com alto-falante e microfone próprios. Um cabo serial entre elas automatiza o ensaio e não conduz dado da medida. A carga é gerada dos dois lados a partir de um valor inicial combinado por ele, e os bytes pontuados viajaram só pelo ar. As gravações das Figuras 5 a 9 usaram o bloco codificado repetido duas vezes.

A Figura 2 mostra o ruído da sala com o enlace parado, média de quatro gravações de oito segundos em janelas de 50 Hz. O piso não é plano. Concentra-se abaixo de 2 kHz e varia 27 dB sob os dezesseis tons da 16-FSK, de −67,6 a −94,8 dBFS. Comparar níveis absolutos entre tons leria essa diferença como sinal, e por isso cada tom é medido contra o próprio piso.

![](figuras/piso-ruido.png "0.95")
Figura 2 - Piso de ruído com o enlace parado, média de quatro gravações de 8 s. A faixa cinza são os extremos entre elas e as marcas no rodapé, os dezesseis tons.

A Figura 3 mostra o que o detector da 16-FSK mede enquanto a máquina transmissora emite um tom de 1700 Hz, o sexto dos dezesseis. O tom chega 47,4 dB acima das sondas que não receberam nada e 13,0 dB acima da segunda mais alta, que é a saia do próprio tom espalhada pela janela de 408 amostras. Um seno sintético analisado na mesma janela, sem transdutor e sem sala, reproduz esse alargamento, então ele é da medida e não do canal.

![](figuras/deteccao-tom.png "0.95")
Figura 3 - Nível nas dezesseis sondas com um tom de 1700 Hz transmitido, contra a sala parada e um seno sintético. O alargamento do pico é da janela de análise.

A Figura 4 mostra uma varredura de 300 a 6000 Hz gravada em seis segundos, e nela o alargamento reaparece como duas diagonais. São o segundo e o terceiro harmônico, em mediana 30,5 e 42,2 dB abaixo da fundamental, frequências que ninguém transmitiu e que dentro da faixa de trabalho são indistinguíveis de sinal.

![](figuras/varredura.png "0.95")
Figura 4 - Varredura de 300 a 6000 Hz, em janela de 4096 amostras. As diagonais são o segundo e o terceiro harmônico, e os riscos verticais são sons da sala.

Essas sombras posicionam os tons. Os dezesseis ocupam de 888 a 3325 Hz espaçados de 162 Hz, quase uma oitava e meia, então o segundo harmônico de seis deles cai a menos de 76 Hz de outro tom e o terceiro de dois deles a menos de 12 Hz. A sombra fica 30,5 dB abaixo da fundamental contra os 47,4 dB de margem do tom transmitido, e consome margem sem decidir o símbolo.

O nível ao longo da faixa também não é uniforme. Medido pela mesma varredura em passos de 74 Hz, varia 23,7 dB entre o melhor e o pior ponto, com até 9,4 dB entre pontos vizinhos.

Depois que a varredura termina o som não cessa junto. O nível cai cerca de 36 dB ao longo de meio segundo e só alcança o piso de ruído por volta de 0,8 s. É contra esse prolongamento que existe o intervalo de guarda descartado no início de cada símbolo.

A 5×2-FSK votada reparte a decisão entre cinco pares de tons. Cinco frequências soam a cada símbolo, uma por par, cada par decide pelo tom que chegou mais forte, e a maioria dos cinco dá o bit. São cem símbolos por segundo, um bit por símbolo, com os primeiros 15% de cada símbolo descartados como guarda.

A polaridade alterna ao longo da faixa. Nos pares de 700, 1540 e 2380 Hz o tom mais grave significa 0, e nos de 1120 e 1960 Hz significa 1, então os dois acordes ficam entrelaçados e com quase a mesma frequência média.

A Figura 5 mostra a energia nas dez frequências em dois símbolos da carga, e quem decide é a comparação dentro de cada par, nunca o nível absoluto. Em trinta símbolos consecutivos da mesma transmissão todos os bits saíram certos, e em vinte e dois deles ao menos um par votou contra os demais.

![](figuras/5x2fsk-espectro-dos-acordes.png "0.95")
Figura 5 - Espectro na janela de decisão de dois símbolos, um com bit 0 e outro com bit 1, nas dez frequências que o detector compara.

Cada par isolado acerta de 74,0% a 86,1% dos bits. Reunidos pela maioria chegam a 87,7%, e a decisão suave, que conserva a confiança que o voto descarta, leva a 88,1% dos 2340 bits do bloco. Com a correção de erros os 48 bytes chegaram idênticos.

A 16-FSK troca a redundância por densidade. Dezesseis frequências entre 888 e 3325 Hz se revezam, exatamente uma soando por vez, e qual delas soou nomeia quatro bits, à mesma taxa de cem símbolos por segundo. Frequências vizinhas recebem códigos que diferem em um único bit em doze dos quinze pares, porque são as que o canal confunde.

Com um tom por vez toda a potência que o alto-falante aceita vai para ele, onde cinco tons simultâneos dividem o mesmo pico. A decisão é escolher o maior entre dezesseis, cada tom contado do próprio piso corrente.

As Figuras 6 a 8 mostram trinta símbolos da carga, a decisão em um deles e o enquadramento do mesmo trecho. O tom transmitido fica 8,0 dB acima do segundo colocado, contra uma mediana de 7,9 dB ao longo do bloco. As duas máquinas não compartilham relógio, e o receptor corrige o passo em quinze amostras das 480 nominais a cada símbolo.

![](figuras/16fsk-tons.png "0.95")
Figura 6 - Trinta símbolos da carga, com o tom detectado marcado sobre cada um. Aqui o detectado é o transmitido nos trinta.

![](figuras/16fsk-decisao.png "0.95")
Figura 7 - Decisão em um símbolo. Em cima, o espectro e o piso corrente de cada tom. Embaixo, a energia contada do próprio piso, que é o que se compara.

![](figuras/16fsk-enquadramento.png "0.95")
Figura 8 - O mesmo trecho, com as fronteiras de símbolo que o receptor usou e a grade de passo nominal.

Nas três gravações válidas os 48 bytes chegaram íntegros. Antes da correção de erros o tom detectado coincidiu com o transmitido em 72,5% a 89,5% dos símbolos, e 85,2% a 94,5% dos bits chegaram certos.

Com a cadeia analógica linear o nível de transmissão deixa de influir. Variar o ganho do transmissor de 1,00 a 0,25 não alterou a recuperação, e as doze gravações leram de 96% a 98% dos bits. O mesmo corte de nível, na cadeia saturada, alterou o resultado de uma gravação íntegra em três para as três.

O transmissor mantém uma janela com os sete últimos bits da mensagem e, a cada bit que entra nela, emite três, cada um a soma módulo dois de um recorte diferente dessa janela. O que viaja pelo ar são esses três, e não os bits da mensagem. A janela desliza de um em um, então cada bit da mensagem permanece nela por sete passos e deixa marca em quinze bits emitidos, sempre misturado aos vizinhos. É um código convolucional de comprimento de restrição sete e taxa um terço, com polinômios geradores 171, 133 e 165 em octal (PROAKIS; SALEHI, 2008), padronizados para uso espacial e adotados em telefonia celular e em redes locais sem fio.

O receptor refaz o caminho do codificador para as hipóteses possíveis, compara o que cada uma teria emitido com o que chegou, soma o peso das discordâncias e descarta as hipóteses que já perderam. Ao fim fica com a de menor soma. Trocar um bit da mensagem muda quinze bits emitidos, então uma hipótese errada discorda em quinze lugares para explicar um erro em um. É o algoritmo de Viterbi (VITERBI, 1967), e o peso de cada discordância é a confiança com que o bit chegou, o que se chama decisão suave (PROAKIS; SALEHI, 2008).

A Figura 9 acompanha dois bits da mensagem até as quinze posições que dependem de cada um. O entrelaçador escreve os bits codificados em linhas de dezesseis colunas e os lê por colunas, o que separa posições consecutivas do código por 73 lugares no ar, passo fixo e conhecido das duas pontas. Uma perturbação curta atinge no máximo uma ou duas das quinze. No primeiro bit as quinze chegaram certas; no segundo, uma chegou trocada e fraca, confiança 0,31 contra 4,23 da mais forte. Os dois bits saíram corretos.

![](figuras/fec-rastro.png "0.95")
Figura 9 - Em cima, dois bits da mensagem e as quinze posições transmitidas que dependem de cada um; losango marca posição trocada. Embaixo, a confiança com que chegaram os 1170 bits e os 69 trocados, todos de confiança baixa, que é o que faz o decodificador descartar os bits trocados em preferência pelos bits corretos.

Desses 1170 bits, sessenta e nove chegaram trocados, 5,9%, e a mensagem saiu idêntica. O erro se concentra na baixa confiança. Abaixo de 0,5 quatro em cada dez estão trocados, acima de 2 é um em 763. A confiança é o peso de cada bit recebido na comparação entre hipóteses de mensagem inteira, e não a decisão de um bit isolado. Uma discordância num bit fraco pesa pouco na soma, e num bit forte pesa muito, de modo que um erro confiante do canal não altera o resultado enquanto as demais posições apontarem a mensagem certa. Em 67 dos 69 casos um dos bits emitidos no mesmo passo chegou mais confiante. Nos outros dois a mensagem também saiu correta, porque o passo é apenas parte da evidência. Cada bit da mensagem permanece na janela por sete passos e aparece em quinze posições transmitidas, e as demais continuaram apontando o mesmo valor.

Repetir o bloco codificado não mudou o resultado. Nas doze gravações, quatro por ponto, uma, duas e quatro repetições entregaram todos os blocos íntegros com o mesmo acerto de bits, e a taxa útil caiu de 11,3 para 3,7 bytes por segundo. O canal operou entre 5,9% e 9,6% de bits codificados errados, dentro dos 10% que a taxa um terço com decisão suave tolera em simulação. A repetição eleva esse limite a 19%, aplicável a uma sala mais ruidosa que esta.

A decisão suave não exige bits adicionais no ar, pois a confiança já é calculada pelo demodulador, e na mesma taxa de código leva a tolerância simulada de menos de 2% para 5%.

Acima do bloco, os dados são partidos em pacotes com número de sequência, comprimento e verificação de redundância cíclica. O receptor pede um pacote, confere, e só então pede o seguinte, repetindo o pedido enquanto a verificação falhar. Uma imagem de 1334 bytes chegou idêntica ao enviado em duas corridas, vinte e um pacotes de 64 bytes a 6,8 bytes por segundo sem nenhuma retransmissão, e onze pacotes de 128 bytes a 7,2 bytes por segundo com três. A taxa fica abaixo dos 11,3 do bloco por causa do preâmbulo de cada pacote, do cabeçalho, da verificação e do intervalo entre confirmar um pacote e pedir o próximo.

## 6 CONSIDERAÇÕES FINAIS

Construímos um modem acústico que leva bytes de um computador a outro por som audível, com alto-falante e microfone comuns, e o expusemos à aplicação como uma porta serial. A camada física entrega a confiança de cada bit e a camada de enlace corrige os que chegam trocados. Na 16-FSK, entre 5,9% e 9,6% dos bits codificados chegaram trocados, e mesmo assim todos os blocos foram decodificados sem erro. Nessa condição o enlace entregou 11,3 bytes por segundo com todos os blocos íntegros, e um arquivo de 1334 bytes chegou idêntico ao enviado.

Esses números valem para uma sala, duas máquinas e uma cadeia analógica sem saturação. Das quatro formas de transmissão construídas, duas foram medidas nessa condição, a 5×2-FSK votada e a 16-FSK. A 2-FSK e a 5×2-FSK multicanal só têm medidas anteriores à correção da cadeia, e refazê-las fica para a versão final.

## DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA

Em conformidade com a Portaria CNPq nº 2.664/2026, os autores declaram o uso de Claude-Code (Anthropic) e Codex (OpenAI) na concepção, para discussão da abordagem e levantamento de referências, na implementação e na análise, para redação e depuração do firmware e dos scripts de ensaio, e na redação do texto, para clareza e correção de linguagem. Todo o conteúdo gerado foi verificado e editado pelos autores, que assumem responsabilidade integral pelo trabalho.

## CONFLITO DE INTERESSES

Os autores declaram não haver conflito de interesses no desenvolvimento e na publicação deste trabalho.

## REFERÊNCIAS

FINNEGAN, Kenneth W.; BENSON, Bridget. Clarifying the amateur Bell 202 modem. In: **ARRL/TAPR Digital Communications Conference (DCC)**, 33., 2014. Anais [...]. [S.l.]: TAPR, 2014.

KUTTRUFF, Heinrich. **Room acoustics**. 6. ed. Boca Raton: CRC Press, 2016.

LOPES, Cristina Videira; AGUIAR, Pedro M. Q. Aerial acoustic communications. In: **IEEE Workshop on Applications of Signal Processing to Audio and Acoustics (WASPAA)**, 2001, New Paltz. Anais [...]. New Paltz: IEEE, 2001.

PROAKIS, John G.; SALEHI, Masoud. **Digital communications**. 5. ed. Nova York: McGraw-Hill, 2008.

PUTZ, Florentin; FORTMANN, Philipp; FRANK, Jan; HAUGWITZ, Christoph; KUPNIK, Mario; HOLLICK, Matthias. Evaluating acoustic data transmission schemes for ad-hoc communication between nearby smart devices. **ACM Transactions on Internet of Things**, v. 7, n. 1, art. 8, 2026. arXiv:2602.02249.

TANENBAUM, Andrew S.; WETHERALL, David J. **Computer networks**. 5. ed. Boston: Pearson, 2011.

VITERBI, Andrew J. Error bounds for convolutional codes and an asymptotically optimum decoding algorithm. **IEEE Transactions on Information Theory**, v. IT-13, n. 2, p. 260-269, abr. 1967.

WU, Joseph. **A basic guide to the HART protocol**. Dallas: Texas Instruments, nov. 2023. (Application Report SLAAEH0). Disponível em: https://www.ti.com/lit/pdf/slaaeh0.
