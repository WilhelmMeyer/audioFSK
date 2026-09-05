<!--
FONTE DO TEXTO. VII SIMECA / IFPR. Artigo do modem acustico.

Montagem: ./artigo/monta.sh  (gera artigo_modem.docx e artigo_modem.pdf; aceita --verifica, --sem-figuras)
Conversor: artigo/simeca-md (submodulo). Correcao no conversor se faz la, nunca por copia.
Estilo: artigo/estilo.md. Ler antes de redigir qualquer secao.

Meta de extensao: 5 laudas, relaxado. Piso 4, teto o que o conteudo pedir.
Orcamento: ~750 palavras por lauda em A4 duas colunas 10 pt; figura ou tabela conta 150-250.
  5 laudas = ~3750 equivalentes. Com 5 figuras/tabelas (~1000), sobram ~2700 palavras de prosa.
  Distribuicao proposta, em palavras de prosa:
    resumo 200 | introducao 500 | meio 350 | fisica 550 | enlace 400 | bancada e resultados 750 | consideracoes 200
Contagem: wc -w artigo/artigo_modem.md  (inclui comentarios; descontar)

Regras do modelo: titulo ate 3 linhas; resumo 150-300 palavras; 3-5 palavras-chave separadas por ponto final.
Convencoes: um paragrafo = uma linha; sem travessao na prosa; equacoes $...$ e $$...\tag{N}$$;
  figura como ![](figuras/x.png "escala") seguida da linha "Figura N - legenda";
  "Tabela N - legenda" na linha antes da tabela em pipes; numeracao e conferida, nao gerada.
Processo: o autor conduz trecho a trecho. Este arquivo e esqueleto: secoes, o que entra em cada uma, e os numeros
  de resultados/ que sustentam cada afirmacao. Nenhum paragrafo redigido sem pedido.
Nenhum numero entra sem origem em resultados/<pasta>. Quando houver fatos.md, ele passa a ser a ficha.

ENQUADRAMENTO (decisao do autor, 2026-09-05): artigo didatico. Apresenta o sistema proposto, compara brevemente
com outros meios de transmissao, avalia o problema do canal acustico e propoe uma solucao para este caso. Nao
pretende substituir outro meio nem reivindicar melhoria sobre a literatura.

CAMADAS (decisao do autor, 2026-09-05): o artigo apresenta a implementacao de duas camadas.
  Fisica: as quatro formas de transmissao (2-FSK, 5x2-FSK votada, 5x2-FSK multicanal, 16-FSK), o sincronismo de simbolo (gate early/late e
    varreduras) e a decisao suave que o demodulador entrega.
  Enlace: o bloco codificado (convolucional K=7, Viterbi suave, entrelacamento, repeticao, palavra de sincronismo por
    correlacao), o pacote com numero de sequencia e CRC, a subdivisao do arquivo em pacotes e o reenvio do pacote que
    nao chega ate um limite de tentativas. Subdivisao e reenvio sao enlace, ao modo de HDLC, nao transporte.
  Acima das duas a aplicacao ve uma porta serial virtual.

NOMENCLATURA (decisao do autor, 2026-09-05; fixa, nao muda mais):
  M-aria: modulacao de ordem M, em que cada simbolo e um tom escolhido entre M frequencias e carrega log2(M) bits.
    Abrange as quatro formas, inclusive a binaria (M = 2). Explicar assim na primeira ocorrencia.
  FSK: modulacao por chaveamento na frequencia, do ingles *frequency shift keying* (FSK). Designa a 2-FSK.
  MFSK: chaveamento em multiplas frequencias, do ingles *multiple frequency shift keying* (MFSK). Designa as que
    usam mais de duas frequencias: 5x2-FSK (nas duas variantes) e 16-FSK.
  Cada sigla apresentada uma vez, assim, e dai em diante so a sigla ou a notacao numerada.
  As quatro formas de transmissao, sempre por esta notacao:
    2-FSK: um tom entre dois, um bit por simbolo (tons do padrao Bell 202, 1200 baud; "Bell 202" e o nome do
      padrao, aparece uma vez).
    5x2-FSK votada: cinco canais 2-FSK em paralelo carregando o mesmo bit, decisao por maioria; um bit por simbolo.
    5x2-FSK multicanal: cinco canais 2-FSK em paralelo, um bit distinto em cada; cinco bits por simbolo.
    16-FSK: um tom entre dezesseis, quatro bits por simbolo.
  Nunca: "20-FSK" para as de cinco pares (M conta tons dos quais UM soa); "M-ario" sem o M explicado; "MFSK" como
    nome de uma unica forma; nomes internos do codigo (mary, mfsk-par, fecrep) na prosa.
  Desvio em relacao ao codigo e ao CLAUDE.md da raiz: la "MFSK" e a de cinco pares e "M-ary" e a de dezesseis tons.
    No artigo nao. A correspondencia esta no CLAUDE.md da raiz, secao "Nomes no codigo e nomes no artigo".
  Forma de toda sigla estrangeira: nome em portugues, "do ingles", termo em italico, sigla entre parenteses depois
    do termo. Ex.: correcao antecipada de erros, do ingles *forward error correction* (FEC); verificacao de
    redundancia ciclica, do ingles *cyclic redundancy check* (CRC); verossimilhanca logaritmica, do ingles
    *log-likelihood ratio* (LLR); retransmissao automatica, do ingles *automatic repeat request* (ARQ).
