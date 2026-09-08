<!--
LEVANTAMENTO DE REFERENCIAS. Artigo do modem acustico, VII SIMECA.
Feito em 2026-09-07 por busca na web. Cada entrada traz a FONTE da verificacao, porque a regra do
artigo e que nenhuma referencia seja inventada. "Verificada" = titulo, autores, ano e veiculo
confirmados em pagina do editor, do IEEE/ACM/Springer, ou da propria instituicao dos autores.
Texto integral lido em nenhuma delas ainda; onde o artigo for usar um NUMERO da fonte, ler antes.
Os grupos G1 a G8 sao os do comentario de REFERENCIAS em artigo_modem.md.
Formato ABNT autor-data, uma referencia por linha, para copiar direto.

ESCOPO (decisao do autor, 2026-09-07, revista no mesmo dia): a decisao inicial restringia estas fontes
a INTRODUCAO e so a ela. O autor a ampliou ao pedir a secao 2.1, que passa a dialogar com a literatura
lida. Vale hoje: a introducao cita FSK, Bell 202, HART e a transmissao de dados por som; a 2.1 cita o
meio acustico. As secoes 2.2 em diante seguem a doutrina do projeto, que e sustentar cada afirmacao no
que foi medido em resultados/, e nao em literatura, ate que o autor peca o contrario.
Os grupos G5 a G8 abaixo ficam levantados para o caso de o autor querer citacao de livro-texto mais
adiante, e nenhum foi usado.
ONDE CADA UMA E CITADA (atualizado 2026-09-07, depois de citar tambem na 2.1 e na 2.2):
  FINNEGAN e BENSON (2014): introducao P1, e so ali. Foi citada tambem na 2.2, para distinguir o
    mapeamento direto de marca e espaco do Bell 202 original da codificacao por inversao do uso amador,
    e o autor mandou tirar: e detalhe interno que a plateia do SIMECA nao cobra. Procurei nesse artigo
    algo que sustentasse o nosso detector por atraso e produto e NAO HA: o trabalho e sobre protocolo,
    enquadramento e AX.25, nao sobre deteccao.
  WU (2023): introducao P2.
  LOPES e AGUIAR (2001): introducao P3; 2.1, no pente; 2.2 duas vezes, na abertura, pelas duas familias
    (um tom por simbolo e k tons simultaneos), e no detector, pela tarefa de decidir presenca sem fase.
  PUTZ et al. (2026): introducao P4; 2.1 quatro vezes, no ultrassom, no eco, no estouro e no ruido do
    ambiente.
Nenhuma fonte nao lida foi citada. PROAKIS e SALEHI, KUTTRUFF, TANENBAUM, LIN e COSTELLO, VITERBI e
FORNEY continuam so levantados; se algum entrar no texto, abrir o livro antes.
Quatro fontes foram LIDAS no PDF, nao no resumo, e cada uma deu uma frase a um paragrafo da
introducao: FINNEGAN e BENSON (2014), WU (2023), LOPES e AGUIAR (2001), PUTZ et al. (2026). As demais
continuam so com dado bibliografico conferido.

TETO DE 40 REFERENCIAS (decisao do autor, 2026-09-07). O levantamento de 2026-09-07 fechou em 16, e
sobra folga para 24. Nota de calibragem, nao objecao: 16 ja cobrem os oito grupos que o corpo do texto
pede, e artigo didatico de 6 laudas costuma citar de 15 a 25. Crescer ate 40 e possivel e so vale se
cada nova entrada for citada de fato no corpo; referencia listada e nao citada e defeito de forma.
-->

# Referências levantadas

<!--
Os PDFs abertos estao em artigo/referencias-pdf/, ignorada pelo git: sao textos de terceiros, com
direito autoral de terceiros, e nao pesam no repositorio. Quem clonar refaz a pasta pelas URLs abaixo.
As tres fechadas abrem pelo acesso institucional do IFPR (portal de periodicos da CAPES chega ao IEEE
Xplore); a do FieldComm exige cadastro. Nenhuma foi lida por inteiro ainda.
-->

