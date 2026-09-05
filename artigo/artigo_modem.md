<!--
FONTE DO TEXTO. VII SIMECA / IFPR. Artigo do modem acustico.

Montagem: ./artigo/monta.sh  (gera artigo_modem.docx e artigo_modem.pdf; aceita --verifica, --sem-figuras)
Conversor: artigo/simeca-md (submodulo). Correcao no conversor se faz la, nunca por copia.
Estilo: artigo/estilo.md. Ler antes de redigir qualquer secao.

Meta de extensao: 5 laudas, relaxado. Piso 4, teto o que o conteudo pedir.
Orcamento: ~750 palavras por lauda em A4 duas colunas 10 pt; figura ou tabela conta 150-250.
  5 laudas = ~3750 equivalentes. Com 5 figuras/tabelas (~1000), sobram ~2700 palavras de prosa.
  Distribuicao proposta, em palavras de prosa:
    resumo 200 | introducao 500 | principio 700 | metodo 350 | resultados 750 | consideracoes 200
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
-->

# Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele

<!--
Titulo: objeto + problema + solucao, tom didatico, sem promessa de melhoria. Maximo 3 linhas. Candidatos:
- Transmissão de dados por som audível entre dois computadores: o canal acústico medido e um modem para ele
- Um modem acústico com placa de som e microfone: da modulação binária ao M-ário com correção de erros
- Enlace de dados pelo ar audível: o que o canal faz com o sinal e o que se fez a respeito
Elementos: audivel; placa de som e microfone de prateleira; canal medido; M-ario; correcao de erros.
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
Cinco frases, conceitual ate a ultima, so ela com numeros (estilo.md, secao 9). Ordem:
1. O que o artigo apresenta: a implementacao das camadas fisica e de enlace de um modem que envia bytes como som
   pela placa de audio e os recupera do outro lado, expondo o canal acustico a aplicacao como porta serial virtual,
   com hardware que toda maquina ja tem; situado entre os outros meios (cabo, radio, infravermelho) como o de menor
   exigencia de hardware e menor taxa.
2. O problema / contraste: a camada Bell 202 a 1200 baud nunca entregou uma mensagem no enlace real; canal em pente,
   limitador de saida, decisao por sinal.
3. A solucao, camada a camada: na fisica, um tom por vez entre dezesseis, decisao pelo piso de ruido de cada tom,
   sincronismo de simbolo; no enlace, bloco com codificacao convolucional K=7 e Viterbi de decisao suave, palavra de
   sincronismo por correlacao, e a transferencia de arquivo, que quebra o arquivo em pacotes numerados com CRC e
   reenvia o pacote que nao chega, ate um limite de tentativas; sem recuperacao de portadora, sem equalizador, sem
   estimador de canal.
4. A implementacao: duas maquinas, carga conhecida gerada dos dois lados, gravacoes pontuadas offline.
5. Resultados com numeros-chave: ~11,3 B/s com 12 de 12 blocos; arquivo de 1334 bytes em 21 de 21 pacotes sem
   retransmissao; e a observacao de que a linearidade da cadeia analogica pesou mais que qualquer mudanca no codigo.
Origem: CLAUDE.md (tabela de camadas), resultados/14-FEC-REP, resultados/15-PKT-ARQ.
-->

Resumo por redigir.

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
P2  A heranca telefonica: AFSK Bell 202 (1200 baud, 1200/2200 Hz), discriminador delay-and-multiply, UART 8N1.
    Funciona no fio. Frase curta que crava: no ar, o canal nao e um fio.
P3  O que o ar faz com o sinal: resposta em pente (vizinhos a 50 Hz diferem 13-18 dB), banda util 550-3500 Hz,
    limitador do alto-falante, sem reverberacao mensuravel. Ultrassom fora do alcance destes transdutores.
    Citacoes de canal acustico em ambiente fechado.
P4  O que se faz nesse canal: OFDM acustico, chirp, MFSK, em geral com equalizador ou estimativa de canal.
    Aglomerado. Sem contraste de merito: sao as ferramentas do campo, e este trabalho usa as mais simples delas.
