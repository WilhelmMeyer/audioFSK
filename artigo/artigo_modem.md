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

ESTADO DO TEXTO (2026-09-07, depois do merge das duas maquinas). O artigo esta sendo montado de tras
  para frente, comecando pelos RESULTADOS, com o que existe em ../resultados/. Cada figura mora na pasta da
  campanha que a gerou; artigo/figuras/ recebe copia para a montagem.
  SECOES 1 e 2: as desta maquina, reescritas em 2026-09-07 por decisao do autor, e mantidas no merge no
  lugar dos tocos "a redigir depois dos resultados" da versao remota. A 1 fala so de FSK, Bell 202, HART e
  transmissao por som, com quatro fontes lidas em PDF. A 2 tem 2.1, o meio, e 2.2, as quatro formas; a 2.3
  foi recolhida e o texto dela esta no comentario da 2.2.
  SECAO 4: a versao remota, redigida do fim para o comeco, com tres figuras que moram nas pastas 01, 02 e
  03 do sentido A2B.
  SECOES 3 e 5: como a versao remota as deixou, a redigir.
  ATENCAO: ha contradicoes abertas entre a 2.1 e a secao 4, listadas no comentario da 2.1. Resolver antes
  de montar.
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
Refeita 2026-09-07. Escopo estreitado por decisao do autor: a introducao fala SO de FSK, Bell 202,
protocolo industrial HART e transmissao de dados por som. Saiu a comparacao entre cabo, radio,
infravermelho e som, e saiu com ela a Tabela 1, que existia so para aquela comparacao. Saiu tambem o
paragrafo de OFDM e chirp, que apresentava ferramentas do campo nao usadas aqui.
Cinco paragrafos: o que e FSK e o que o Bell 202 fixa; o Bell 202 vivo, no HART; o mesmo principio no
ar; o que o ar cobra; o que apresentamos.
Uma frase de cada artigo, e as quatro fontes foram LIDAS no PDF, nao no resumo:
  P1 FINNEGAN e BENSON (2014), p. 2: "The Bell 202 protocol is an audio frequency shift keyed (AFSK)
     modulation that encodes data by shifting between 1200Hz and 2200Hz audio tones. These tones
     represent a binary one and zero respectively and transitions occur at a rate of 1200 symbols per
     second. Originally developed by AT&T for use on the telephone network".
  P2 WU (2023), p. 2 e 4: "a backward-compatible enhancement to 4-20 mA instrumentation that allows
     two-way communication with smart, microprocessor-based field devices"; "The standard HART
     transmission is a frequency shift keyed (FSK) signal superimposed on the 4-20mA signal. The FSK
     bits are transmitted at 1200 bits per second"; a figura 1-3 marca 1200 Hz em "1" e 2200 Hz em "0",
     o que encerra a divergencia com as fontes secundarias que dizem 2400 Hz.
  P3 LOPES e AGUIAR (2001), p. 1: "Inter-machine communications have always been kept away from our
     own communication channel, audible sound in air. There are good reasons for this: the data rates
     are relatively low when compared to other media (e.g. electric wires, radio) and the sounds tend to
     be annoying. But as more and more devices support an audio channel for voice or music, that
     channel becomes a cheap option for transferring arbitrary information among devices that happen
     to be near each other."
  P4 PUTZ et al. (2026), p. 2: "sound waves travel more than 87 000 times slower than electromagnetic
     waves, leading to delay spreads on the order of tens of milliseconds"; e "Commercial products for
     acoustic data transmission on smart devices typically achieve only 10-200 bps"; a revisao e de 31
     estudos com mais de 11000 transmissoes.
P5 nao cita: e o que fizemos. Nenhum numero desta bancada entra aqui; ficam na secao 4.
NUMERACAO DE TABELA: a Tabela 1 saiu, entao a antiga Tabela 2 vira Tabela 1 e assim por diante. Nao
renumerei porque as secoes 3 a 5 estao em merge com a versao remota; renumerar depois do merge.
-->

A modulação por chaveamento na frequência, do inglês *frequency shift keying* (FSK), põe dados num canal de voz comutando a portadora entre duas frequências, uma para cada valor do bit. O padrão Bell 202 fixa essas duas frequências em 1200 e 2200 Hz, com transições a 1200 símbolos por segundo, e foi desenvolvido pela AT&T para a rede telefônica (FINNEGAN; BENSON, 2014). Um canal projetado para conduzir voz passa a conduzir bytes sem que nada no meio precise mudar.