## Tabela de leitura

<!-- Coluna "Onde entra" auditada em 2026-09-07 contra o corpo de artigo_modem.md (grep das quatro
fontes citadas, seção por seção). "não citada" quer dizer levantada e ainda não usada no texto, não
descartada; a razão do descarte, quando há uma, fica em "Levantado e não aproveitado", no fim deste
arquivo. -->

| # | Referência | O que contém, e o que dele serve a este artigo | Onde entra | PDF |
|---|---|---|---|---|
| 1 | PUTZ *et al.* (2026), ACM Trans. IoT | Revisão de 31 estudos de transmissão acústica aérea, 8 esquemas reimplementados, mais de 11000 transmissões em sala real e em câmara anecoica. Dá a régua da área: taxas publicadas de 5 bps a 32 kbps, sistemas comerciais entre 10 e 200 bps por priorizarem confiabilidade, e a crítica de que anúncios acima de 500 bps vêm de condições irreais. Atribui a degradação ao multipercurso em ambiente fechado e dá o número: som 87000 vezes mais lento que a onda eletromagnética, espalhamento de atraso de dezenas de milissegundos. | Introdução P4; seção 2.1, quatro vezes (ruído do ambiente, ultrassom, eco, estouro) | `putz-2026-acm-tiot.pdf` |
| 2 | LOPES; AGUIAR (2003), IEEE Pervasive Computing | Compara som, rádio e infravermelho como meios de curto alcance e baixa banda, que é o argumento do primeiro parágrafo da introdução, feito por terceiros. | não citada | fechado, IEEE Xplore 1228528 |
| 3 | LOPES; AGUIAR (2001), WASPAA | O "Digital Voices", das primeiras transmissões acústicas aéreas documentadas. Já usa M-FSK na banda audível, e varia ASK, FSK e espalhamento espectral para que a mensagem soe como música em vez de modem. | Introdução P3; seção 2.1, no pente; seção 2.2, duas vezes (abertura e detector) | `lopes-aguiar-2001-waspaa.pdf` |
| 4 | FIELDCOMM GROUP, especificação HART | A norma. Fixa o Bell 202 como camada física do HART, 1200 bps sobre a malha de 4 a 20 mA. É o que torna o Bell 202 um padrão vivo, não uma peça de museu. | não citada | fechado, exige cadastro |
| 5 | WU, TI SLAAEH0 | Guia do HART por quem fabrica o modem. Frequências, enquadramento, a lógica de superpor o digital ao analógico sem perturbá-lo. Fonte primária acessível para os números do Bell 202 no HART. | Introdução P2 | `ti-slaaeh0-hart.pdf` |
| 6 | FINNEGAN; BENSON (2014), TAPR DCC | Demodulação do Bell 202 e a distinção entre o Bell 202 original da AT&T e o uso amador sobre AX.25, com NRZI. Trata do discriminador de frequência, que é o detector da nossa 2-FSK. | Introdução P1, e só ali | `finnegan-benson-2014-bell202.pdf` |
| 7 | KUTTRUFF (2016), *Room acoustics* | Livro-texto de acústica de salas. Coloração por filtro pente a partir da soma de reflexões, que é o fenômeno da seção 2.1, e reverberação, que era o da antiga 2.3. | não citada | livro |
| 8 | LEE *et al.* (2015), INFOCOM | Adota chirp por resolver multipercurso em canal seletivo em frequência, e chega a 16 bps com alcance de até 25 m. É a literatura por trás das nossas varreduras de sincronismo, e mostra que a ideia é de terceiros e anterior. | não citada | fechado, IEEE Xplore 7218629 |
| 9 | MATSUOKA; NAKASHIMA; YOSHIMURA (2008), MMM | OFDM acústico embutido em áudio comum, substituindo a faixa alta do sinal por portadoras, com alcance de cerca de 3 m. É o OFDM acústico citado na introdução como ferramenta do campo que não adotamos. | não citada | fechado, Springer |
| 10 | GETREUER *et al.* (2018), IEEE Trans. Multimedia | Espalhamento espectral mais MFSK em 18,5 a 20 kHz, 84 bps, componente da plataforma Nearby do Google. Prova que o quase-ultrassom funciona quando o transdutor responde lá em cima, o que sustenta a nossa recusa dele por limitação de hardware, e não de princípio. | não citada | fechado, IEEE Xplore 8080245 |
| 11 | PROAKIS; SALEHI (2008), *Digital communications* | Livro-texto. Detecção não coerente de M-FSK e a relação entre M, taxa de símbolos e taxa de bits da equação da seção 2.2. | não citada | livro |
| 12 | GERGANOV (2021), ggwave | Software, não artigo. Faz exatamente o que a nossa 16-FSK faz, divide o dado em pedaços de 4 bits e manda um tom por pedaço, com Reed-Solomon por cima, e entrega 8 a 16 bytes por segundo. Mesma ordem de grandeza dos 11 B/s medidos aqui, o que dá uma âncora externa ao resultado. | não citada | repositório aberto |
| 13 | TANENBAUM; WETHERALL, *Redes de computadores* | Livro-texto. CRC, pare-e-espere, ARQ e HDLC, que é a comparação feita ao dizer que segmentação e reenvio são enlace, não transporte. Preferir a tradução brasileira. | não citada | livro |
| 14 | VITERBI (1967), IEEE Trans. Inf. Theory | O artigo do algoritmo. Limites de erro para códigos convolucionais e o decodificador assintoticamente ótimo. | não citada | fechado; ver Forney (1973) |
| 15 | FORNEY (1973), Proc. IEEE | A exposição que tornou o algoritmo de Viterbi padrão, e a leitura mais didática dos dois. | não citada | `forney-1973-viterbi.pdf` |
| 16 | LIN; COSTELLO (2004), *Error control coding* | Livro-texto. Decisão suave e entrelaçamento, que são os dois pontos da seção 2.4 que Viterbi e Forney sozinhos não cobrem. | não citada | livro |