P5  O caso: duas maquinas de prateleira numa sala, sem nada a instalar, que precisam trocar poucos bytes com
    confianca. O que o caso pede: decisao insensivel ao ganho (o canal e um pente), erro reparavel onde cai
    (10-25% dos bits chegam errados), e um jeito de medir sem que a sala entre na medida.
P6  Em primeira pessoa, "apresentamos": a implementacao das camadas fisica e de enlace. (a) o canal medido, (b) a
    camada fisica, com as tres modulacoes experimentadas no mesmo enlace e o sincronismo de simbolo, (c) a camada de
    enlace, com o bloco codificado e a transferencia de arquivo em pacotes com reenvio do que nao chega, (d) o metodo de medicao com gravacoes e pontuacao
    pareada, (e) o que a bancada ensinou sobre a cadeia analogica. Acima das duas, a aplicacao ve uma porta serial. Fecha com uma linha
    anunciando a verificacao: duas maquinas, um arquivo inteiro pelo ar.
-->

## 2 PRINCÍPIO DE FUNCIONAMENTO

<!--
Mecanismo em palavras antes de qualquer equacao. Cada equacao: frase fechada antes, "Nela," depois, leitura
fisica, gancho para o resultado que a mede. Orcamento ~700 palavras. Subsecoes abaixo.
Figura 1 candidata: diagrama do enlace (bytes -> modulador -> ar -> demodulador -> bytes).
-->

### 2.1 O canal medido

<!--
O canal primeiro, porque tudo o que segue e resposta a ele.
- Como se mediu: tom a tom (tonef + meas), nao por varredura; mediana de tres repeticoes. A varredura errou
  (1700 Hz a -27 dB na varredura, +50 dB no tom parado). resultados/02-LVL-TONE, 03-CH-CHIRP.
- O que se mediu: banda util 550-3500 Hz; acima de 4 kHz SNR cai (12 dB a 4000, 8 a 4500, ~0 a 5000);
  pente com 13-18 dB entre vizinhos a 50 Hz; sem cauda de reverberacao, o sinal para no piso de ruido.
- Consequencia de projeto, frase curta: um tom pode cair num nulo; a decisao nao pode depender da amplitude
  absoluta de um tom.
Figura 2 candidata: resposta em frequencia medida, com os 16 tons marcados sobre o pente.
-->

### 2.2 Camada física

<!--
Tres modulacoes, uma por paragrafo, na ordem em que foram experimentadas; depois o sincronismo de simbolo.
- Bell 202: bandpass, x[n]·x[n-D], lowpass, bit pelo sinal, bytes em 8N1. Sem portadora recuperada. Qualquer
  inclinacao do canal enviesa toda decisao no mesmo sentido; squelch quadratico. Nunca entregou uma mensagem no ar.
  Equacao (1) candidata: saida do discriminador e D = fs/(4 f_c).
- MFSK votado, 100 baud: cinco pares de tons a 200 Hz, um voto por par, maioria decide; ganho cancela
  (identico de x2 a x0,001). Polaridade alternada ao longo da banda para que ambos os simbolos tenham a mesma
  frequencia media. Acorde de cinco divide a amplitude por cinco, 14 dB a menos por tom.
  ~1,8 B/s, 4 de 4. resultados/05-MFSK-VOTE, 06-MFSK-PAR.
- M-ario 16 tons: um tom por vez, quatro bits por simbolo, Gray entre vizinhos; cada tom dividido pelo seu piso
  corrente (silencioso 15 simbolos em 16, entao o piso e mesmo o ruido). Recebe 0,14 rms onde os acordes
  recebiam 0,07-0,09. Guarda de 35% do simbolo. resultados/07-MARY-BASE, 11-MARY-CHORD.
  Equacao (2) candidata: pontuacao do tom k = E_k / piso_k, decisao argmax.
- Frase curta: a modulacao M-aria existe por potencia, e foi a maior alavanca que esta bancada mediu.
- Sincronismo de simbolo: gate early/late guiado por contraste, e a alternativa de duas varreduras de 80 ms
  bracketing o quadro, com periodo medido entre elas (479,96 ± 0,07 amostras onde o nominal e 480).
  Ordenar por posicao, nao por altura: a varredura de tras ganhou 4 vezes em 8. resultados/12-13-SYNC.
  Equacao (3) candidata: periodo medido = (n2 - n1) / simbolos do quadro.
