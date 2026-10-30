# Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele

<!-- SEGUNDA VERSÃO, recomeçada em 2026-10-29 depois dos pareceres. A primeira versão, como foi enviada, e os pareceres estão em primeiro-envio/ (artigo_modem.md, PARECERES.md). O roteiro discutido entre os autores está no artefato "Roteiro do artigo acústico". Voz impessoal, a pedido do revisor 1. Contas só onde forem considerações de implementação (sincronismo, janela de análise, espalhamento espectral e harmônicos). -->

**AUTORES:**

1. Winderson Nascimento Da Cruz | 0009-0007-0636-7160 | IFPR, Campus Jacarezinho | windersoncruz00@gmail.com
2. Jefferson Wilhelm Meyer Soares | 0000-0003-3372-9298 | IFPR, Campus Jacarezinho | jefferson.soares@ifpr.edu.br

**DOI:** https://doi.org/10.5281/zenodo.XXX

## RESUMO

Apresenta-se a transmissão de dados por som audível entre dois computadores, com alto-falante e microfone de uso geral. No canal acústico a amplitude recebida difere da emitida, frequências próximas chegam com níveis distintos, o ruído do ambiente ocupa a mesma faixa e a cadeia analógica satura em nível alto e gera harmônicos. Para tratar essas condições, na camada física são comparadas quatro modulações por deslocamento de frequência, do inglês *frequency shift keying* (FSK). A 2-FSK transmite um bit por símbolo, em um de dois tons, e a 5×2-FSK votada repete esse mesmo bit em cinco pares de tons e decide pela maioria. A 5×2-FSK multicanal usa os mesmos pares para transmitir cinco bits distintos por símbolo, e a 16-FSK emite um único tom por símbolo, entre dezesseis, que carrega quatro bits. Duas varreduras de frequência nas pontas do quadro dão o início e a duração dos símbolos. Na camada de enlace, a correção antecipada de erros por código convolucional repara os bits que a camada física entrega errados, uma palavra de referência localiza o bloco, e pacotes com verificação de redundância cíclica e retransmissão automática completam a entrega. Uma negociação pelo próprio som mede o canal em cada sentido e escolhe a modulação e a taxa sem configuração prévia. Com o alto-falante afastado do microfone, a 16-FSK com correção de erros entregou 11,3 bytes por segundo, com 4 blocos íntegros de 4, e um arquivo de 1334 bytes chegou idêntico em 21 pacotes, sem retransmissão.

**PALAVRAS-CHAVE:** Modem acústico. Modulação por deslocamento de frequência. Codificação convolucional. Canal acústico.

<!-- Resumo reaproveitado da primeira versão: frase solta "O meio acústico impõe condições severas" retirada, "emitida/recebida" no lugar de "chega/saiu", voz impessoal, negociação acrescentada. Os números finais ficam sujeitos à Tabela 1 (6.2). -->

## 1 INTRODUÇÃO

Rádio e infravermelho transferem dados sem cabo entre computadores próximos com taxas elevadas, mas exigem transceptor dedicado. O som usa o alto-falante e o microfone já presentes, ao custo de taxa baixa e alcance curto (LOPES; AGUIAR, 2003).

<!-- LOPES; AGUIAR (2003) está fechada (IEEE Xplore 1228528) e ainda não foi lida. Abrir pelo Periódicos CAPES e conferir que a comparação está lá antes de manter a citação. -->

A modulação por deslocamento de frequência, do inglês *frequency shift keying* (FSK), representa cada valor de bit por uma frequência. Na rede telefônica, o padrão Bell 202, da AT&T, usa 1200 e 2200 Hz a 1200 símbolos por segundo (FINNEGAN; BENSON, 2014). O mesmo padrão segue na instrumentação industrial, onde o protocolo de transdutor remoto endereçável, do inglês *Highway Addressable Remote Transducer* (HART), superpõe FSK de 1200 bits por segundo à malha de corrente de 4 a 20 mA sem alterar o valor analógico que ela transporta (WU, 2023).

Lopes e Aguiar (2001) demonstraram a transmissão pelo ar com várias frequências audíveis. O ar, porém, não é um par de fios. O som se propaga a cerca de 343 m/s, aproximadamente 875 mil vezes mais devagar que a onda eletromagnética, e em ambiente fechado as reflexões chegam dezenas de milissegundos depois do som direto (PUTZ *et al.*, 2026).

Em uma revisão de 31 estudos, com mais de 11 mil transmissões em aparelhos reais, Putz *et al.* (2026) apontam o multipercurso como a principal degradação e situam os produtos comerciais entre 10 e 200 bits por segundo. Uma implementação aberta que transmite quatro bits por tom opera entre 8 e 16 bytes por segundo (GERGANOV, 2021).

<!-- Os 8 a 16 B/s do ggwave vêm do README, conforme referencias.md. Conferir no repositório antes de submeter. -->

Este trabalho apresenta um modem acústico que transmite bytes entre dois computadores por som audível, com alto-falante e microfone de uso geral, e que a aplicação vê como uma porta serial virtual. Descrevem-se os fenômenos do canal, as quatro modulações, a camada de enlace e a negociação do enlace pelo próprio som, com as medidas de cada recurso. A Figura 1 mostra o arranjo.

![](figuras/bancada.png "0.95")
Figura 1 - O sistema. Os dados saem de uma máquina como som, atravessam o ar e são reconstruídos na outra a partir do que o microfone capta.