## G1 - comunicação acústica entre dispositivos, transferência de dados por áudio (introdução, P1)

LOPES, Cristina Videira; AGUIAR, Pedro M. Q. Acoustic modems for ubiquitous computing. **IEEE Pervasive Computing**, v. 2, n. 3, p. 62-71, 2003. DOI: 10.1109/MPRV.2003.1228528.
<!-- Verificada: IEEE Xplore doc 1228528. A citacao central da P1: compara o som com radio e
infravermelho como meio de curto alcance e baixa banda, que e exatamente o argumento do paragrafo. -->

LOPES, Cristina Videira; AGUIAR, Pedro M. Q. Aerial acoustic communications. In: **IEEE Workshop on Applications of Signal Processing to Audio and Acoustics (WASPAA)**, 2001, New Paltz. Anais [...]. New Paltz: IEEE, 2001.
<!-- Verificada: IEEE Xplore doc 969582; PDF em ee.columbia.edu/~dpwe/papers/LopesA01-aerialcomm.pdf;
pagina de publicacoes do ISR/IST. E o "Digital Voices", das primeiras transmissoes acusticas aereas
documentadas, e ja usa M-FSK na banda audivel. Serve tambem a G5. -->

PUTZ, Florentin; FORTMANN, Philipp; FRANK, Jan; HAUGWITZ, Christoph; KUPNIK, Mario; HOLLICK, Matthias. Evaluating acoustic data transmission schemes for ad-hoc communication between nearby smart devices. **ACM Transactions on Internet of Things**, v. 7, n. 1, art. 8, 2026. arXiv:2602.02249.
<!-- Verificada: pagina do arXiv com o veiculo estampado. A mais util de todas. Revisao de 31 estudos,
8 esquemas reimplementados, mais de 11000 transmissoes em sala real e em camara anecoica. Dela saem
tres coisas que o artigo pode usar: (a) a faixa de taxas da literatura, de 5 bps a 32 kbps; (b) a
constatacao de que sistemas comerciais ficam em 10 a 200 bps priorizando confiabilidade, enquanto os
academicos anunciam acima de 500 bps em condicoes irreais; (c) o multipercurso interno como principal
degradacao, com espalhamento de atraso na ordem de dezenas de milissegundos. Texto integral por ler. -->