-->

### 2.3 Camada de enlace

<!--
- Por que: o enlace entrega 10-25% dos bits errados; CRC so relata o dano; sem 8N1 dentro do bloco nao ha o que
  deslizar (um bit de start errado destroi o resto do fluxo; bloco fixo nao tem isso).
- O que: convolucional K=7, Viterbi de decisao suave (LLR que o demodulador ja computava e descartava),
  entrelacamento, repeticao r, palavra de sincronismo de 31 bits (m-sequencia) achada por correlacao, nunca por
  contagem de simbolos. Tabela candidata: taxa de erro tolerada por variante (hard 8%, soft 8%, 1/3 soft 13%,
  1/3 x2 25%), da simulacao contra erros de bit; declarar que e simulada.
- Transferencia de arquivo: o arquivo e quebrado em pacotes de tamanho
  fixo, cada um com byte de sincronismo, numero de sequencia, comprimento e CRC-16 (cabecalho de 3 bytes, cauda
  de 2). O receptor pede um pacote, confere o CRC e, se o pacote nao chega ou chega errado, pede de novo, ate um
  limite de tentativas por pacote (4 na bancada); so entao desiste. Pare-e-espere dirigido pelo receptor, com o
  transmissor sem estado. Por que pacotes: o modem derruba bytes, nao so os corrompe, e um byte perdido desloca tudo
  o que vem depois; o pacote e a unidade que se confere e se reenvia, e um pacote perdido custa um reenvio, nao o
  arquivo. Tamanho do pacote: 32 bytes de carga na camada sem codigo (16-24 bytes recuperaram 91% dos pacotes onde
  64 recuperaram 50%, na sala reverberante); 64 e 128 sobre o bloco codificado. A redundancia do bloco e um parametro
  do enlace acertado entre os dois lados. Fonte: xfer.py (docstring e constantes), recvfile.py, resultados/15-PKT-ARQ.
- Acima: a aplicacao ve uma porta serial virtual.
Gancho: a tabela de resultados mostra o que o bloco e o pacote recuperam.
-->

## 3 MÉTODO DE MEDIÇÃO

<!--
Por que uma secao propria: julgar uma ideia transmitindo mede a ideia e a sala ao mesmo tempo, e a sala nao para.
Orcamento ~350 palavras.
- Duas maquinas; carga conhecida gerada dos dois lados a partir de uma semente, so o ar carrega os bytes
  pontuados. O canal de controle da bancada nao entra no artigo (decisao do autor, 2026-09-05).
- Gravacao do lado remoto transmitindo carga conhecida (WAV float + JSON), pontuacao offline; um canal fixo permite
  comparar variantes sobre os mesmos segundos de ar. Pontuacao com alinhamento tolerante (SequenceMatcher,
  autojunk desligado): o enlace derruba bytes, nao so os corrompe.
- Regra da regua unica: acuracia de bit sempre no melhor deslocamento, blocos inteiros como o numero honesto
  separado. Comparacao pareada sobre a mesma gravacao, nunca duas medias.
- Calibrar ganho numa rajada, nao num tom: transientes de troca de tom carregam 2,5x o pico do tom parado.
- Uma campanha por eixo, com cabecalho do commit e das condicoes (study.py). O que foi degradado de proposito e dito.
Figura 3 candidata: foto/diagrama da bancada de duas maquinas, alto-falante e microfone.
Tabela 1 candidata: parametros do enlace (fs, baud por camada, tons, K, r, tamanho de bloco, ganho, guarda).
-->

## 4 RESULTADOS EXPERIMENTAIS

<!--
Ordem: identificacao (o que o canal e, o que a cadeia analogica fazia), depois operacao (camadas, redundancia,
sincronismo, arquivo). Cada paragrafo com a celula: Figura N mostra + condicao + numero ± + previsto vs medido +
causa + o que passou a alimentar. Orcamento ~750 palavras.

