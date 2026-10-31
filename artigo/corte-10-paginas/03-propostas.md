# Propostas de corte para 10 páginas

Medido no `artigo_modem.pdf` atual (11 páginas, duas colunas, cerca de 47 linhas por coluna, 94 por página). **A página 11 tem só uma coluna parcial de referências, cerca de 33 linhas.** Isso é o excesso real; a meta pedida, ~1,3 página, equivale a ~120 linhas de coluna. Economias abaixo em linhas de coluna, figura contada pela altura da imagem mais a legenda. As figuras flutuam, então o ganho real pode variar algumas linhas para mais ou para menos (a página 3 já tem ~12 linhas vazias no pé da coluna direita).

**Soma das 18 propostas: ~183 linhas, ~1,9 página.**

- **P1 a P9, só texto, nenhuma figura: ~43 linhas.** Bastam sozinhas para tirar a página 11 (33 linhas), com folga pequena.
- **P1 a P11: ~74 linhas, ~0,8 página.** Folga confortável para 10 páginas.
- **P1 a P14: ~121 linhas, ~1,3 página.** Atinge a meta pedida sem tocar em figura de resultado nem nas Figuras 3, 4, 7, 9 e 10.

Ordem: da mais segura para a mais arriscada.

| # | Localização | Tipo | Economia | Por que sai | O que se perde |
|---|---|---|---|---|---|
| P1 | 2.1, "A banda disponível para os dados é a faixa audível..." | cortar inteiro | 4 | Redundante: a 2.3 diz o mesmo com a razão. | Nada; a 2.3 cobre. |
| P2 | 1, "A modulação por deslocamento de frequência, do inglês..." | mesclar com 2.1 | 3 | Parágrafo de uma frase, solto entre a comparação de meios e a literatura. | Nada, se a sigla migrar (versão abaixo). |
| P3 | Abertura da 3 ("A camada física converte...") e da 4 ("A camada de enlace recebe...") | cortar as duas | 8 | Anunciam o que o título e a primeira subseção já dizem. | Uma frase de definição de cada camada; a 1 e o resumo já a dão. |
| P4 | 3.3, "O mesmo cálculo mostra por que $S$ tem de ser exato..." | cortar inteiro | 5 | Detalhe de implementação (um erro de contagem já corrigido), não fundamento. | O alerta sobre a contagem exata de símbolos. |
| P5 | 3.3, "No enlace negociado da seção 4.4, todo quadro leva as duas varreduras..." | cortar inteiro | 5 | Detalhe de montagem: qual protótipo usa qual mecanismo. | A informação de que o enlace negociado dispensou a malha. |
| P6 | 6, "Os ensaios foram feitos com dois computadores na mesma sala..." | encurtar | 4 | Lista montagens que cada resultado repete ao lado do número; e diz que o canal de controle serviu ao ensaio do sincronismo, que a Figura 16 descreve como feito num computador só. | Nada que os parágrafos seguintes não digam. |
| P7 | 6, "Além de decidir cada tom, o receptor precisa saber onde começa..." | encurtar | 5 | Recapitula a 3.3. | Nada. |
| P8 | 6, "Com os blocos entregues, a transferência de arquivo depende..." | encurtar | 4 | Três variantes da mesma transferência; a de 64 bytes é a do resumo e da conclusão. | Os casos de 128 bytes e de 10 cm. |
| P9 | 6, "A Figura 17 mostra duas imagens enviadas do computador para um celular..." | encurtar | 5 | Repete condições já ditas e explica a taxa duas vezes. | Nada medido. |
| P10 | Figura 1 e "A Figura 1 mostra o arranjo." | tirar figura | 9 | Ilustra o que o título e a frase anterior já dizem. | A imagem de abertura. |
| P11 | Seção 5 inteira e Figura 14 | cortar inteiro | 22 | Não é camada física nem enlace, não tem medida, a figura é provisória e o comentário registra que o texto descreve a tela antiga. A estrutura decidida (CLAUDE.md) tem seis seções sem ela. | O visor e a tela do celular. Exige trocar "no formato do visor da seção 5" na 3.3 (ver abaixo) e renumerar 6 e 7. |
| P12 | Figura 11 e "A Figura 11 mostra a palavra no quadro transmitido..." | tirar figura | 15 | O quadro é desenho, não medida; a palavra e as varreduras já estão descritas na 3.3 e na 4.2. | A proporção visual entre preâmbulo e bloco no tempo. |
| P13 | Figura 12 e "A Figura 12 mostra uma sessão do sistema implementado..." | tirar figura | 14 | Diagrama de turnos; a 4.4 descreve a sequência em texto. | A linha do tempo de uma sessão, com o pacote repetido. |
| P14 | Figura 8 e "A Figura 8 mostra, no formato do visor da seção 5, um quadro curto..." | tirar figura | 18 | Gerada pelo modulador sem passar pelo ar; ilustra a (4), que se lê sem ela. | A imagem de $n_1$, $n_2$ e das fronteiras. Remove também a remissão à seção 5. |
| P15 | Figura 13 (erros por tom) | tirar figura, manter a frase | 16 | O número que sustenta a ideia (três tons, 47% a 90%, mudando entre séries) fica no texto. | A evidência visual de que os piores tons mudam. |
| P16 | 4.1, "A redundância mais simples é repetir cada bit três vezes..." | mesclar com o seguinte | 5 | Contraste didático que o parágrafo seguinte pode fazer em meia frase. | O exemplo da repetição tripla. |
| P17 | Figura 7 (decisão contra o piso) | tirar figura | 19 | A (3) e a Figura 4 já mostram energia por tom; a 7 acrescenta o piso corrente. | A visão do piso de cada tom e da grandeza comparada em (3). Arriscado: é a única figura da decisão. |
| P18 | Figura 3 (espalhamento da janela) e o parágrafo que a apresenta | tirar figura, encurtar | 22 | A Figura 4 também mostra o vazamento contra a (2). | A prova de que o espalhamento é da janela e não do canal, e o −13,0 contra −13,4 dB. Arriscado: é conta de implementação, que o roteiro quer. |