## G2 - Bell 202, modems telefônicos, discriminador de frequência, HART (introdução, P2)

FIELDCOMM GROUP. **HART communication protocol specification**: FCG TS20013 (HCF_SPEC-13). Austin: FieldComm Group. Disponível em: https://library.fieldcommgroup.org/20013/TS20013/.
<!-- Verificada: biblioteca do proprio FieldComm Group, que detem a especificacao. E a norma, nao um
artigo. HART e norma IEC 61158 tipo 20 e IEC 61784 CPF 9; se o artigo preferir citar a norma IEC em
vez da especificacao do consorcio, os dados da IEC ainda precisam ser conferidos na fonte. -->

WU, Joseph. **A basic guide to the HART protocol**. Dallas: Texas Instruments, nov. 2023. (Application Report SLAAEH0). Disponível em: https://www.ti.com/lit/pdf/slaaeh0.
<!-- Verificada e LIDA no PDF, paginas 1, 2 e 4. Nota tecnica de fabricante, citavel como tal. O
carimbo de rodape da a data: SLAAEH0, novembro de 2023. A figura 1-3 marca 1200 Hz no "1" e 2200 Hz
no "0", o que encerra a divergencia registrada logo abaixo. Frase usada na introducao, P2: "a
backward-compatible enhancement to 4-20 mA instrumentation that allows two-way communication with
smart, microprocessor-based field devices" e "The standard HART transmission is a frequency shift
keyed (FSK) signal superimposed on the 4-20mA signal. The FSK bits are transmitted at 1200 bits per
second". -->

FINNEGAN, Kenneth W.; BENSON, Bridget. Clarifying the amateur Bell 202 modem. In: **ARRL/TAPR Digital Communications Conference (DCC)**, 33., 2014. Anais [...]. [S.l.]: TAPR, 2014.
<!-- Dado bibliografico verificado pelo proprio PDF hospedado em files.tapr.org; o texto nao pode ser
extraido automaticamente e precisa ser lido a mao antes de citar. Trata da demodulacao do Bell 202 e
da distincao entre o Bell 202 original da AT&T e o uso amador sobre AX.25. -->

### Divergência de fonte, resolvida, que vale registrar

<!-- Duas frequencias circulam para o "0" do HART: 2200 Hz e 2400 Hz. As fontes de quem fabrica o
modem dizem 2200 (Analog Devices, DS8500: bit 0 em 2200 Hz, bit 1 em 1200 Hz, FSK de fase continua a
1200 bps; e a patente US10897384B2, que descreve o filtro passa-faixa como delimitando 1200 a 2200 Hz).
O 2400 aparece so em fontes secundarias. O artigo mantem 1200/2200, que e o que o codigo implementa
e o que as fontes primarias dizem. -->

## G3 - canal acústico em ambiente fechado, resposta em pente (introdução P2; seção 2.1)

KUTTRUFF, Heinrich. **Room acoustics**. 6. ed. Boca Raton: CRC Press, 2016.
<!-- Verificada: pagina da Routledge/CRC, 6a edicao. Ha 7a edicao com Michael Vorlander. O capitulo de
acustica subjetiva trata da coloracao por filtro pente, que e o fenomeno da secao 2.1. Confirmar
capitulo e paginas na edicao que se tiver em maos antes de citar com pagina. -->

