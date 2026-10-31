# Votos do leitor do programa (P1 a P18)

Critério: o trecho descreve algo que o programa faz e que pesa no resultado medido? Base: código, `CLAUDE.md` e `resultados/` (ver `02-compreensao-programa.md`).

| # | Voto | Justificativa |
|---|---|---|
| P1 | TIRA | A banda vem justificada na 2.3 com a medida; aqui não acrescenta nada. |
| P2 | ENCURTA (aceita) | A versão curta descreve bem o que o modulador faz: um tom por símbolo, alfabeto combinado entre as pontas. |
| P3 | TIRA | Frases de anúncio, sem mecanismo nem número. |
| P4 | ENCURTA | O erro de contagem foi real e pesou (`12-13-SYNC`: 0/4 blocos com o span errado, 4/4 com o certo), mas basta meia frase presa ao parágrafo anterior: "um símbolo a mais na contagem de $S$ acumula um símbolo inteiro de erro no quadro". |
| P5 | TIRA | Diz qual protótipo usa qual sincronismo e não sustenta nenhum número. |
| P6 | ENCURTA, com correção | A suspeita do proponente está **invertida**. As gravações de dois computadores da Fig. 16 (`12-13-SYNC`, `H03-2FSK-FEC`) foram feitas por `capture.py`, que comanda o outro lado pelo canal de controle; a transferência entre computadores (`recvfile.py`) também usa esse canal. Os ensaios com o celular não usam. Proposta: "Nos ensaios entre computadores, um canal de controle apenas comanda a gravação e a transferência, e os bytes avaliados viajam somente pelo ar; com o celular não há canal de controle." |
| P7 | ENCURTA, mas a versão curta está **errada** | A frase "24 gravações de blocos de 48 bytes em 16-FSK, feitas num único computador" não bate com as fontes indicadas no próprio comentário: 4 gravações de 192 B com rep 2 entre duas máquinas (`12-13-SYNC`), 8 de **2-FSK** (fsk2) entre duas máquinas (`H03-2FSK-FEC`) e o restante de 16-FSK num computador só (`studies/…-ganho-mary`). Proposta: "A Figura 16 compara a malha e as varreduras da seção 3.3 sobre as mesmas 24 gravações, cada uma lida pelos dois caminhos." O autor precisa conferir a composição (e os 15/24 contra 23/24) antes de descrever o conjunto. |
| P8 | ENCURTA (aceita) | O caso de 64 B (21/21, 0 retransmissões, 6,8 B/s, `15-PKT-ARQ`) carrega o resultado; os de 128 B e de 10 cm só repetem. A versão curta confere com os resultados. |
| P9 | ENCURTA (aceita) | Os números conferem com `H08-ARQUIVO-CELULAR` (logo rep1: 328,7 s, 3,86 B/s, 4,97%; bandeira: 30/30, 2,9 B/s, 5,4%). Ressalva menor: a bandeira levou 321,7 s ou 323,7 s conforme o arquivo, e o texto atual diz 324 s. O embaralhamento da carga foi o que fez a bandeira passar (26/30 sem ele) e não aparece no trecho; se couber, uma oração. |
| P10 | TIRA | Ilustração, sem mecanismo. |
| P11 | TIRA | O visor não pesa em nenhum número, a figura é provisória e o próprio comentário avisa que a porta serial virtual afirmada no resumo/introdução só existe sobre o Bell 202, que nunca entregou mensagem. Ao tirar, rever essas menções. |
| P12 | TIRA | É desenho, não medida. A palavra de 31 bits por correlação pesa muito, mas o texto da 4.2 já a descreve. |
| P13 | TIRA | O enlace negociado tem poucas sessões no ar (`H06`, `H07`, uma no celular) e vários detalhes só simulados; o diagrama ilustra um protocolo, não um resultado. |
| P14 | TIRA | Gerada pelo modulador sem passar pelo ar; (4) se lê sem ela. |
| P15 | ENCURTA (aceita) | O número (3 tons, 47–90%, mudando entre séries, `H05-ERROS-POR-TOM`) é medido e justifica a sondagem; a figura é dispensável. |
| P16 | ENCURTA (aceita) | A versão curta está correta para o código (taxa 1/3, K=7, nenhum bit é cópia). |
| P17 | PERMANECE | O piso por tom é mecanismo central da 16-FSK (o oráculo de piso perfeito empata: 88,4 contra 88,3%) e a figura é de um símbolo realmente recebido. Se for preciso cortar, prefiro P18. |
| P18 | ENCURTA (aceita) | O lóbulo da janela é conceito de terceiros (sinc). A conta da versão curta confere: com $N=408$ e $f_s/N≈117,6$ Hz, 162,5 Hz caem no primeiro lóbulo lateral, e (2) dá −13,4 dB. A segunda frase ("separa um tom do vizinho... mesmo sem ruído") é vaga; sugiro: "Esse vazamento soma-se ao piso do tom vizinho em cada símbolo." |

**Resumo.** Tiro P1, P3, P5 e P10 a P14. Encurto P2, P4, P6 a P9, P15, P16 e P18. P17 permanece. P6 e P7 precisam de correção factual antes de qualquer versão curta, porque o sincronismo da Figura 16 não foi medido "em 16-FSK, num único computador".