-->

# Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele

<!--
Titulo: objeto + problema + solucao, tom didatico, sem promessa de melhoria. Maximo 3 linhas. Candidatos:
- Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele
- Um modem acústico com placa de som e microfone: da modulação binária ao M-ário com correção de erros
- Enlace de dados pelo ar audível: o que o canal faz com o sinal e o que se fez a respeito
Elementos: audivel; placa de som e microfone de prateleira; canal medido; 16-FSK; correcao de erros.
-->

**AUTORES:**

<!--
nome | ORCID | filiacao | e-mail. ORCID vazio remove o icone. Dois autores, ordem decidida em 2026-09-05.
Linha 1: o proprio Winderson preenche ORCID, campus e e-mail.
-->

1. Winderson | | IFPR | 
2. Jefferson Wilhelm Meyer Soares | 0000-0003-3372-9298 | IFPR, Campus Jacarezinho | jefferson.soares@ifpr.edu.br

**DOI:** https://doi.org/10.5281/zenodo.XXX

## RESUMO

<!--
Redigido em 2026-09-05. Ordem: o que apresenta; o problema, que e o meio; a solucao em duas camadas; a implementacao e
o metodo; os numeros. So a ultima frase tem numero. O que nao foi tratado (latencia, voz medida) fica fora.
Fonte dos numeros: resultados/14-FEC-REP, resultados/15-PKT-ARQ.
-->

Este artigo apresenta a transmissão de dados por som audível entre dois computadores, com alto-falante e microfone comuns, expondo o enlace à aplicação como uma porta serial. O meio acústico impõe condições severas: a banda audível comporta poucas unidades de informação por segundo, aqui chamadas de símbolos, a amplitude que chega não é a que saiu, frequências vizinhas chegam com dezenas de decibéis de diferença, o eco de um símbolo invade o seguinte, o ruído e a fala ocupam a mesma banda, e o hardware também pode saturar e distorcer o sinal. Tratamos essas dificuldades em duas camadas. Na física, conferimos quatro modulações de ordem M, ditas M-árias, em que cada símbolo é um tom escolhido entre M frequências e carrega tantos bits quanto essa escolha permite: a 2-FSK binária, modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), e três por chaveamento em múltiplas frequências, do inglês *multiple frequency shift keying* (MFSK), a 5×2-FSK com o mesmo bit em cinco canais e decisão por voto, a 5×2-FSK multicanal com cinco bits em paralelo, e a 16-FSK com quatro bits por símbolo. Mesmo na melhor dessas formas, parte dos bits pode chegar com erro ou se perder, e na camada de enlace implementamos a correção antecipada de erros, do inglês *forward error correction* (FEC), o sincronismo de quadro por palavra de referência, a segmentação do arquivo em pacotes com verificação de redundância cíclica, do inglês *cyclic redundancy check* (CRC), e a retransmissão automática, do inglês *automatic repeat request* (ARQ). Medimos cada recurso sobre gravações do mesmo enlace, para comparar as variantes sobre o mesmo ar. Na melhor configuração o enlace entregou cerca de 11 bytes por segundo com 12 blocos íntegros em 12, e um arquivo de 1334 bytes chegou idêntico em 21 pacotes de 21, sem reenvio.