<!-- PUTZ et al. (2026), de G1, serve tambem aqui, e com numero: o som viaja mais de 87000 vezes mais
devagar que a onda eletromagnetica, e por isso o espalhamento de atraso e de dezenas de milissegundos.
E o argumento fisico de por que o eco importa aqui e nao importa no radio, dito por terceiros. -->

## G4 - OFDM acústico, chirp acústico, MFSK acústico (introdução, P3)

LEE, Hyewon; KIM, Tae Hyun; CHOI, Jun Won; CHOI, Sunghyun. Chirp signal-based aerial acoustic communication for smart devices. In: **IEEE Conference on Computer Communications (INFOCOM)**, 2015, Hong Kong. Anais [...]. Hong Kong: IEEE, 2015. p. 2407-2415. DOI: 10.1109/INFOCOM.2015.7218629.
<!-- Verificada: pagina da Seoul National University e Semantic Scholar. 16 bps, alcance ate 25 m.
Adota chirp justamente por resolver multipercurso em canal seletivo em frequencia. E a referencia
que sustenta as varreduras de sincronismo deste artigo, feitas por terceiros e antes. -->

MATSUOKA, Hosei; NAKASHIMA, Yusuke; YOSHIMURA, Takeshi. Acoustic OFDM: embedding high bit-rate data in audio. In: **International Multimedia Modeling Conference (MMM)**, 14., 2008, Kyoto. Anais [...]. Berlim: Springer, 2008. p. 498-507. (Lecture Notes in Computer Science, 4903).
<!-- Verificada: capitulo Springer 10.1007/978-3-540-77409-9_47. Ha a extensao em periodico:
MATSUOKA, H.; NAKASHIMA, Y.; YOSHIMURA, T. Acoustic OFDM system and its extension. The Visual
Computer, 2008, DOI 10.1007/s00371-008-0281-5. Alcance de cerca de 3 m. -->

GETREUER, Pascal; GNEGY, Chet; LYON, Richard F.; SAUROUS, Rif A. Ultrasonic communication using consumer hardware. **IEEE Transactions on Multimedia**, v. 20, n. 6, p. 1277-1290, 2018. DOI: 10.1109/TMM.2017.2766049.
<!-- Verificada: pagina do proprio autor (getreuer.info) e Google Scholar com paginas e DOI.
DSSS mais MFSK, 84 bps, banda de 18,5 a 20 kHz, e componente da plataforma Nearby do Google.
Referencia de peso onde o artigo disser que o ultrassom exige transdutor que responda la em cima. -->

## G5 - modulação M-FSK, detecção não coerente, diversidade em frequência (seção 2.2)

PROAKIS, John G.; SALEHI, Masoud. **Digital communications**. 5. ed. Nova York: McGraw-Hill, 2008.
<!-- Verificada: ISBN 978-0-07-295716-7. Livro-texto para deteccao nao coerente de M-FSK e para a
relacao entre M, taxa de simbolos e taxa de bits da equacao da secao 2.2. Confirmar capitulo. -->

<!-- LOPES e AGUIAR (2001), de G1, e o M-FSK acustico propriamente dito, e cabe citado junto aqui. -->

GERGANOV, Georgi. **ggwave**: tiny data-over-sound library. 2021. Disponível em: https://github.com/ggerganov/ggwave.
<!-- Verificada: repositorio e README. Nao e artigo, e software, e por isso entra so se o autor quiser
um ponto de comparacao pratico. Vale muito como tal: usa exatamente a ideia da 16-FSK deste artigo,
divide o dado em pedacos de 4 bits e manda um tom por pedaco, com Reed-Solomon por cima, e entrega
8 a 16 bytes por segundo. E a mesma ordem de grandeza dos 11 B/s medidos aqui. PUTZ et al. (2026)
mediram o ggwave e dao 268 bps para ele, o que permite cita-lo por terceiros, se preferir. -->

