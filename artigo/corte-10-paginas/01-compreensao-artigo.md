# Compreensão do artigo (leitor, só pelo texto)

## Tese

O canal acústico entre computadores comuns tem piso de ruído desigual por frequência, resposta em pente, vazamento da janela, harmônicos e saturação. Um modem que decide cada tom contra o piso da própria frequência, entrega confiança por bit a um código convolucional com Viterbi suave e sincroniza o quadro por duas varreduras externas entrega dados íntegros pelo ar, e uma negociação pelo som escolhe a configuração de cada sentido sem combinar nada antes.

## Seções

**1 Introdução.** Situa o som contra rádio e infravermelho, define FSK, cita a literatura (Lopes e Aguiar, Putz, ggwave) e apresenta o sistema. Essenciais: §1 "Rádio e infravermelho...", §5 "Este trabalho apresenta..." com a Fig. 1. §3/§4 dão o contexto da literatura e a faixa de taxas.

**2 O canal acústico.** O que o canal faz com o tom e que limites isso impõe ao projeto.
- 2.1: detecção por maior energia, log2 M bits, resolução (1), 408 amostras e 118 Hz contra 162,5 Hz. Essenciais: §3 "O receptor escolhe...", §4 + eq. (1) + §5 "Nela, fs...". §6 "O descarte cobre..." justifica o descarte.
- 2.2: piso (§1-3, Fig. 2), "Um tom transmitido precisa superar..." (é a premissa de 3.2), pente, reverberação, vazamento (eq. 2, Fig. 3, "O tom vizinho... −13,0 dB"), detecção (Fig. 4, desvio acima de 2,5 kHz), harmônicos e saturação (Fig. 5). Essenciais: piso + Fig. 2, "Um tom transmitido...", pente "O som chega ao microfone...", eq. (2), "O tom vizinho...", não linearidade "A cadeia analógica cria...". Figs. 3, 4 e 5 confirmam a teoria no sistema; Fig. 4 serve de ponte para o Gray (3.1).
- 2.3: faixa de 700-3325 Hz, sem ultrassom. Um parágrafo, justifica a escolha de faixa.

**3 Camada física.** Converte bits em tons e volta, com confiança.
- 3.1: as quatro formas (Fig. 6). Cada parágrafo de forma ("A 2-FSK usa...", "A 5×2-FSK votada...", "A 5×2-FSK multicanal...", "A 16-FSK emite...") é essencial porque a Fig. 15 compara as quatro. "Nas duas formas de cinco pares, os dez tons..." (harmônicos) e "Nas formas de cinco pares, cinco tons dividem..." (14 dB) são justificativas de projeto.
- 3.2: decisão contra o piso, eq. (3), Fig. 7, LLR ("Além do valor decidido..."). Essenciais: eq. (3) + "Nela, Ek..." e o parágrafo do LLR (ligação com 4.1).
- 3.3: malha × varreduras, eq. (4), Fig. 8, desvio medido 479,90-480,07, exatidão de S. Essenciais: §1 "Os dois computadores...", §3 "A malha leva alguns símbolos..." (o defeito que a Fig. 16 mede), §4 "A implementação atual marca...", eq. (4), §"No sistema implementado, em quatro quadros...". "O mesmo cálculo mostra por que S..." é refinamento.
- 3.4: nível abaixo da saturação; picos 2,5× na 16-FSK. Curta; sustenta a condição "abaixo da saturação" dos ensaios.

**4 Camada de enlace.** Bits com confiança viram dados íntegros e ordenados.
- 4.1: redundância, repetição × convolucional, XOR, Fig. 9, taxa 1/3 K=7, Viterbi suave, Fig. 10 (112 erros, 9,6%, corrigidos), entrelaçamento e repetição. Essenciais: "O sistema usa um código convolucional...", "Na recepção, o algoritmo de Viterbi...", Fig. 10 e seu parágrafo, e a última frase de "Antes da transmissão..." (repetição, usada em 4.4 e na 6).
- 4.2: palavra de 31 bits por correlação; Fig. 11. Essenciais: §1 "A camada física entrega..." e §2 "Logo antes do bloco...".
- 4.3: pacotes, CRC-16, pare-e-espere, CRC-32. Essenciais os dois parágrafos.
- 4.4: chamada, sondagem, contrato decidido pelo receptor, recuo; Fig. 12; Fig. 13 justifica medir a cada sessão. Essenciais: "O receptor, que mediu a sondagem..." e "A medição se repete...".