O Bell 202 não é peça de museu. O protocolo de transdutor remoto endereçável em barramento, do inglês *Highway Addressable Remote Transducer* (HART), superpõe um sinal FSK de 1200 bits por segundo à malha de 4 a 20 mA que liga o transmissor de campo ao sistema de controle, sem perturbar o valor analógico que ela já carrega (WU, 2023). A retrocompatibilidade é o que o difundiu, pois o instrumento antigo filtra o sinal digital e continua medindo como antes.

O mesmo princípio vale no ar, e Lopes e Aguiar (2001) já observavam por que quase ninguém o usa assim. A comunicação entre máquinas sempre foi mantida longe do som audível por duas boas razões, a taxa baixa diante do fio e do rádio e o incômodo do som. A contrapartida é que o canal de áudio existe em cada aparelho, o que o torna uma opção barata de transferir informação entre dispositivos próximos, sem instalar nada.

O ar, porém, não é o par de fios. O som viaja mais de 87000 vezes mais devagar que a onda eletromagnética, de modo que as reflexões da sala se espalham por dezenas de milissegundos, e o multipercurso em ambiente fechado é a maior degradação dos esquemas acústicos publicados (PUTZ *et al.*, 2026). Na mesma revisão, de 31 estudos e mais de 11000 transmissões em aparelhos reais, os produtos comerciais entregam de 10 a 200 bits por segundo, que é a ordem de grandeza a esperar do meio.

Apresentamos um modem acústico que leva bytes de um computador a outro por som audível, com alto-falante e microfone comuns, e que se expõe à aplicação como uma porta serial. Partimos das duas frequências do Bell 202 e chegamos a dezesseis tons com correção de erros, porque cada forma anterior falhou no ar por uma razão que medimos. Verificamos o conjunto entre duas máquinas na mesma sala, transferindo um arquivo inteiro pelo ar.

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
Numeros do pente recalculados a 50 Hz sobre a varredura A->B: degrau entre vizinhos com mediana 2,5 dB,
p90 6,5 dB, maximo 13,0 dB; excursao de 27,6 dB dentro de 550-3500 Hz; os 16 tons caem entre -5,7 e
-27,8 dB. O "13 a 18 dB" anterior valia como maximo e exagerava cinco vezes como faixa tipica.