## 2 O CANAL ACÚSTICO

### 2.1 Frequência e detecção

O som se propaga no ar a cerca de 343 m/s. A banda disponível para os dados é a faixa audível, porque é a que alto-falantes e microfones de uso geral reproduzem.

Cada valor de bit, ou de grupo de bits, corresponde a uma frequência combinada entre as duas pontas. A cada intervalo fixo, chamado símbolo, o transmissor emite um tom e o receptor identifica qual esteve presente. Um tom puro concentra a energia em uma única frequência, ao contrário da fala, que ocupa banda larga e varia com o locutor, e por isso os símbolos são tons.

O receptor escolhe a frequência de maior energia. Um ganho comum a todas, vindo do volume ou da distância, não altera a escolha, mas a probabilidade de erro depende da relação sinal-ruído, do inglês *signal-to-noise ratio* (SNR), em cada frequência.

Com $M$ frequências, cada símbolo carrega $\log_2 M$ bits, e $M$ é limitado pela resolução da medida. Em uma janela de $N$ amostras, duas frequências só se distinguem quando separadas de pelo menos a resolução dada por (1).

$$\Delta f = \frac{f_s}{N} \tag{1}$$

Nela, $f_s$ é a taxa de amostragem e $N$, o número de amostras da janela. No sistema implementado, $f_s$ = 48 kHz e o símbolo tem 480 amostras, das quais as primeiras 72 formam um intervalo de descarte, e a janela tem 408 amostras, com $\Delta f$ ≈ 118 Hz. Os dezesseis tons da 16-FSK, espaçados de 162,5 Hz, respeitam esse limite, e mais tons na mesma faixa seriam lidos como o vizinho.

O descarte cobre a transição do tom anterior, que alto-falante e microfone não acompanham instantaneamente, e a incerteza sobre o instante em que o símbolo começa. Descartar mais limparia a janela, mas a encurtaria e pioraria $\Delta f$.

### 2.2 Efeitos do canal

Uma sala em silêncio não produz sinal nulo no microfone. Tráfego, máquinas e fala ocupam a faixa dos dados, de forma contínua e em rajadas (PUTZ *et al.*, 2026), e o microfone acrescenta ruído e processamento próprios, que variam de uma máquina para outra. Resulta um piso de ruído permanente, com nível diferente em cada frequência.

A Figura 2 mostra esse piso no sistema implementado, medido com o enlace parado em quatro gravações de 8 s e analisado em janelas de 50 Hz. Concentrado abaixo de 2 kHz, ele varia 27 dB sob os dezesseis tons da 16-FSK, de −67,6 a −94,8 dBFS.

![](figuras/piso-ruido.png "0.95")
Figura 2 - Piso de ruído com o enlace parado, média de quatro gravações de 8 s. A faixa cinza mostra os extremos entre elas, e as marcas no rodapé, os dezesseis tons.

Um tom transmitido precisa superar esse piso na sua frequência, e não o silêncio. A SNR de cada tom é a razão entre a sua energia e a desse piso, e um mesmo nível de transmissão dá SNR diferentes a tons diferentes. Por isso cada tom é comparado com o piso da sua própria frequência, e não com um limiar único.

Entre o conversor do transmissor e o do receptor, amplificador, alto-falante, ar, superfícies que refletem ou absorvem o som e microfone alteram o tom, de modo que o sinal recebido difere do emitido mesmo sem ruído.

O som chega ao microfone pelo caminho direto e por reflexões atrasadas pelo seu percurso, que o reforçam em algumas frequências e o cancelam em outras. A resposta do canal toma a forma de um pente de máximos e mínimos fixado pela geometria (KUTTRUFF, 2016). Frequências próximas podem chegar com níveis muito diferentes, e os mínimos se deslocam quando objetos ou pessoas se movem na sala.

Vistas no tempo, as mesmas reflexões formam a reverberação. Na janela de um símbolo, o tom dos símbolos anteriores ainda soma energia à sua frequência e compete com o tom atual na decisão.

O espectro medido de um tom puro também não é uma linha única. Analisar o tom só durante a janela de $N$ amostras equivale a cortar um seno contínuo nas bordas da janela, o que espalha a energia pelas frequências próximas, efeito chamado vazamento espectral. O nível a uma distância $\delta$ do tom, relativo ao do próprio tom, é dado por (2).

$$\frac{|X(f_0+\delta)|}{|X(f_0)|} = \left|\frac{\sin(\pi \delta N / f_s)}{\pi \delta N / f_s}\right| \tag{2}$$

Nela, $f_0$ é a frequência do tom e $X$, o espectro da janela. O nível se anula nos múltiplos de $f_s/N$, e os zeros em $\pm f_s/N$ delimitam o lóbulo principal. Os lóbulos laterais decrescem com a distância, e o primeiro fica cerca de 13 dB abaixo do pico.

A Figura 3 mostra o efeito no sistema implementado, com um símbolo do tom de 1700 Hz captado pelo receptor (a) e o espectro das suas 408 amostras analisadas contra o de um seno ideal cortado na mesma janela, calculado sem passar por alto-falante, ar e microfone (b). As curvas coincidem em torno do tom, de modo que o espalhamento vem da janela, e não do canal.