**PALAVRAS-CHAVE:** Modem acústico. Modulação por chaveamento de frequência. Codificação convolucional. Canal acústico.

## 1 INTRODUÇÃO

<!--
Funil em cinco a sete paragrafos, um passo por paragrafo, citacoes em aglomerado no fim de cada um (estilo.md, secao 1).
Orcamento ~500 palavras.

P1  Contexto amplo: os meios de levar bytes de uma maquina a outra e o que cada um exige. Cabo (serial, USB,
    Ethernet): taxa alta, exige porta e cabo. Radio (Wi-Fi, Bluetooth): exige transceptor e pareamento, e ha
    ambientes que o vetam. Infravermelho: linha de visada. Som audivel: alto-falante e microfone ja estao em toda
    maquina, nada a instalar, taxa baixa e alcance de uma sala. Comparacao breve, sem ranking; cada meio serve a um
    caso. Tabela 1 candidata: meio | hardware exigido | taxa tipica | alcance | onde cabe. Aglomerado de citacoes.
    Onde o som cabe: pareamento, transferencia curta, ambientes sem RF, ensino de comunicacao de dados com o que ha
    na sala.
P2  A heranca telefonica: 2-FSK nos tons do padrao Bell 202 (1200 baud, 1200/2200 Hz), discriminador de atraso e
    multiplicacao, UART 8N1.
    Funciona no fio. Frase curta que crava: no ar, o canal nao e um fio.
P3  O que o ar faz com o sinal: resposta em pente (vizinhos a 50 Hz diferem 13-18 dB), banda util 550-3500 Hz,
    limitador do alto-falante, sem reverberacao mensuravel. Ultrassom fora do alcance destes transdutores.
    Citacoes de canal acustico em ambiente fechado.
P4  O que se faz nesse canal: OFDM acustico, chirp, MFSK (no sentido da literatura, M tons), em geral com
    equalizador ou estimativa de canal.
    Aglomerado. Sem contraste de merito: sao as ferramentas do campo, e este trabalho usa as mais simples delas.
P5  O caso: duas maquinas de prateleira numa sala, sem nada a instalar, que precisam trocar poucos bytes com
    confianca. O que o caso pede: decisao insensivel ao ganho (o canal e um pente), erro reparavel onde cai
    (10-25% dos bits chegam errados), e um jeito de medir sem que a sala entre na medida.
P6  Em primeira pessoa, "apresentamos": (a) o canal medido, (b) tres camadas fisicas experimentadas no mesmo
    enlace, (c) a camada de correcao com sincronismo por correlacao, (d) o metodo de medicao
    com gravacoes e pontuacao pareada, (e) o que a bancada ensinou sobre a cadeia analogica. Fecha com uma linha
    anunciando a verificacao: duas maquinas, um arquivo inteiro pelo ar.
-->

## 2 O MEIO

<!--
O meio nao e camada: fica abaixo da fisica, como o ar fica abaixo da camada 1. Responde "com o que se esta lidando".
Propriedades gerais do som entre um alto-falante e um microfone numa sala, sem os numeros medidos nesta bancada;
esses ficam na 5, e aqui so o gancho ("como os resultados medem"). Numero so para fixar ordem de grandeza que a
fisica precise ("dezenas de dB entre frequencias vizinhas").
- Regras de transmissao via som: o que um alto-falante e um microfone comuns alcancam em frequencia; por que a
  informacao vai em frequencia e nao em amplitude (a amplitude que chega nao e a que saiu).
- Multiplos caminhos: o direto e as reflexoes se somam e formam uma resposta em pente; uma frequencia pode cair num
  nulo. Eco e reverberacao como fenomenos, e o que cada um faz com um simbolo (o anterior invade o seguinte).
- Interferencia e ruido da sala; a fala humana ocupa a mesma banda.
- Nao linearidade dos transdutores: limitador do alto-falante, transientes de troca de tom, compressao do microfone.
- Relogios de amostragem independentes nas duas maquinas: o periodo de simbolo recebido nao e o nominal.
- Ultrassom: fora do alcance dos transdutores comuns; o argumento (salas silenciosas la em cima) e certo e o
  hardware nao chega. Gancho para a 5.