AMPLIADA e depois ENCURTADA DUAS VEZES em 2026-09-07, a pedido do autor: 822 palavras, depois 649, agora
cerca de 495, contra 596 antes da ampliacao. Criterio: fica o que o leitor precisa para entender o canal,
sai o que so defende a metodologia, recapitula o que ja foi dito ou responde pergunta que ninguem fez.
O QUE FOI CORTADO, para nao ser reescrito por engano:
  - o paragrafo do ultrassom, com a banda de 22 kHz e os 4 kHz do modo inaudivel. Sobrou uma oracao, no
    paragrafo da SNR, porque a regra de estilo exige dizer o que ficou fora e com que razao. Com ele saiu
    a citacao de PUTZ et al. 7.3.3, sobre seletividade na banda quase-ultrassonica.
  - a discordancia entre as duas varreduras. E defesa de metodo, nao entendimento do meio; fica no
    comentario acima, que e onde ela importa.
  - os 30 dB SPL de dispersao entre modelos, de PUTZ et al. 7.3.2, de proposito: os demais decibeis desta
    secao sao amplitude de amostra em gravacao, medida relativa, e os 30 dB deles sao nivel de pressao
    sonora. Duas reguas na mesma unidade e no mesmo paragrafo confundiriam.
  - a condicao exata da interferencia ("o periodo cabe um numero inteiro de vezes na diferenca de
    percurso"). O leitor precisa saber que somam ou se cancelam conforme a frequencia; a condicao exata
    e verdadeira e nao muda nenhuma decisao do projeto.
  - as oracoes "porque..." das tres exigencias, que repetiam o que os paragrafos anteriores acabaram de
    dizer. A regra do autor manda cortar recapitulacao.
  - "cada uma das tres faltas cobra um preco diferente", da abertura, que e meta-discurso.
  - a FIGURA 1 INTEIRA, por decisao do autor em 2026-09-07: nada de imagem nesta secao. O numero que ela
    carregava sobreviveu na prosa, que e a excursao de 22 dB entre o tom mais forte e o mais fraco. Saiu
    com ela a unica imagem existente no artigo; as Figuras 2 a 5 nunca existiram como arquivo, e seguem
    citadas na prosa das secoes 2.2, 3 e 4, que nao foram alteradas aqui.
    O arquivo figuras/resposta-canal.png e o figura_canal.py que o gera ficaram sem uso. NAO foram
    apagados: a decisao de remove-los do repositorio e do autor, e o script ainda documenta como a
    varredura foi repontuada.
Tres citacoes sobreviveram, todas de PDF lido: LOPES e AGUIAR (2001) no pente, PUTZ et al. (2026) no eco
e no estouro. As frases exatas de origem estao em referencias.md.
O eco continua entrando como PROPRIEDADE DO MEIO e o paragrafo fecha pela negativa, dizendo que esta sala
nao tem cauda mensuravel. Nao virou dificuldade vencida, que os resultados desmentiriam.

=== CONTRADICOES COM A SECAO 4, ABERTAS NO MERGE DE 2026-09-07 ===
A secao 4 chegou da outra maquina, redigida do fim para o comeco sobre as pastas de resultados/, e discorda
desta 2.1 em quatro pontos. O autor decidiu manter as duas como estao e acertar depois. Listadas aqui para
serem achadas; NAO corrigir sem decisao do autor, porque cada uma pode cair para qualquer um dos lados.

1. A CAUDA, e esta e a grave. A 2.1 diz "nesta bancada a cauda nao e mensuravel, o sinal para no piso de
   ruido". A secao 4 mediu o contrario: "o nivel nao cai de uma vez e sim cerca de 50 dB ao longo de meio
   segundo", e dedica um paragrafo a ela. A secao 4 tambem e honesta sobre a origem, dizendo que uma
   gravacao so nao separa a reverberacao da sala do comportamento da caixa sem fio e do codec dela. Do
   jeito que esta, o artigo afirma e nega a mesma coisa em duas secoes.
2. BANDA 550-3500 Hz E O DESCARTE DO ULTRASSOM. O comentario da secao 4 diz que ambos ficaram de fora "por
   falta de lastro", herdados de uma medicao tom a tom que nunca virou pasta. A 2.1 continua afirmando os
   dois, e o ultrassom ocupa um paragrafo inteiro dela.
3. EXCURSAO DE NIVEL NA BANDA. A 2.1 diz 28 dB entre o melhor e o pior ponto, em bins de 50 Hz na faixa de
   550 a 3500 Hz. A secao 4 diz 23,7 dB, em passos de 74 Hz na faixa dos dezesseis tons. Sao medidas
   diferentes e podem conviver, mas o leitor ve dois numeros para a mesma ideia sem saber que reguas mudam.
4. DEGRAU ENTRE VIZINHOS. A 2.1 da mediana 2,5 dB e maximo 13 dB a 50 Hz de resolucao; a secao 4 da "ate
   9,4 dB entre pontos vizinhos" a 74 Hz. Mesmo caso do item 3.

E uma omissao, que nao e contradicao: a secao 4 mostra que o PISO DE RUIDO nao e plano, se concentra abaixo
de 2 kHz e cai cerca de 25 dB entre 2000 e 2900 Hz. A 2.1 so diz que o canal "nao e silencioso". Se a 2.1
sobreviver como esta, vale uma frase dizendo que o ruido tambem tem forma. -->


Transmitir pelo ar é converter a sequência de amostras em variação de pressão, deixá-la atravessar a sala a 343 m/s e reconvertê-la em amostras do outro lado. Entre um conversor e outro estão o amplificador, o alto-falante, o ar, as superfícies que refletem e o microfone. Esse canal não é plano, não é linear e não é silencioso.

O ruído do ambiente ocupa parte significativa da mesma banda, vindo do tráfego, de máquinas, da fala e do próprio manuseio dos aparelhos, em componentes tanto contínuos quanto em rajada (PUTZ *et al.*, 2026).

Um alto-falante e um microfone de uso geral respondem bem na banda da fala e perdem eficiência nos extremos. Colocamos os tons entre 550 e 3500 Hz, onde a resposta medida varia 28 dB entre o melhor e o pior ponto. Acima disso o nível cai de 12 a 20 dB.

O ultrassom atrai porque a sala fica silenciosa acima da banda da fala e a transmissão não incomoda quem está por perto. A amostragem usual de 44,1 ou 48 kHz fecha a banda abaixo de 22 kHz, exigir inaudibilidade a reduz a menos de 4 kHz, e nessa faixa o hardware de áudio é fortemente seletivo (PUTZ *et al.*, 2026). A absorção do ar cresce com a frequência e encurta o alcance, e por isso o ultrassom fica fora deste trabalho.

Dentro da banda o sinal chega ao microfone pelo caminho direto e pelas reflexões nas superfícies da sala, cada uma atrasada pelo percurso que fez. Uma cópia atrasada reforça o som direto nas frequências cujo período cabe um número inteiro de vezes na diferença de percurso, e o cancela naquelas em que essa diferença vale meio período. Como a condição depende da frequência, a resposta do canal é um pente de máximos e nulos alternados, e a geometria da sala fixa o espaçamento entre eles.

O degrau entre vizinhos a 50 Hz de resolução tem mediana de 2,5 dB e chega a 13 dB, e a posição dos nulos muda quando alguém se move. Lopes e Aguiar (2001) já apontavam essas reflexões como a razão de não se confiar em muitos níveis de amplitude no ar.

As mesmas reflexões, vistas no tempo, são a reverberação. Depois que a fonte cala o som persiste enquanto as ondas ainda percorrem a sala perdendo energia a cada superfície, e enquanto essa cauda dura a energia de um símbolo invade o seguinte. Em ambiente fechado o espalhamento chega a dezenas de milissegundos, absorvido por intervalo de guarda (PUTZ *et al.*, 2026). Nesta bancada a cauda não é mensurável, mas o projeto a antecipa porque outra sala pode tê-la.

A cadeia analógica também não é linear. O cone do alto-falante tem excursão limitada e o amplificador, tensão limitada, então os picos são achatados quando o nível cresce, e o microfone comprime do mesmo modo na outra ponta. A energia retirada dos picos reaparece como harmônicos e intermodulação, parte deles dentro da própria banda de trabalho, onde nenhum filtro os separa do sinal. Passado esse ponto, subir o nível piora a recepção.

O estouro não é particularidade desta bancada. Putz *et al.* (2026) mediram distorção não linear na maioria dos aparelhos acima de cerca de 75% do volume máximo, num enlace de mão única, sem realimentação que corrija o ganho.

Disso decorrem duas exigências. A decisão do receptor não pode depender da amplitude absoluta de nenhum tom, e o nível de operação tem de ser encontrado por medição.

### 2.2 As quatro formas de transmissão

<!--
REESCRITA 2026-09-07, a pedido do autor: descrever melhor o nosso trabalho, como modulamos e como
detectamos cada uma das quatro formas. Titulo novo; era "Modulacao", que nao dizia que a secao e sobre
as quatro formas que construimos. O termo "quatro formas de transmissao" e o vocabulario ja fixado no
CLAUDE.md desta pasta.
A 2.3, "Sincronismo e correcao de erros", foi RETIRADA por decisao do autor em 2026-09-07, "por
enquanto". O texto dela esta preservado no fim deste comentario, para voltar sem ser reescrito.

NUMEROS CONFERIDOS NO CODIGO EM 2026-09-07, nao no CLAUDE.md:
  2-FSK: MARK 1200 Hz, SPACE 2200 Hz, 1200 baud, 8N1; deteccao por atraso e produto, atraso de um
    quarto de periodo em 1700 Hz; fase continua entre simbolos.
  5x2-FSK: MFSK_PAIRS = (700,900) (1320,1120) (1540,1740) (2160,1960) (2380,2580), 200 Hz dentro de
    cada par, 100 baud. Polaridade alternada conferida par a par: nos pares 0, 2 e 4 o tom grave e o
    bit 0; nos pares 1 e 3 e o bit 1. Media dos acordes recalculada aqui: 8100/5 = 1620 Hz para o
    acorde do bit 0 e 8300/5 = 1660 Hz para o do bit 1, o que confirma o CLAUDE.md.
    MFSK_PRESENCE_MIN = 1.3.
  16-FSK: MARY_TONES, dezesseis tons de 888 a 3325 Hz; espacamento conferido, 162 Hz constante
    (1050-888 = 162, 3325-3162 = 163 por arredondamento). MARY_BITS = 4, codigo Gray, 100 baud.

CORRECAO, e ela vale para o CLAUDE.md da raiz tambem: O INTERVALO DE GUARDA E 15%, NAO 35%.
  O padrao entregue e guard=0.15 em MFSKDemodulator (linha 397) e MaryDemodulator (linha 796), e o
  descarte e no INICIO do simbolo, np.arange(self.guard, samples_per_symbol).
  Os 35% aparecem em dois lugares e nenhum e o caminho vivo: loopback_test.py linha 119, num caso
  deliberadamente ajustado para reverberacao ((0.35, 0.15, True)), e console.py linha 605, numa
  varredura de diagnostico que repontua audio guardado. O CLAUDE.md da raiz descrevia o caso de teste
  como se fosse o comportamento entregue, e a versao anterior desta secao repetia o erro; os dois
  CLAUDE.md foram corrigidos em 2026-09-07 e agora dizem 15%.

O marcador "(CITAR: modulacao M-FSK, deteccao nao coerente)" foi retirado: pela decisao de escopo do
autor, a literatura serve a introducao e a 2.1, e daqui para a frente o texto se sustenta no que
construimos e medimos. PROAKIS e SALEHI (2008) continua levantado em referencias.md, grupo G5, se o
autor quiser citar livro-texto para o principio M-ario.
A remissao "A Figura 2 mostra o espectro de cada uma" tambem saiu, porque nao ha figura no artigo.

TEXTO DA 2.3 RETIRADA, para restaurar quando o autor pedir:
  "O bloco e localizado por uma palavra de referencia de 31 bits, correlacionada sobre as LLR
  recebidas, nunca por contagem de simbolos, pois o gate consome numeros diferentes de amostras por
  simbolo enquanto ajusta. E a mesma correlacao que resolve o alinhamento de nibble da 16-FSK, em que
  um simbolo a mais antes do bloco troca os nibbles de todos os bytes. Acima do bloco, o arquivo vai
  em pacotes com numero de sequencia, comprimento e CRC-16, reenvio pare-e-espere dirigido pelo
  receptor, transmissor sem estado. A aplicacao ve uma porta serial virtual."
-->

Chamamos M-ária a modulação de ordem $M$, em que cada símbolo é um tom escolhido entre $M$ frequências e carrega $\log_2 M$ bits, e a taxa de bits é o produto de (1).

$$R_b = R_s \log_2 M \tag{1}$$

Nela, $R_b$ é a taxa de bits, $R_s$ é a taxa de símbolos em bauds e $M$ é o número de frequências. Subir $M$ é o caminho para subir $R_b$, com a taxa de símbolos presa pela banda e pelas reflexões. Construímos quatro formas, e o que muda entre elas é quanto a decisão depende da amplitude. Elas ocupam as duas famílias que Lopes e Aguiar (2001) já haviam formulado, a de um tom por símbolo e a de $k$ tons simultâneos.

A 2-FSK usa os dois tons do padrão Bell 202, 1200 e 2200 Hz, a 1200 símbolos por segundo, com os bytes em 8N1 e fase contínua na troca de tom.

O demodulador multiplica o sinal filtrado por uma cópia atrasada de um quarto de período em 1700 Hz, e a média do produto muda de sinal conforme o tom presente. O limite é o limiar, pois um canal que atenue um tom mais que o outro enviesa toda decisão no mesmo sentido.

A 5×2-FSK votada troca o limiar por comparação. Cinco pares de tons carregam o mesmo bit a 100 símbolos por segundo, com 200 Hz dentro de cada par, e cada par vota no tom que chegou mais forte. Como o voto é uma razão, multiplicar o sinal por qualquer fator não muda o resultado.

A polaridade alterna ao longo da banda, de modo que os dois acordes ficam com frequência média quase igual, 1620 e 1660 Hz, e um canal inclinado não favorece nenhum bit. Um segundo critério exige que a razão entre vencedor e perdedor passe de 1,3, sem o que o ruído elegeria um bit em sala vazia.

A 5×2-FSK multicanal usa os mesmos dez tons com um bit distinto em cada par, cinco bits por símbolo. O limite das duas formas de cinco pares é potência, pois o pico que o alto-falante aceita é fixo e cada um dos cinco tons sai 14 dB abaixo do que sairia sozinho.

A 16-FSK devolve essa potência. São dezesseis tons de 888 a 3325 Hz, espaçados 162 Hz, e exatamente um soa por vez, quatro bits por símbolo, com vizinhos em código Gray para que a confusão do canal custe um bit e não quatro.

A tarefa do detector é decidir quais frequências estão presentes, sem informação de fase (LOPES; AGUIAR, 2001). O receptor mede a energia de cada tom, divide pelo piso corrente daquele tom e elege o maior, conforme (2).

$$\hat{s} = \arg\max_k \frac{E_k}{P_k} \tag{2}$$

Nela, $E_k$ é a energia no tom $k$ e $P_k$ é a média corrente dessa energia. Como cada tom fica em silêncio quinze símbolos em dezesseis, essa média é o piso de ruído naquela frequência, e um tom caído num nulo passa a ser comparado com o próprio nulo.

As três formas de 100 bauds compartilham o relógio de símbolo, ajustado por um gate de adiantamento e atraso, e descartam os primeiros 15% de cada símbolo como guarda. A transmissão abre com preâmbulo alternado, que dá ao gate transições para travar, e fecha com cauda ociosa.

## 3 MÉTODO DE MEDIÇÃO

<!-- A redigir depois dos resultados. -->

## 4 RESULTADOS EXPERIMENTAIS

<!--
Redigido a partir de 2026-09-07, do fim para o comeco. Campanhas escolhidas com o autor: 01, 02 e 03 para o
canal; 04, 05, 06 e 07 para as quatro formas; 07 para linearidade; 08 para ganho; 11 para potencia; 12-13
para deriva de relogio e quadro longo; 14 para redundancia; 15 para arquivo; 08-A2B, 16 e 17 para as duas
direcoes. Prosa propositalmente longa nesta fase; sintetizar depois.
Nenhum numero entra sem pasta. Ficaram de fora, por falta de lastro: banda util 550-3500 Hz, colapso acima
de 4 kHz e o descarte do ultrassom, todos herdados de uma medicao tom a tom que nunca virou pasta.
-->

O primeiro dado do meio é o ruído que já está na sala antes de qualquer transmissão. Medimos com o enlace inteiramente parado, quatro gravações de oito segundos pelo microfone da máquina receptora, e a Figura 1 mostra a média delas em janelas de 50 Hz. O ruído não é plano. Ele se concentra abaixo de 2 kHz, com máximos em torno de 1300 e 1500 Hz, e cai cerca de 25 dB entre 2000 e 2900 Hz.

![](figuras/piso-ruido.png "0.95")
Figura 1 - Piso de ruído do microfone receptor com o enlace parado, média de quatro gravações de 8 s em janelas de 50 Hz; a faixa cinza são os extremos entre as gravações e as marcas no rodapé são os dezesseis tons da 16-FSK. Notar que o ruído cai cerca de 25 dB entre 2000 e 2900 Hz, de modo que os tons da metade inferior da banda trabalham contra um fundo bem mais alto.

Na banda inteira esse piso fica em −52,3 dBFS e, sob os dezesseis tons, ele vai de −67,6 a −94,8 dBFS. Os tons não recebem portanto o mesmo tratamento, e a diferença é da sala e não do sistema. Um projeto que escolhesse frequências apenas pela resposta dos transdutores estaria decidindo metade da questão.

O sinal transmitido se destaca desse fundo com folga. A Figura 2 mostra o que o detector mede enquanto a máquina transmissora emite um tom de 1700 Hz, com três curvas na mesma janela e na mesma escala: as dezesseis sondas do detector durante o tom, as mesmas sondas com a sala parada, e um seno sintético de 1700 Hz analisado do mesmo jeito. O tom chega 47,4 dB acima das sondas que não receberam nada e 13,0 dB acima da segunda sonda mais alta, onde a decisão do receptor precisa de apenas 1,3 dB.

![](figuras/deteccao-tom.png "0.95")
Figura 2 - Nível nas dezesseis sondas do detector com um tom de 1700 Hz transmitido, comparado com a sala parada e com um seno sintético analisado na mesma janela. A curva sintética não passou por transdutor nem por sala, e serve de régua: o alargamento em torno do pico é da janela de análise, não do canal.

A curva do seno sintético quase se sobrepõe à medida, e isso responde uma pergunta que a figura levantaria sozinha. O pico não é infinitamente estreito, e a razão é a janela de análise, não o canal: uma janela finita espalha energia de qualquer tom pelas sondas vizinhas, e o seno sintético, que não passou por sala nenhuma, espalha do mesmo jeito. O que sobra de diferença entre as duas curvas é o que a cadeia e a sala de fato acrescentaram, e é pouco.

O comportamento ao longo da banda inteira se lê melhor com uma varredura, um tom que sobe de 300 a 6000 Hz em seis segundos, e a Figura 3 mostra a gravação dela. Três coisas aparecem ali. A primeira são as diagonais mais claras acima da varredura principal, que são o segundo e o terceiro harmônico, 30,5 e 42,2 dB abaixo da fundamental: são frequências que ninguém transmitiu e que a própria cadeia fabricou, e dentro da banda de trabalho elas são indistinguíveis de sinal. A segunda é o que acontece depois que a varredura acaba, à direita da figura, onde o nível não cai de uma vez e sim cerca de 50 dB ao longo de meio segundo. A terceira são os riscos verticais em 3,6 s e entre 4,2 e 4,4 s, que atravessam várias frequências no mesmo instante e por isso não podem ser a varredura: são sons da sala durante a gravação.

![](figuras/varredura.png "0.95")
Figura 3 - Espectrograma de uma varredura de 300 a 6000 Hz gravada pelo microfone receptor, com janela de 4096 amostras (11,7 Hz por bin). As diagonais tracejadas marcam o segundo e o terceiro harmônico gerados pela cadeia; o recorte mostra a crista contra a separação de 162 Hz entre tons vizinhos da 16-FSK; os riscos verticais em 3,6 e 4,2 s são ruído da sala, não sinal.

A cauda de meio segundo merece cuidado. O desligamento do transmissor leva 10 ms, então ela não vem dele, e uma única gravação não separa a reverberação da sala do comportamento do alto-falante sem fio e do seu codec. Registramos o que foi medido no receptor, sem atribuir a origem. Ela importa porque o intervalo de guarda descartado no início de cada símbolo existe justamente para que o final de um símbolo não seja lido junto com o começo do seguinte.

O nível ao longo da banda também não é uniforme. Na faixa ocupada pelos dezesseis tons, medida pela mesma varredura em passos de 74 Hz, o nível varia 23,7 dB entre o melhor e o pior ponto, com diferenças de até 9,4 dB entre pontos vizinhos. O som chega ao microfone pelo caminho direto e pelas reflexões nas superfícies da sala, cada uma atrasada pelo seu percurso, e cópias atrasadas somam em fase em algumas frequências e se opõem em outras. A resposta resultante alterna máximos e nulos ao longo da banda, e a posição deles depende da geometria e muda quando alguém se move.

A primeira forma de transmissão medida sobre esse canal reparte a decisão entre cinco pares de tons. Dez frequências soam ao mesmo tempo, agrupadas em cinco pares, e cada par carrega o mesmo bit: dentro do par, o tom mais forte diz qual é o bit, e a maioria dos cinco decide. A taxa é de cem símbolos por segundo, um bit por símbolo. O receptor descarta os primeiros 15% de cada símbolo como guarda e mede os 8,5 ms restantes. A Figura 4 mostra a abertura da transmissão, em que os bits se alternam, e nela os dois acordes se revezam a cada dez milissegundos.

![](figuras/5x2fsk-alternancia.png "0.95")
Figura 4 - Trecho alternado que abre a transmissão, com o espectrograma ao fundo e a leitura do receptor por cima. Cada coluna é um símbolo e cada marcador é o tom que venceu o seu par, com a forma dizendo que bit ele significa. A polaridade alterna ao longo da banda, de modo que os dois acordes ocupam frequências entrelaçadas e não metades separadas do espectro.

A polaridade alterna de propósito. Nos pares de 700, 1540 e 2380 Hz o tom mais grave significa 0, e nos pares de 1120 e 1960 Hz significa 1, de modo que os dois acordes ficam entrelaçados na banda e têm quase a mesma frequência média. Um canal que favoreça as frequências altas ou as baixas favorece igualmente os dois símbolos, e não empurra a decisão para um lado.

A Figura 5 mostra a decisão símbolo a símbolo, em dois instantes. Em cada um deles medimos a energia nas dez frequências dentro da janela de decisão, e o que decide é a comparação dentro de cada par, nunca o nível absoluto. No símbolo de cima os cinco pares votaram 0 e o bit transmitido era 0. No de baixo o bit era 1, o par de 700 e 900 Hz votou 0, e os outros quatro fizeram o bit sair certo.

![](figuras/5x2fsk-espectro-dos-acordes.png "0.95")
Figura 5 - Espectro medido na janela de decisão de dois símbolos, um com bit 0 e outro com bit 1, com as barras marcando a energia nas dez frequências que o detector compara. No símbolo de baixo o par mais grave vota contra o bit transmitido e a maioria decide mesmo assim.

Esse voto contrário não é acidente raro. Medida ao longo do bloco, a taxa de acerto de cada par isolado vai de 74,0% a 86,1%, e nenhum deles serviria sozinho. O que separa um tom presente de um ausente também não é uniforme na banda: são 8,6 a 9,0 dB nos pares do meio, contra 6,6 dB no par de 700 Hz e apenas 2,7 dB no de 2380 Hz, o que é consequência direta do piso de ruído medido na Figura 1. Reunidos, os cinco pares levam o acerto a 87,7%.

A Figura 6 mostra o mesmo mecanismo sobre os dados. São trinta símbolos consecutivos em que todos os bits saem certos, e ainda assim em vinte e dois deles ao menos um par votou contra os demais. A votação está trabalhando o tempo todo, e não apenas quando o resultado final estaria em risco.

![](figuras/5x2fsk-votacao-nos-dados.png "0.95")
Figura 6 - Trinta símbolos consecutivos da carga transmitida, com a leitura do receptor sobreposta ao espectrograma. Todos os bits saem certos; os marcadores em vermelho são os pares que votaram contra o bit transmitido, presentes em vinte e dois dos trinta símbolos.

Antes da correção de erros, 88,1% dos 2340 bits do bloco chegaram certos. Com ela, os 48 bytes enviados chegaram idênticos, sem nenhum byte errado, e a cadeia recebida é a mesma que saiu da outra máquina, `HPdp14v7rxCu9tyxbhaEWN2DnsHi4LdGhQeAN0MPo4uVpv62`.

A segunda forma de transmissão medida troca a redundância por densidade. Em vez de dez tons simultâneos carregando um bit, dezesseis frequências entre 888 e 3325 Hz se revezam, exatamente uma soando por vez, e qual delas soou nomeia quatro bits. A taxa de símbolos é a mesma, cem por segundo, mas cada símbolo vale quatro vezes mais. Frequências vizinhas recebem códigos que diferem em um único bit, porque tons vizinhos são os que o canal confunde, e assim a confusão mais provável custa um bit em vez de quatro. A Figura 7 mostra trinta símbolos consecutivos, com um único tom aceso a cada dez milissegundos.

![](figuras/16fsk-tons.png "0.95")
Figura 7 - Trinta símbolos consecutivos da carga, com o espectrograma ao fundo e o tom detectado marcado sobre cada símbolo. Um único tom soa por vez, entre os dezesseis marcados no eixo, e nos trinta símbolos deste trecho o tom detectado é o transmitido.

Com um tom por vez, toda a potência que o alto-falante aceita vai para ele. Dez tons simultâneos precisam dividir o mesmo pico, e cada um sai com uma fração dele; um tom sozinho leva o pico inteiro. É a mesma escolha de sempre entre redundância e alcance, e aqui ela aparece como quatro bits por símbolo em vez de um.

A decisão é escolher o maior entre dezesseis, e não comparar dois. Isso levanta um problema que a comparação dentro do par não tinha: um tom pode chegar forte porque foi transmitido ou porque a sala favorece aquela frequência. O receptor resolve dividindo a energia de cada tom pelo piso corrente daquela frequência antes de comparar. Como cada tom fica calado em quinze símbolos de cada dezesseis, a média de longo prazo de cada frequência é o próprio ruído naquele ponto da banda, e nunca o sinal. A Figura 8 mostra as duas grandezas em um símbolo: em cima o espectro medido e o piso de cada tom, embaixo a diferença entre os dois, que é o que decide.

![](figuras/16fsk-decisao.png "0.95")
Figura 8 - Decisão em um símbolo. Em cima, o espectro na janela de decisão, a energia medida em cada um dos dezesseis tons e o piso corrente de cada um. Embaixo, a energia de cada tom contada do próprio piso, que é a grandeza comparada; o tom transmitido, de 2512 Hz, fica 8,0 dB acima do segundo colocado.

Essa correção não é cosmética, porque o piso não é o mesmo em toda a banda. Entre o tom de piso mais alto e o de piso mais baixo há 6,9 dB de diferença, tomada a mediana ao longo do bloco, o que reproduz o ruído medido na Figura 1. Sem dividir, um tom sentado numa região silenciosa da banda concorreria em desvantagem permanente. A margem sobre o segundo colocado, no símbolo da figura, é de 8,0 dB, próxima da mediana de 7,9 dB do bloco, que varia entre 2,6 e 12,6 dB entre o primeiro e o último decil.

Falta situar cada símbolo no tempo, e as duas máquinas não compartilham relógio. A Figura 9 sobrepõe ao mesmo trecho as fronteiras que o receptor de fato usou e a grade de passo constante que o período nominal daria. As duas não coincidem. O símbolo nominal tem 480 amostras e o receptor consumiu entre 420 e 585 ao longo do trecho, com mediana em 480, e o afastamento em relação à grade regular chega a 1,88 ms, com mediana de 0,63 ms. O relógio de símbolo é recuperado do próprio sinal, símbolo a símbolo, e não contado a partir do início.

![](figuras/16fsk-enquadramento.png "0.95")
Figura 9 - O mesmo trecho, com as fronteiras de símbolo que o receptor usou e a grade de passo nominal. Acima do quadro, os quatro bits enviados em cada símbolo, já codificados e entrelaçados, e não os bytes da mensagem. As fronteiras medidas se afastam da grade regular em até 1,88 ms.

Nas três gravações desta forma de transmissão, os 48 bytes chegaram íntegros. Antes da correção de erros, o tom detectado coincidiu com o transmitido em 72,5% a 89,5% dos símbolos, e 85,2% a 94,5% dos bits chegaram certos.

## 5 CONSIDERAÇÕES FINAIS

<!-- A redigir por ultimo. Inclui a frase sobre o que ficou para a versao final por prazo, entre elas
refazer a 2-FSK na cadeia atual (ver HANDOFF.md, "O que falta medir", item 4). -->

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