![](figuras/espalhamento-janela.png "0.95")
Figura 3 - Tom de 1700 Hz recebido. (a) Um símbolo, com o intervalo de descarte e a janela analisada. (b) Espectro da janela, contra um seno ideal cortado na mesma janela. As linhas pontilhadas marcam os dezesseis tons da 16-FSK.

O tom vizinho da 16-FSK, 162 Hz acima, cai no primeiro lóbulo lateral e recebe −13,0 dB, contra −13,4 dB previstos por (2). Essa margem separa um tom do vizinho na decisão, mesmo sem ruído, e diminui se os tons forem aproximados.

O detector vê apenas a energia de cada um dos dezesseis tons na janela. A Figura 4 mostra esses valores no sistema implementado, com o tom de 1700 Hz transmitido, sobre a curva de (2) para um seno ideal no mesmo nível, somada em potência ao piso da sala em silêncio. O tom transmitido fica 47,4 dB acima do nível da mesma frequência com a sala em silêncio, que é a sua margem sobre o piso.

![](figuras/deteccao-tom.png "0.95")
Figura 4 - Energia nos dezesseis tons da 16-FSK na janela de decisão, com o tom de 1700 Hz transmitido. A curva é o previsto por (2) mais o piso de ruído, e os círculos vazados, o previsto em cada tom. Os quadrados são a sala em silêncio, mediana de quatro gravações.

Os outros quinze tons também sobem acima do silêncio, porque recebem os lóbulos laterais do tom transmitido. Até 2,5 kHz o medido difere do previsto em 0,9 dB na mediana, e em até 3,5 dB perto dos zeros da curva, onde o nível muda rápido com a frequência. Acima de 2,5 kHz o medido excede o previsto em 4,5 dB na mediana, o que o vazamento não explica, e o maior desvio, 7,1 dB em 3325 Hz, fica a 75 Hz do segundo harmônico de 1700 Hz (Figura 5).

Para ser escolhido, o tom transmitido precisa vencer ao mesmo tempo o piso de ruído, que supera por 47,4 dB, e o vazamento sobre o vizinho, que supera por 13,0 dB.

A cadeia analógica cria ainda frequências não transmitidas. Amplificador, alto-falante e microfone não são perfeitamente lineares, e a não linearidade põe energia nos múltiplos inteiros da frequência do tom, os harmônicos, que acompanham todo tom e crescem com o nível. Em nível alto, o cone do alto-falante e o amplificador atingem seus limites e achatam os picos, e Putz *et al.* (2026) mediram distorção não linear na maioria dos aparelhos acima de cerca de 75% do volume máximo.

A Figura 5 mostra o efeito no sistema implementado, com uma varredura de 300 a 6000 Hz em seis segundos, transmitida pelo ar e captada pelo receptor. O segundo e o terceiro harmônicos aparecem como diagonais, em mediana 30,5 e 42,2 dB abaixo da fundamental, respectivamente. Entre os dezesseis tons, de 888 a 3325 Hz, o segundo harmônico de seis deles cai a até 76 Hz de outro tom, e o terceiro de dois, a até 12 Hz, somando energia onde nada foi transmitido.

![](figuras/varredura.png "0.95")
Figura 5 - Varredura de 300 a 6000 Hz, em janela de 4096 amostras. As diagonais são o segundo e o terceiro harmônicos, e os riscos verticais são sons da sala.

<!-- Winderson: o caso do microfone mais antigo que entregava sinal espúrio entra aqui se houver registro (qual máquina, o que se viu). Sem registro, fica fora. Transmissão pela carcaça e pela mesa: sem medida no repositório, fora. -->

### 2.3 Limites dos transdutores

Alto-falantes e microfones de uso geral respondem bem na faixa da fala e perdem eficiência nos extremos, e por isso os tons das quatro formas ficam entre 700 e 3325 Hz. O ultrassom fica fora. Exigir inaudibilidade deixa uma faixa de menos de 4 kHz de largura, onde o hardware de áudio já é seletivo (PUTZ *et al.*, 2026), e a absorção do ar cresce com a frequência e encurta o alcance.

<!-- Caixa Bluetooth (atraso e compressão do codec) fora até haver número que o artigo use. -->

## 3 CAMADA FÍSICA

A camada física converte os bits em tons e, na recepção, o som captado de volta em bits, cada um com a confiança da decisão. A correção de erros, a localização do bloco e os pacotes ficam acima dela, na camada de enlace.

### 3.1 Formas de transmissão

A Figura 6 mostra os tons que cada forma emite para o mesmo byte, 1011 0010, no sistema implementado.

![](figuras/formas-transmissao.png "0.95")
Figura 6 - Tons emitidos por cada forma para o byte 1011 0010. As linhas claras são as frequências disponíveis em cada forma, e os traços escuros, as que soam em cada símbolo. Acima de cada símbolo estão os bits que ele carrega. Os símbolos duram 0,83 ms na 2-FSK e 10 ms nas demais.

A 2-FSK usa os tons do padrão Bell 202, 1200 e 2200 Hz, a 1200 símbolos por segundo. O receptor multiplica o sinal por uma cópia atrasada de si mesmo, e o sinal algébrico do produto filtrado indica o tom presente. Essa decisão depende do nível relativo dos dois tons, e um canal que atenue um deles mais que o outro desloca todas as decisões no mesmo sentido.