**5 Interface.** O visor no navegador e a Fig. 14 (provisória). Não sustenta nenhum resultado; mostra o sistema em uso.

**6 Resultados.** Condições (§1); quatro formas a 10 e 30 cm com Fig. 15; malha × varreduras com Fig. 16 (15 × 23 de 24 blocos); arquivo de 1334 B (21 pacotes, 6,8 B/s; 11 pacotes, 7,2 B/s; 10 cm); duas imagens ao celular com Fig. 17; sessão negociada a 2 m com Fig. 18.

**7 Considerações.** Recapitula as duas camadas, repete os resultados principais, declara o limite (uma sala, uma sessão por forma) e o passo seguinte.

## Fio condutor

- Fig. 15 depende de 3.1 (as formas), 4.1 (repetição 3, "antes da correção") e 4.3 (pacotes e confirmações).
- Fig. 16 depende de 3.3 §3 (malha erra o início) e 4.2 (a palavra fica no início): o texto da 6 faz explicitamente essa ponte.
- Arquivo e imagens dependem de 4.1 (correção) e 4.3 (CRC-32, retransmissão, "só converge se...").
- Fig. 18 depende de 4.4 (contrato, tons excluídos, ganho) e da Fig. 13 (por que medir por sessão), e indiretamente do pente de 2.2.
- 7 §1 resume 3.2 + 4.1 + 3.3; 7 §2 resume 6.

## Redundâncias percebidas

1. Comparação contra o piso dita três vezes: 2.2 "Um tom transmitido precisa superar..."; 3.2 §1 "Como cada tom deve ser comparado..."; 7 §1 "decide cada tom contra o piso...".
2. Malha e varreduras descritas em 3.3 (§2-4) e de novo em 6 "Além de decidir cada tom, o receptor precisa saber..." (resume as duas formas antes da Fig. 16); 4.2 §1 retoma a malha ganhando/perdendo símbolo.
3. Varreduras usadas só no enlace negociado: 3.3 último § e implícito em 4.4/Fig. 11.
4. Saturação/harmônicos: 2.2 "A cadeia analógica cria..." e 3.4 §1 "Como a cadeia analógica achata os picos..."; harmônicos de novo em 3.1 "Nas duas formas de cinco pares...".
5. Vazamento para o vizinho: 2.2 "O tom vizinho..." / "Os outros quinze tons também sobem..." e 3.1 Gray "O erro mais provável é a confusão com o vizinho...".
6. "Taxa abaixo da do bloco isolado" duas vezes na 6 (parágrafo do arquivo de 1334 B e parágrafo das imagens).
7. Repetição do bloco: 4.1 última frase, 4.4 contrato, 6 Fig. 15/17; aceitável, mas são três menções.
8. FSK definida duas vezes (Resumo e 1 §2), o que é esperado pelo modelo; "condição abaixo da saturação" em 3.4 e 6 §1.
9. 7 §2 repete quase literalmente 6 (quatro formas, "quase três vezes mais rápidas", 1334 B em 21 pacotes).

## Inconsistências notadas (para o autor, não cortes)

- Resumo cita "11,3 bytes por segundo, com 4 blocos íntegros de 4", número que não aparece na seção 6.
- 6 §1 diz que no ensaio do sincronismo um canal de controle entre os computadores comanda a gravação; o parágrafo da Fig. 16 diz que as 24 gravações foram feitas num único computador.
- 6 §1 diz "com um celular no lugar de um deles nos ensaios ... da transferência de arquivo", mas o arquivo de 1334 B foi entre os dois computadores.
- 3.1 diz que a 2-FSK usa Bell 202 a 1200 símbolos/s, mas a 6 envia as quatro formas "a 100 símbolos por segundo" (o comentário pendente da 3.4 registra a dúvida).