Fora da lista, como último recurso: baixar a escala das figuras de 0,95 para 0,85 tira ~10% da altura de cada uma, ~25 linhas no total, ao custo de legibilidade em figuras já densas (6, 7, 10).

## Versões curtas propostas

**P2.** Apagar o parágrafo da introdução e abrir o segundo parágrafo da 2.1 assim:
> Na modulação por deslocamento de frequência, do inglês *frequency shift keying* (FSK), cada valor de bit, ou de grupo de bits, corresponde a uma frequência combinada entre as duas pontas. A cada intervalo fixo, chamado símbolo, o transmissor emite um tom e o receptor identifica qual esteve presente.

**P6.**
> Os ensaios foram feitos na mesma sala, entre dois computadores ou entre um computador e um celular, todos com alto-falante e microfone de uso geral e com o nível abaixo da saturação. Na transferência de arquivo entre computadores, um canal de controle apenas comanda o ensaio, e os bytes avaliados viajam somente pelo ar.

(Conferir com o autor em qual ensaio o canal de controle de fato atuou; o texto atual o põe no do sincronismo, que foi feito num computador só.)

**P7.**
> A Figura 16 compara as duas formas de sincronismo da seção 3.3, a malha e as varreduras, sobre as mesmas 24 gravações de blocos de 48 bytes em 16-FSK, feitas num único computador que tocava e gravava ao mesmo tempo.

**P8.**
> Uma imagem de 1334 bytes foi transferida entre os dois computadores com o alto-falante afastado, em 21 pacotes de 64 bytes, e chegou idêntica, conferida pelo CRC de 32 bits, sem retransmissão e a 6,8 B/s. A taxa fica abaixo da do bloco isolado pelo preâmbulo, pelo cabeçalho e pela espera entre pacotes.

**P9.**
> A Figura 17 mostra duas imagens enviadas a um celular a 10 cm, em 16-FSK com configuração fixada à mão, ambas idênticas às enviadas e com todos os pacotes na primeira tentativa. O logotipo, de 1270 bytes, chegou a 3,9 B/s com 5,0% dos bits errados e o bloco sem repetição; a bandeira, de 934 bytes, a 2,9 B/s com 5,4% e o bloco repetido duas vezes. Em pacotes de 32 bytes a espera pela confirmação pesa mais na taxa.

(Se o ponto e vírgula incomodar pela regra do autor, trocar por ponto.)

**P11.** Na 3.3, onde ficar a Figura 8 (se P14 não for aceita), trocar "no formato do visor da seção 5," por "em espectrograma,". Renumerar RESULTADOS para 5 e CONSIDERAÇÕES FINAIS para 6.

**P15.** Manter o parágrafo e só apagar " (Figura 13)".

**P16.** Apagar o parágrafo da repetição tripla e abrir o seguinte assim:
> O sistema usa um código convolucional, que envia três bits por bit da mensagem sem que nenhum deles seja cópia, ao contrário da repetição simples, em que duas cópias trocadas bastam para a maioria errar.

**P17.** Apagar a figura e a frase "A Figura 7 mostra essa decisão em um símbolo recebido no sistema implementado."

**P18.** Apagar a figura e trocar o parágrafo "A Figura 3 mostra o efeito..." e o seguinte por:
> No sistema implementado, o tom vizinho da 16-FSK, 162 Hz acima de 1700 Hz, cai no primeiro lóbulo lateral e recebe −13,0 dB, contra −13,4 dB previstos por (2). Essa margem separa um tom do vizinho na decisão, mesmo sem ruído.

Renumerar as figuras seguintes conforme as que saírem.