A 5×2-FSK votada emite, a cada símbolo, um tom de cada um de cinco pares, todos com o mesmo bit, a 100 símbolos por segundo. Os tons de cada par distam 200 Hz, próximos o bastante para que o canal os trate de modo semelhante, e cada par vota no mais forte. A maioria dá o bit, e um par em um mínimo da resposta em pente perde a votação sem decidir o resultado.

A 5×2-FSK multicanal usa os mesmos pares como cinco canais 2-FSK independentes, cada um com um de cinco bits consecutivos dos dados. A taxa quintuplica, mas, sem votação, um par em um mínimo do pente perde o seu bit.

Nas duas formas de cinco pares, os dez tons foram escolhidos para que o segundo e o terceiro harmônicos (seção 2.2, Figura 5) de um tom do valor 0 não caiam sobre um tom do valor 1, nem o contrário, pois um harmônico nessa posição somaria energia ao valor errado.

A 16-FSK emite um tom por símbolo, entre dezesseis frequências de 888 a 3325 Hz espaçadas de cerca de 162 Hz, e carrega quatro bits a 100 símbolos por segundo. Os valores seguem o código Gray, em que tons vizinhos carregam valores que diferem em um só bit, e não em até quatro, como de 0111 para 1000 no binário comum. O erro mais provável é a confusão com o vizinho, que recebe o vazamento do tom transmitido (Figura 4), e com o código Gray ele custa um bit.

Nas formas de cinco pares, cinco tons dividem o mesmo pico de amplitude e cada um sai cerca de 14 dB abaixo do que sairia sozinho, enquanto na 16-FSK um único tom recebe toda a amplitude disponível.

### 3.2 Decisão contra o piso

Como cada tom deve ser comparado com o piso de ruído da própria frequência (seção 2.2), o receptor da 16-FSK divide a energia de cada tom na janela pelo piso de ruído corrente daquela frequência e escolhe o maior, conforme (3).

$$\hat{k} = \arg\max_k \frac{E_k}{P_k} \tag{3}$$

Nela, $E_k$ é a energia no tom $k$ e $P_k$ é a média corrente dessa energia, atualizada a cada símbolo em todos os tons menos o vencedor. Como cada tom fica em silêncio em quinze de cada dezesseis símbolos, essa média estima o piso sem contaminação pelo sinal.

A Figura 7 mostra essa decisão em um símbolo recebido no sistema implementado. O tom transmitido fica 8,0 dB acima do segundo colocado, contra uma mediana de 7,9 dB ao longo do bloco.

![](figuras/16fsk-decisao.png "0.95")
Figura 7 - Decisão da 16-FSK em um símbolo. Em cima, o espectro da janela e o piso corrente de cada tom. Embaixo, a energia de cada tom acima do próprio piso, que é a grandeza comparada em (3).

Além do valor decidido, o receptor entrega a confiança de cada bit, a diferença, em logaritmo, entre o melhor tom em que o bit vale 1 e o melhor em que vale 0. Essa confiança, chamada verossimilhança logarítmica, do inglês *log-likelihood ratio* (LLR), é usada pela camada de enlace na correção de erros.

### 3.3 Sincronismo de símbolo

Os dois computadores não compartilham relógio. Cada um conta o tempo pelo próprio oscilador, e as contagens se afastam pouco a pouco. O receptor precisa, portanto, descobrir onde começa cada símbolo e quanto ele dura de fato.

A primeira implementação do sistema usou uma malha de adiantamento e atraso. A cada símbolo, o receptor mede o tom também um pouco antes e um pouco depois do instante esperado e desloca a leitura seguinte para o lado em que o tom apareceu mais nítido. Só há o que medir quando o tom muda, e por isso a transmissão começa com um preâmbulo de tons alternados, que dá à malha tempo de se ajustar.

A malha leva alguns símbolos para se ajustar, e enquanto não se ajusta lê errado justamente o início do quadro, onde estão a palavra de referência e os primeiros bits do bloco.

A implementação atual marca o quadro por fora, com uma varredura em cada extremidade. A varredura é um som de 80 ms cuja frequência sobe continuamente de 700 a 3400 Hz, como um assobio que vai do grave ao agudo. Essa forma não se confunde com os tons dos dados nem com o ruído, e o receptor a localiza comparando o sinal recebido, posição a posição, com uma cópia dela, pela mesma correlação usada para a palavra de referência (seção 4.2). A primeira varredura dá o início do quadro.

A distância entre as varreduras dá também o período real do símbolo, conforme (4).

$$T = \frac{n_2 - n_1}{S} \tag{4}$$

Nela, $n_1$ e $n_2$ são as posições das duas varreduras, em amostras, e $S$ é o número de símbolos entre elas.

A Figura 8 mostra, no formato do visor da seção 5, um quadro curto de 18 símbolos, gerado pelo modulador sem passar pelo ar para que cada símbolo fique visível. O receptor marca $n_1$ no fim da primeira varredura e $n_2$ no início da segunda, e (4) dá as fronteiras de símbolo desenhadas.

![](figuras/sincronismo-varreduras.png "0.95")
Figura 8 - Quadro curto de 16-FSK entre as duas varreduras de sincronismo, gerado pelo modulador do sistema, com a frequência na horizontal e o mais recente no alto. As linhas finas são as fronteiras de símbolo obtidas por (4).