Figura candidata: nenhuma com numero medido; se houver, um esquema do caminho direto e das reflexoes.
-->

## 3 CAMADA FÍSICA

<!--
O que se construiu sobre o meio para transformar bits em som e som em simbolos. Fronteira: a fisica lida com amostras
e entrega simbolos, com a verossimilhanca de cada bit; nao sabe o que os bits significam.
Mecanismo em palavras antes de qualquer equacao; cada equacao com frase fechada antes, "Nela," depois, leitura fisica
e gancho para o resultado que a mede. Sem adiantar os numeros da 5.
- Os metodos de transmissao, na ordem em que foram experimentados:
  2-FSK: um bit em uma de duas frequencias (tons do padrao Bell 202, 1200/2200 Hz, 1200 baud), bytes em 8N1;
    discriminador de atraso e
    multiplicacao, bit pelo sinal; sem portadora recuperada; squelch. Qualquer inclinacao do canal enviesa toda
    decisao no mesmo sentido, e o squelch e quadratico. O 8N1 e enquadramento de byte sem deteccao de erro e fica
    aqui como parte da modulacao; esse caminho nao tem enlace.
    Equacao candidata: saida do discriminador e D = fs/(4 f_c).
  5x2-FSK votada, 100 baud: cinco canais 2-FSK, pares de tons a 200 Hz, o mesmo bit em todos, um voto por par,
    maioria decide; o ganho cancela.
  5x2-FSK multicanal, 100 baud: os mesmos cinco canais, um bit distinto em cada, cinco bits por simbolo; a
    palavra de sincronismo lida por voto entre os canais e a repeticao espalhada por canais diferentes.
    Polaridade alternada ao longo da banda para que os dois simbolos tenham a mesma frequencia media. Limiar de
    presenca, porque um voto e uma razao e ruido puro elege um bit. Acorde de cinco divide a amplitude por cinco.
  16-FSK: um tom por vez entre dezesseis, quatro bits por simbolo, Gray entre vizinhos; cada tom dividido pelo seu piso
    corrente (silencioso 15 simbolos em 16, entao o piso e mesmo o ruido). Guarda de 35% do simbolo. Existe por
    potencia. Equacao candidata: pontuacao do tom k = E_k / piso_k, decisao argmax.
- Preambulo alternado e cauda ociosa, e por que nenhum e opcional.
- Relogio de simbolo: gate early/late guiado pelo contraste da decisao; e as duas varreduras de 80 ms que bracketam
  o quadro, dando o inicio como indice absoluto e o periodo medido entre elas. Ordenar os picos por posicao, nao por
  altura. Equacao candidata: periodo medido = (n2 - n1) / simbolos do quadro.
- O que a fisica entrega para cima: no caminho sem codigo, o bit; no codificado, a verossimilhanca de cada bit,
  quatro por simbolo na 16-FSK. E a interface entre as camadas, a LLR.
Figura candidata: diagrama de blocos do modulador e do demodulador 16-FSK.
-->

## 4 CAMADA DE ENLACE

<!--
O que se construiu sobre os simbolos para entregar bytes corretos: achar o bloco, reparar, conferir, reenviar.
Opera em bits e verossimilhancas, nunca em amostras. Subdivisao e reenvio sao enlace, ao modo de HDLC.
- Por que corrigir e nao so detectar: o enlace entrega uma fracao dos bits errada; um CRC so relata o dano. Bloco de
  tamanho fixo: nao ha o que deslizar (sob 8N1 um bit de start errado desloca tudo o que vem depois).
- Palavra de sincronismo de 31 bits (m-sequencia), achada por correlacao sobre as verossimilhancas, nunca por
  contagem de simbolos; e ela que resolve o alinhamento de nibble da 16-FSK.
- Codigo convolucional K=7, Viterbi de decisao suave (a verossimilhanca ja existia, o soft custou nada),
  entrelacamento, repeticao r. Tabela candidata: taxa de erro tolerada por variante (hard 8%, soft 8%, 1/3 soft 13%,
  1/3 x2 25%), da simulacao contra erros de bit; dizer que e simulada. A redundancia e um parametro combinado entre os
  dois lados.
- Pacote: byte de sincronismo, numero de sequencia, comprimento, CRC-16; cabecalho de 3 bytes, cauda de 2. Por que
  pacotes: o modem derruba bytes, nao so os corrompe, e um byte perdido desloca o resto; o pacote e a unidade que se
  confere e se reenvia.
