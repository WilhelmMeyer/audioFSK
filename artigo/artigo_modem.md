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

ESTADO DO TEXTO (2026-09-07): so o RESUMO se salva do rascunho anterior. As secoes 1, 2 e 3 que existiam
  foram descartadas por decisao do autor: foram escritas as pressas e nao servem de base. O artigo esta sendo
  montado de tras para frente, comecando pelos RESULTADOS, com o que existe em ../resultados/. Cada figura
  mora na pasta da campanha que a gerou; artigo/figuras/ recebe copia para a montagem.
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

<!-- A redigir depois dos resultados. -->

## 2 PRINCÍPIO DE FUNCIONAMENTO

<!-- A redigir depois dos resultados. Mecanismo, sem numero desta bancada. -->

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

### 4.1 O canal medido

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