No sistema implementado, em quatro quadros de 2453 símbolos recebidos entre as duas máquinas, o período medido por (4) variou de 479,90 a 480,07 amostras, contra 480 nominais. Um desvio de 0,1 amostra por símbolo acumula cerca de 245 amostras no quadro, meio símbolo e mais que as 72 do intervalo de descarte, e com o período nominal o fim do quadro seria lido fora do símbolo.

Pela mesma conta, $S$ tem de ser exato, pois um símbolo a mais ou a menos erra o período em 480/2453 ≈ 0,2 amostra, e o erro acumulado no quadro chega a um símbolo inteiro.

No enlace negociado da seção 4.4, todo quadro leva as duas varreduras, e o receptor usa só elas. A malha permanece apenas no primeiro protótipo, configurado por comandos, em que as varreduras são opcionais.

### 3.4 Nível de operação

Como a cadeia analógica achata os picos e gera harmônicos acima de certo nível (seção 2.2), o volume do alto-falante e o ganho de captura ficam abaixo desse ponto em todos os ensaios.

Na 16-FSK, a troca abrupta de tom a cada símbolo produz picos cerca de 2,5 vezes maiores que os de um tom contínuo, como se mediu no sistema implementado, e por isso o nível é calibrado com uma transmissão real, e não com um tom.

<!-- Pendente: confirmar com o autor se a 2-FSK da Tabela 1 é a de Bell 202 (1200/2200 Hz, 1200 baud, sem correção de erros) ou a 2-FSK justa de 1700/2350 Hz a 100 baud com FEC (fsk2 no código). O texto acima descreve a de Bell 202, como a primeira versão. Gray: o código foi corrigido em 2026-10-29 (valor = gray(tom)); a Tabela 1 precisa ser medida já com essa versão. -->

## 4 CAMADA DE ENLACE

A camada de enlace recebe da camada física os bits com a sua confiança e entrega à aplicação os dados íntegros e na ordem de envio. Ela corrige erros, localiza o bloco no fluxo recebido, divide os dados em pacotes com retransmissão e negocia o enlace pelo próprio som.

### 4.1 Correção de erros

Mesmo com o nível ajustado, parte dos bits chega trocada. Para corrigi-los sem nova transmissão, o transmissor envia bits além dos da mensagem, e esse excesso, chamado redundância, permite ao receptor desfazer as trocas.

A redundância mais simples é repetir cada bit três vezes e decidir pela maioria, o que corrige uma cópia trocada, mas cada cópia só confere o próprio bit. Duas cópias trocadas bastam para a maioria errar, mesmo com os vizinhos certos, e esse único bit faz o pacote inteiro falhar na verificação.

O sistema usa um código convolucional, que também envia três bits por bit da mensagem, mas nenhum deles é cópia. Cada bit enviado resulta de uma operação lógica entre o bit que entra e alguns dos anteriores, e por isso confere vários bits da mensagem de uma vez. Um bit trocado no ar pode então ser reconstituído pelos demais bits enviados que dependem dos mesmos bits da mensagem.

A operação é o ou-exclusivo, que dá 1 quando a quantidade de uns é ímpar e 0 quando é par. A Figura 9 mostra o cálculo com um exemplo. O codificador guarda em fila os sete últimos bits da mensagem, e cada um dos três bits enviados é o ou-exclusivo de um grupo diferente desses sete. A cada bit novo a fila anda uma posição, e cada bit da mensagem participa de sete cálculos seguidos.

![](figuras/codificador.png "0.95")
Figura 9 - Codificador convolucional com um exemplo. A fila guarda os sete últimos bits da mensagem, e cada bit enviado é o ou-exclusivo dos bits marcados na sua linha. Ao lado de cada linha, o padrão de ligações, com 1 para caixa ligada, e o mesmo padrão em octal.

Na nomenclatura da literatura, o código tem taxa um terço, três bits enviados por bit da mensagem, e comprimento de restrição sete, os sete bits de cada cálculo (PROAKIS; SALEHI, 2008). Cada grupo é identificado pelo padrão de ligações da sua linha na Figura 9, lido do bit que entra ao mais antigo. A primeira linha dá 1111001, que em octal, de três em três bits, se escreve 171, e as outras duas dão 133 e 165.

Na recepção, o algoritmo de Viterbi procura a mensagem cuja codificação mais se parece com o que chegou (VITERBI, 1967). Como cada bit da mensagem entra em vários bits enviados, uma mensagem errada discorda do recebido em muitas posições, e a certa, só nas poucas trocadas. Cada discordância pesa conforme a confiança do bit, o que se chama decisão suave, e um bit trocado com baixa confiança quase não pesa.

A combinação de código convolucional e decodificação de Viterbi se firmou nos enlaces de comunicação espacial, em que o canal também entrega bits ruidosos e o decodificador alcança desempenho próximo do ótimo com complexidade modesta (FORNEY, 1973).

A Figura 10 mostra a correção de um bloco recebido no sistema implementado. Dos 1170 bits codificados, 112 chegaram errados, 9,6%, e a mensagem saiu sem erro. O painel de baixo mostra por quê, 107 dos 112 bits errados chegaram com confiança abaixo de 1,7, contra 273 dos 1058 certos, e por isso os errados pesaram pouco.

![](figuras/correcao-bloco.png "0.95")
Figura 10 - Correção de um bloco de 48 bytes recebido em 16-FSK. Em cima, a posição dos bits codificados errados, na ordem de transmissão. No meio, a mensagem decodificada, sem erros. Embaixo, quantos bits errados e certos chegaram em cada faixa de confiança.