- Subdivisao do arquivo em pacotes de tamanho fixo e reenvio: o receptor pede, confere o CRC e, se nao chega ou chega
  errado, pede de novo ate um limite de tentativas; transmissor sem estado. Pare-e-espere dirigido pelo receptor.
- Acima: a aplicacao ve uma porta serial virtual.
Fonte: fec.py, xfer.py, recvfile.py.
-->

## 5 BANCADA E RESULTADOS

<!--
Abre com o sistema, depois os resultados. Ordem dos resultados: primeiro o que o meio e (identificacao), depois a
operacao das camadas. Cada paragrafo de resultado com a celula: Figura N mostra + condicao + numero ± + previsto vs
medido + causa + o que passou a alimentar. Cada numero diz de qual direcao veio (B->A ou A->B).

5.a O sistema.
    Hardware: as duas maquinas, placas de som, alto-falante e microfone de cada uma, taxa de amostragem (48 kHz).
    Software: Python, com o processamento de sinal separado de toda entrada e saida (o mesmo codigo roda ao vivo e
    sobre gravacao), e a interface como porta serial virtual.
    Cabo serial entre as maquinas: mencao muito breve, como auxilio do ensaio (sincronizar o inicio, combinar a
    carga conhecida gerada dos dois lados), deixando claro que os bytes pontuados viajaram so pelo ar. Nunca como
    recurso da comunicacao. Uma frase.
    Metodo: gravacao do lado remoto transmitindo carga conhecida e pontuacao offline; um canal fixo permite comparar
    variantes sobre os mesmos segundos de ar. Pontuacao com alinhamento tolerante (o enlace derruba bytes). Regua
    unica: bits no melhor deslocamento, blocos inteiros como numero separado. Comparacao pareada sobre a mesma
    gravacao. Calibrar ganho numa rajada, nao num tom (transientes com 2,5x o pico). O que foi degradado de
    proposito e dito ao lado do numero.
    Tabela candidata: parametros do enlace (fs, baud por camada, tons, K, r, tamanho de bloco, ganho, guarda).
    Figura candidata: foto ou diagrama da bancada.

5.b O meio medido. Tom a tom (mediana de tres), nao por varredura: a varredura errou (1700 Hz a -27 dB na varredura,
    +50 dB no tom parado). Banda util 550-3500 Hz; acima de 4 kHz SNR cai (12 dB a 4000, 8 a 4500, ~0 a 5000), acima
    de 6 kHz negativa. Pente com 13-18 dB entre vizinhos a 50 Hz. Sem cauda de reverberacao: o sinal para no piso de
    ruido. Um voto elege um bit do silencio (485 bytes decodificados de sala vazia). Microfone comprime ~3,5 dB ao
    longo da rajada. Periodo de simbolo medido 479,96 ± 0,07 amostras onde o nominal e 480.
    resultados/02-LVL-TONE, 03-CH-CHIRP (as duas direcoes), 12-13-SYNC.
    Figura candidata: resposta em frequencia medida com os 16 tons marcados sobre o pente.

5.c Nivel e saturacao. O sinal de que a cadeia comprime: ganho digital MENOR ganha. A->B a ganho 0,5 fixo,
    alto-falante 1,00 / 0,45 / 0,20 / 0,10: 82,3% / 85,1% / 88,0% / 82,2% de bits, blocos 0/3, 0/3, 3/3, 1/3.
    U invertido com joelho em 0,20. A inversao do ganho digital em 0,45 (81,4% a 1,0 contra 89,1% a 0,25, picos
    recebidos so 0,10-0,19) some em 0,20. Levou A->B de 0 de 12 a 8 de 9. resultados/17-SPK-LEVEL-A2B, 16-SPK-A2B.
    Figura candidata: bits certos e blocos contra nivel do alto-falante.

5.d As quatro formas de transmissao no mesmo enlace. Tabela: forma | bits por simbolo | taxa | medido no ar
    (2-FSK nunca entregou uma mensagem; 5x2-FSK votada 1,8 B/s 4/4; 5x2-FSK multicanal 5,9 B/s 5/9; 16-FSK rep 2
    ganho 0,5 9,4 B/s 9/11; 16-FSK rep 1 cadeia linear 11,3 B/s 12/12). A 16-FSK recebe 0,14 rms onde os cinco
    canais simultaneos recebiam 0,07-0,09. Ligar cada linha a
    metodo da 3. resultados/04 a 08, 11, 14.