## G6 - reverberação, tempo de reverberação, interferência entre símbolos (seção 2.3)

<!-- KUTTRUFF (2016), de G3, e PUTZ et al. (2026), de G1, cobrem os dois. Nao foi levantada
referencia especifica de intervalo de guarda contra interferencia entre simbolos; se a secao precisar,
PROAKIS e SALEHI (2008) tem o tratamento geral. -->

## G7 - CRC, ARQ, pare-e-espere, HDLC (seção 2.4)

TANENBAUM, Andrew S.; WETHERALL, David J. **Computer networks**. 5. ed. Boston: Pearson, 2011.
<!-- Verificada: ISBN 978-0-13-212695-3, Pearson, publicado em 27/09/2010, com edicoes internacionais
de 2013 e uma 6a edicao posterior. Ha traducao brasileira (Redes de computadores, Pearson), que seria
preferivel num artigo em portugues; edicao e ano da traducao POR CONFIRMAR antes de citar.
Cobre CRC, pare-e-espere, ARQ e HDLC, que e a comparacao que o artigo faz ao dizer que segmentacao e
reenvio sao enlace. -->

## G8 - códigos convolucionais, Viterbi, decisão suave, entrelaçamento, repetição (seção 2.4)

VITERBI, Andrew J. Error bounds for convolutional codes and an asymptotically optimum decoding algorithm. **IEEE Transactions on Information Theory**, v. IT-13, n. 2, p. 260-269, abr. 1967.
<!-- Verificada: citacao completa em multiplas fontes academicas independentes. -->

FORNEY JR., G. David. The Viterbi algorithm. **Proceedings of the IEEE**, v. 61, n. 3, p. 268-278, mar. 1973.
<!-- Verificada: PDF na Georgia Tech (www2.isye.gatech.edu/~yxie77/ece587/viterbi_algorithm.pdf) com
o cabecalho de pagina conferindo volume, numero, pagina e data. -->

LIN, Shu; COSTELLO JR., Daniel J. **Error control coding**. 2. ed. Upper Saddle River: Pearson Prentice Hall, 2004.
<!-- Verificada: ISBN 978-0-13-042672-7, Pearson, 2004. Cobre decisao suave e entrelacamento, que sao
os dois pontos da secao 2.4 que Viterbi (1967) e Forney (1973) sozinhos nao cobrem. -->

## Levantado e não aproveitado, com a razão

<!--
- Modems acusticos SUBAQUATICOS (varios, inclusive dissertacao em portugues da UMinho e uma revisao
  na Wireless Personal Communications, 2020). Canal diferente: 1500 m/s, Doppler, dezenas de
  quilometros. Citar confundiria o leitor sobre qual canal e o nosso.
- MFSK nao coerente com diversidade em desvanecimento Nakagami-m, Hoyt e afins. Analise de desempenho
  em canal com desvanecimento estatistico; este artigo e didatico e mede um canal deterministico
  especifico. Fora do enquadramento.
- Canais acusticos encobertos e exfiltracao por ar (MOSQUITO, PIXHELL, AirHopper, mesh acustica
  encoberta). Mesma fisica, proposito de seguranca ofensiva. Nao e o assunto e desviaria o texto.
- Patentes de modem HART e de transmissao acustica (US10897384B2, US10153928 e outras). Servem para
  dirimir divergencia tecnica, como acima, mas patente nao e referencia de artigo didatico.
- Bell System, especificacao original do Data Set 202. O catalogo de 1972 (PUB 40000, no bitsavers)
  cita as especificacoes de interface dos Data Sets 202C e 202D, de 1964, mas o documento de 1976 nao
  foi localizado. Se o artigo quiser a fonte primaria do Bell 202, e preciso ir ao bitsavers a mao.
  Enquanto isso, FINNEGAN e BENSON (2014) e a especificacao HART sustentam os numeros.
-->