Antes da transmissão, os bits codificados são entrelaçados, escritos em linhas e lidos em colunas, o que afasta no tempo bits vizinhos no código. Uma perturbação curta, como um ruído de rajada, atinge então bits espalhados, que o decodificador corrige um a um. O bloco pode ainda ser repetido, o que aumenta a tolerância a erros à custa de tempo de transmissão.

### 4.2 Localização do bloco

A camada física entrega uma sequência contínua de bits, com o preâmbulo e o que veio antes e depois do bloco, sem indicar qual é o primeiro bit do bloco, e decodificar a partir de um único bit adiantado ou atrasado já produz mensagem errada. Contar os bits desde o início não resolve, pois a malha de sincronismo da seção 3.3 pode ganhar ou perder um símbolo no preâmbulo, e na 16-FSK cada símbolo vale quatro bits.

Logo antes do bloco o transmissor coloca uma palavra de referência de 31 bits, conhecida pelas duas pontas. O receptor desliza essa palavra sobre os bits recebidos e conta as coincidências em cada posição. Fora da palavra elas ficam em torno da metade, como num sorteio, e na posição da palavra quase todos os 31 bits coincidem. Essa busca é a correlação, e o bloco começa no bit seguinte ao da maior coincidência.

A Figura 11 mostra a palavra no quadro transmitido, entre o preâmbulo e o bloco codificado, que ocupa a maior parte do tempo no ar.

![](figuras/quadro-codificado.png "0.95")
Figura 11 - Quadro de 48 bytes em 16-FSK, em escala de tempo, entre as duas varreduras de sincronismo da seção 3.3.

### 4.3 Pacotes e retransmissão

Para transferir um arquivo, os dados são divididos em pacotes com número de sequência, comprimento e verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), de 16 bits. O receptor pede um pacote, confere o CRC e só então pede o seguinte, repetindo o pedido até quatro vezes se a verificação falhar, no arranjo pare-e-espere dos protocolos de enlace (TANENBAUM; WETHERALL, 2011). Ao fim, um CRC de 32 bits confirma o arquivo inteiro.

A retransmissão só converge se a maioria dos pacotes chegar íntegra na primeira tentativa, e por isso complementa a correção de erros sem substituí-la.

### 4.4 Negociação do enlace pelo ar

Até aqui, as duas pontas precisam combinar de antemão a forma de transmissão, os tons, o nível e a taxa. A negociação faz esse acordo pelo próprio som, sem canal auxiliar nem ajuste manual, no início de cada sessão, nome dado a cada conexão da chamada ao último pacote de dados.

A estação que chama emite um par de varreduras de frequência, e a que escuta responde. Cada uma sonda então o canal no sentido em que transmite, com tons isolados em todas as frequências candidatas e com blocos conhecidos em volumes crescentes do alto-falante, repetidos com dois ganhos do microfone de quem escuta.

O receptor, que mediu a sondagem, decide a configuração de cada sentido. O acordo, chamado contrato, fixa a modulação, 16-FSK ou 2-FSK, os tons utilizáveis, o volume do alto-falante de quem transmite, o ganho do microfone de quem recebe, a velocidade em símbolos por segundo e o número de repetições do bloco codificado (seção 4.1). Enviado o contrato ao transmissor, os dados seguem em pare-e-espere, e se os pacotes falharem repetidamente o transmissor recua para mais repetições ou menos símbolos por segundo.

A Figura 12 mostra uma sessão do sistema implementado, da chamada aos dados, com um pacote ilegível pedido de novo e retransmitido.

![](figuras/negociacao.png "0.8")
Figura 12 - Sequência de uma sessão negociada pelo ar, em escala de tempo. Cada seta vai do fim da leitura de um turno ao fim da leitura do seguinte. A seta tracejada é um pacote ilegível.

A medição se repete a cada sessão porque o canal muda com o tempo. No sistema implementado, em três séries de gravações do mesmo dia, três dos dezesseis tons concentraram de 47% a 90% dos erros de símbolo de cada série, e não foram os mesmos de uma série para outra (Figura 13). Uma lista fixa de tons a evitar serviria a uma conexão e não à seguinte.

![](figuras/erros-por-tom.png "0.95")
Figura 13 - Fração dos erros de símbolo em cada tom da 16-FSK, em três séries de gravações do mesmo dia e no mesmo sentido. Os marcadores cheios são os três piores tons de cada série, e a linha pontilhada, a fração de cada tom se os erros se distribuíssem por igual.

## 5 INTERFACE COM A APLICAÇÃO

O enlace negociado é operado em cada computador por uma tela no navegador, o visor, que inicia a sessão, mostra o estado do enlace e apresenta ao final os dados recebidos.

A Figura 14 mostra o visor. O espectrograma do microfone, com o mais recente no alto, mostra os sinais que chegam, e a escala de frequência acima dele marca os tons contratados em cada sentido. Um fluxograma indica a etapa da negociação, da chamada ao contrato e aos dados, e contadores e listas registram os últimos sinais enviados e ouvidos e as decisões tomadas. Com isso, a sessão é acompanhada sem consultar registros.

![](figuras/telas-visor-celular.png "0.95")
Figura 14 - Visor no computador (a) e no celular (b), durante a transferência de um arquivo.