5.e Redundancia. Cadeia saturada: rep 1 0/6 e 1/6, rep 2 2/6 e 5/6, rep 4 4/7. Cadeia corrigida, 48 bytes, quatro
    gravacoes por ponto: rep 1, 2 e 4 todos 4 de 4, a 11,3 / 6,7 / 3,7 B/s. Redundancia compra a cauda, nao a media
    (um rep 4 leu 64% dos bits e entregou o bloco). resultados/14-FEC-REP.

5.f Relogio de simbolo. Oito gravacoes: gate 87,7% e 5/8; melhor deslocamento (oraculo) 89,3% e 7/8; varredura da
    frente 88,4% e 8/8; duas varreduras com periodo medido 89,0% e 8/8. O gate nao e ruim na media, colapsa (49,0%
    onde o relogio congelado leu 84,9%). Pareado: as varreduras leem mais bits em 59 de 60. Parte na auto-captura
    Bluetooth, canal diferente, dizer. resultados/12-13-SYNC.

5.g Arquivo inteiro. testcard.bmp, 1334 bytes, 21 de 21 pacotes de 64 bytes sem retransmissao a 6,8 B/s; 11 de 11
    a 7,2 B/s com 128 bytes (3 retransmissoes). Pacote maior amortiza o preambulo e falha mais; quase empata. Antes
    entregava 1 de 21 com pacotes de 81 bytes, e nada na subdivisao ou no reenvio mudou: a correcao analogica.
    Zero retransmissoes em 21 e resultado forte, mas nao mede a taxa de falha por pacote com precisao.
    resultados/15-PKT-ARQ.

5.h O que nao ajudou e o que ficou fora: marygap, maryband, marychord (custam ou nao medem nada); piloto por tom
    morto; a correcao do estimador de piso, boa na cadeia distorcida e pior na linear (0 de 3 contra 2 de 3), ainda
    nao no ar. Cada um com o numero e a pasta. Curto. resultados/09, 10, 11, INVESTIGACAO-A2B.md.
-->

## 6 CONSIDERAÇÕES FINAIS

<!--
Tres paragrafos, sem numero novo, os mesmos do resumo.
1. O que se apresentou: o meio e as duas camadas construidas sobre ele; o mecanismo de cada uma.
2. O que a estrutura fez: 11,3 B/s a 12 de 12; arquivo inteiro 21 de 21; e a observacao de que a linearidade da
   cadeia pesou mais que qualquer mudanca de codigo, nas duas direcoes do enlace. Situar de volta entre os meios:
   taxa de um teclado lento, hardware de qualquer maquina, para o caso descrito.
3. Passo seguinte e fronteira: varreduras no caminho de arquivo (nao medido); estimador de piso a medir no ar;
   ultrassom fora do escopo por transdutor, nao por argumento.
-->

## FINANCIAMENTO

<!-- Preencher ou remover. -->

## DECLARAÇÃO DE USO DE INTELIGÊNCIA ARTIFICIAL GENERATIVA

<!--
Manter atualizada: ferramenta usada e nao declarada e omissao; declarada e nao usada e inverdade.
Modelo (Portaria CNPq 2.664/2026): os autores declaram o uso de Claude Code (Anthropic) na concepcao, na
implementacao, na analise e na redacao; todo conteudo verificado e editado pelos autores.
-->

## CONFLITO DE INTERESSES

Os autores declaram não haver conflito de interesses no desenvolvimento e na publicação deste trabalho.

## REFERÊNCIAS

<!--
ABNT autor-data, ordem alfabetica, uma referencia por linha. Clusters:
- comunicacao acustica audivel entre dispositivos (P1)
- 2-FSK, padrao Bell 202 e discriminador (P2)
- canal acustico em ambiente fechado, resposta em pente (P3)
- OFDM/chirp/MFSK acusticos com equalizacao (P4)
- M-FSK, diversidade em frequencia, FSK multicanal (3)
- codigos convolucionais, Viterbi de decisao suave (2.3)
- m-sequencias / palavra de sincronismo (2.3)
-->