4.a Nivel e saturacao. O sinal de que a cadeia comprime: ganho digital MENOR ganha. A->B a ganho 0,5 fixo,
    alto-falante 1,00 / 0,45 / 0,20 / 0,10: 82,3% / 85,1% / 88,0% / 82,2% de bits, blocos 0/3, 0/3, 3/3, 1/3.
    U invertido com joelho em 0,20. A inversao do ganho digital em 0,45 (81,4% a 1,0 contra 89,1% a 0,25, picos
    recebidos so 0,10-0,19) some em 0,20. Levou A->B de 0 de 12 a 8 de 9. resultados/17-SPK-LEVEL-A2B, 16-SPK-A2B.
    Frase curta: e a alavanca analogica, e custa seis ensaios para ler.
    Figura 4 candidata: bits certos e blocos contra nivel do alto-falante.
4.b As tres camadas no mesmo enlace. Tabela 2: camada | taxa | medido no ar (Bell 202 nunca; MFSK 1,8 B/s 4/4;
    paralelo 5,9 B/s 5/9; M-ario rep 2 gain 0,5 9,4 B/s 9/11; M-ario rep 1 cadeia linear 11,3 B/s 12/12).
    Ligar cada linha a camada da 2.2.
4.c Redundancia. Cadeia saturada: rep 1 0/6 e 1/6, rep 2 2/6 e 5/6, rep 4 4/7. Cadeia corrigida, 48 bytes, quatro
    gravacoes por ponto: rep 1, 2 e 4 todos 4 de 4, a 11,3 / 6,7 / 3,7 B/s. Redundancia comprava a cauda, nao a
    media (um rep 4 leu 64% dos bits e entregou o bloco). resultados/14-FEC-REP.
4.d Sincronismo. Oito gravacoes: gate 87,7% e 5/8; melhor deslocamento (oraculo) 89,3% e 7/8; varredura da frente
    88,4% e 8/8; duas varreduras com periodo medido 89,0% e 8/8. O gate nao e ruim na media, colapsa
    (49,0% onde o relogio congelado leu 84,9%). Pareado: as varreduras leem mais bits em 59 de 60.
    resultados/12-13-SYNC. Dizer que parte disso foi na auto-captura Bluetooth, canal diferente.
4.e Arquivo inteiro. testcard.bmp, 1334 bytes, 21 de 21 pacotes de 64 bytes sem retransmissao a 6,8 B/s; 11 de 11
    a 7,2 B/s com 128 bytes (3 retransmissoes). Pacote maior amortiza o preambulo e falha mais; quase empata.
    Antes entregava 1 de 21 com pacotes de 81 bytes, e nada na quebra em pacotes ou no reenvio mudou: a correcao
    analogica. resultados/15-PKT-ARQ. Frase: o reenvio converge so quando a taxa de erro por pacote e baixa o
    bastante; zero retransmissoes em 21 e resultado forte, mas nao mede essa taxa com precisao, so diz que e baixa.
4.f O que nao ajudou e o que ficou fora: marygap, maryband, marychord (custam ou nao medem nada); piloto por tom
    morto; a correcao do estimador de piso, boa na cadeia distorcida e pior na linear (0 de 3 contra 2 de 3),
    ainda nao no ar. Cada um com o numero e a pasta. Curto.
-->

## 5 CONSIDERAÇÕES FINAIS

<!--
Tres paragrafos, sem numero novo, os mesmos do resumo.
1. O que se apresentou e o mecanismo: um tom por vez dividido pelo proprio piso, codigo convolucional suave,
   sincronismo por correlacao; nada de estimador de canal.
2. O que a estrutura fez: 11,3 B/s a 12 de 12; arquivo inteiro 21 de 21; e a observacao de que a linearidade da
   cadeia pesou mais que qualquer mudanca de codigo, nas duas direcoes do enlace.
   Situar de volta entre os meios: taxa de um teclado lento, hardware de qualquer maquina, para o caso descrito.
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
- Bell 202 / AFSK e discriminador (P2)
- canal acustico em ambiente fechado, resposta em pente (P3)
- OFDM/chirp/MFSK acusticos com equalizacao (P4)
- codigos convolucionais, Viterbi de decisao suave (2.3)
- m-sequencias / palavra de sincronismo (2.3)
-->