Sobre o mesmo enlace estão em implementação uma conversa, com o canal aberto entre as mensagens, e um terminal de comandos.

<!-- Figura 14 PROVISÓRIA: as duas telas ainda mudam (percurso e régua de tons); refazer no fim dos testes, com resultados/FIG-TELAS/COMO-REFAZER.md, e rever o parágrafo acima, que ainda descreve a tela antiga. Chat e terminal: descrever quando estiverem prontos (outra sessão). Porta serial virtual: hoje só app.py --pty, sobre a 2-FSK de Bell 202 sem correção de erros, que não entregou mensagem pelo ar; o enlace negociado não expõe porta serial. O resumo e a introdução afirmam a porta serial virtual: rever. -->

## 6 RESULTADOS EXPERIMENTAIS

Os ensaios foram feitos com dois computadores na mesma sala, cada um com alto-falante e microfone de uso geral, e com um celular no lugar de um deles nos ensaios das formas de transmissão e da transferência de arquivo. No ensaio do sincronismo, um canal de controle entre os computadores apenas comanda a gravação, e os bytes avaliados viajam somente pelo ar. Foram usadas duas montagens, uma com o alto-falante a 10 cm do microfone e outra com ele afastado, sempre com o nível abaixo da saturação.

Com o alto-falante a 10 cm do microfone de um celular, cada forma de transmissão enviou o mesmo texto de 320 bytes em 10 pacotes de 32 bytes, a 100 símbolos por segundo e com repetição 3, configurados à mão nas duas pontas. A Figura 15 mostra a taxa efetiva de cada uma, contadas as confirmações, e os bits recebidos errados em cerca de 29 mil.

![](figuras/resultado-formas.png "0.95")
Figura 15 - Taxa efetiva de cada forma de transmissão, a 10 cm, do primeiro envio à última confirmação, e, dentro de cada barra, os bits recebidos errados antes da correção, em cerca de 29 mil. As quatro entregaram os 10 pacotes na primeira tentativa, idênticos ao enviado.

As quatro formas entregaram o texto inteiro, sem nenhuma retransmissão, com no máximo 8 bits errados, todos corrigidos. As que transmitem quatro ou cinco bits por símbolo, a 16-FSK e a 5×2-FSK multicanal, chegam a 2,5 B/s, quase três vezes as de um bit por símbolo. Com essa folga de erros, a repetição 3 é mais do que o canal exige, e as taxas não medem o limite de cada forma.

<!-- Fontes: H09-QUATRO-FORMAS-10CM (RESUMO.md; uma sessão por forma, 2026-10-30; votada com o embaralhamento da carga, as outras sem). Script: resultados/H09-QUATRO-FORMAS-10CM/figuras/figura_formas.py. A figura antiga (blocos de 48 bytes entre computadores, F02 com uma gravação excluída) saiu pela regra do autor: só testes em que as quatro formas passam. -->

Além de decidir cada tom, o receptor precisa saber onde começa cada símbolo, e a seção 3.3 apresenta duas formas de obter isso. Na primeira, a malha de adiantamento e atraso corrige o instante símbolo a símbolo, a partir do próprio sinal. Na segunda, as duas varreduras nas pontas do quadro marcam por fora onde ele começa e quanto dura cada símbolo. A Figura 16 compara as duas sobre as mesmas 24 gravações de blocos de 48 bytes em 16-FSK, feitas num único computador que tocava e gravava ao mesmo tempo.

![](figuras/sincronismo-bloco.png "0.95")
Figura 16 - Bits certos ao longo do quadro, em janelas de 5%, na média de 24 gravações lidas com a malha e com as varreduras. Ao lado de cada curva, os blocos entregues íntegros.

Com as varreduras, o acerto fica perto de 91% desde o primeiro bit. Com a malha, cai a 83,5% nos primeiros 10% do quadro e só se iguala depois que ela se ajusta. É nesse trecho que fica a palavra de referência, e um início mal lido basta para o bloco se perder: a malha entregou 15 dos 24 blocos, e as varreduras, 23.

<!-- Fontes: 12-13-SYNC (4 gravações, 192 B, rep 2), H03-2FSK-FEC (as 8 com varreduras), studies/20260903-111105-ganho-mary (uma máquina, ganho 0,20 a 0,38). -->

Com os blocos entregues, a transferência de arquivo depende dos pacotes e da retransmissão da seção 4.3. Uma imagem de 1334 bytes foi transferida entre os dois computadores com o alto-falante afastado e chegou idêntica, conferida pelo CRC de 32 bits. Em pacotes de 64 bytes, os 21 pacotes chegaram sem retransmissão, a 6,8 B/s, e em pacotes de 128 bytes, os 11 chegaram com 3 retransmissões, a 7,2 B/s. A 10 cm, três transferências da mesma imagem também chegaram idênticas, de 5,0 a 7,6 B/s. A taxa fica abaixo da do bloco isolado pelo preâmbulo, pelo cabeçalho e pela espera entre pacotes.

A Figura 17 mostra duas imagens enviadas do computador para um celular, com a 16-FSK a 100 símbolos por segundo, em pacotes de 32 bytes e com a configuração fixada à mão nas duas pontas. As duas chegaram idênticas às enviadas, conferidas pelo CRC de 32 bits, com todos os pacotes na primeira tentativa. O logotipo, de 1270 bytes, chegou em 40 pacotes, com o bloco sem repetição, em 329 s, ou 3,9 B/s, com 5,0% dos bits recebidos errados. A bandeira, de 934 bytes, chegou em 30 pacotes, com o bloco repetido duas vezes, em 324 s, ou 2,9 B/s, com 5,4%. Em ambas a correção de erros recuperou todos os bits, e a taxa fica abaixo da do bloco isolado porque, em pacotes curtos, a espera pela confirmação pesa mais.

![](figuras/arquivo-enviado-recebido.png "0.6")
Figura 17 - Imagens recebidas pelo celular pelo ar, idênticas byte a byte às enviadas pelo computador.

Por fim, no enlace negociado as duas pontas partem sem configuração prévia. Com os computadores a cerca de 2 m, uma sessão entregou completos os 207 bytes de um sentido e os 44 do outro, em 302 s contados da chamada. A Figura 18 mostra o que cada receptor mediu na sondagem e o que contratou.

![](figuras/enlace-contratos.png "0.95")
Figura 18 - Margem de cada tom na sondagem de uma sessão negociada, em cada sentido, e os tons que o contrato daquele sentido usou. Acima de cada faixa, o ganho digital, a repetição e a velocidade contratados, e os bytes entregues.

Num sentido, o receptor excluiu os três tons de margem mais baixa, entre 1862 e 2188 Hz, e deslocou a faixa para cima; no outro, todos os tons da faixa de fábrica tinham margem acima de 30 dB e nenhum foi excluído. Os ganhos contratados também diferem, 0,20 e 0,12. Com outro computador em uma das pontas, a sessão também se completou, em 405 s.

<!-- Fontes: H07-ENLACE-MODOS (2026-10-22), H06-ENLACE-AR sessão 3 (contratos: A->B exclui 4 tons, ganho 0,45, rep 2; B->A exclui 3, ganho 0,3, rep 1), sessoes-enlace-2maq/20261027-175531 (405 s). Figura do visor em modo projeção com as fases: a capturar. 6.6 chat e terminal: quando medidos. -->

## 7 CONSIDERAÇÕES FINAIS

<!-- Roteiro, capítulo 7. Por redigir por último. -->

## DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA

Em conformidade com a Portaria CNPq nº 2.664/2026, os autores declaram o uso de Claude-Code (Anthropic) e Codex (OpenAI) na concepção, para discussão da abordagem e levantamento de referências, na implementação e na análise, para redação e depuração do software do modem e dos scripts de ensaio, e na redação do texto, para clareza e correção de linguagem. Todo o conteúdo gerado foi verificado e editado pelos autores, que assumem responsabilidade integral pelo trabalho.

<!-- A primeira versão dizia "firmware"; o projeto não tem firmware, trocado por "software do modem". -->

## CONFLITO DE INTERESSES

Os autores declaram não haver conflito de interesses no desenvolvimento e na publicação deste trabalho.

## REFERÊNCIAS

FINNEGAN, Kenneth W.; BENSON, Bridget. Clarifying the amateur Bell 202 modem. In: **ARRL/TAPR Digital Communications Conference (DCC)**, 33., 2014. Anais [...]. [S.l.]: TAPR, 2014.

FORNEY JR., G. David. The Viterbi algorithm. **Proceedings of the IEEE**, v. 61, n. 3, p. 268-278, mar. 1973.

GERGANOV, Georgi. **ggwave**: tiny data-over-sound library. 2021. Disponível em: https://github.com/ggerganov/ggwave.

KUTTRUFF, Heinrich. **Room acoustics**. 6. ed. Boca Raton: CRC Press, 2016.

LOPES, Cristina Videira; AGUIAR, Pedro M. Q. Aerial acoustic communications. In: **IEEE Workshop on Applications of Signal Processing to Audio and Acoustics (WASPAA)**, 2001, New Paltz. Anais [...]. New Paltz: IEEE, 2001.

LOPES, Cristina Videira; AGUIAR, Pedro M. Q. Acoustic modems for ubiquitous computing. **IEEE Pervasive Computing**, v. 2, n. 3, p. 62-71, 2003. DOI: 10.1109/MPRV.2003.1228528.

PROAKIS, John G.; SALEHI, Masoud. **Digital communications**. 5. ed. Nova York: McGraw-Hill, 2008.

PUTZ, Florentin; FORTMANN, Philipp; FRANK, Jan; HAUGWITZ, Christoph; KUPNIK, Mario; HOLLICK, Matthias. Evaluating acoustic data transmission schemes for ad-hoc communication between nearby smart devices. **ACM Transactions on Internet of Things**, v. 7, n. 1, art. 8, 2026. arXiv:2602.02249.

TANENBAUM, Andrew S.; WETHERALL, David J. **Computer networks**. 5. ed. Boston: Pearson, 2011.

VITERBI, Andrew J. Error bounds for convolutional codes and an asymptotically optimum decoding algorithm. **IEEE Transactions on Information Theory**, v. IT-13, n. 2, p. 260-269, abr. 1967.

WU, Joseph. **A basic guide to the HART protocol**. Dallas: Texas Instruments, nov. 2023. (Application Report SLAAEH0). Disponível em: https://www.ti.com/lit/pdf/slaaeh0.

<!-- KUTTRUFF, PROAKIS, TANENBAUM e VITERBI ficam se os capítulos 2 a 4 os citarem; retirar os que sobrarem sem citação. -->
