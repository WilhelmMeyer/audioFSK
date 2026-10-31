# Votação consolidada e o que foi aplicado

Leitores: **A** = artigo (`04a`), **P** = programa (`04b`). Regra: os dois concordam, aplica; divergem, fica a opção mais conservadora; correção factual de P prevalece sobre o texto proposto.

**Resultado: o PDF foi de 11 para 9 páginas**, com cerca de meia coluna livre na última. Montado com `monta.py --pdf` em 2026-10-30.

| # | Trecho | A | P | Decisão |
|---|---|---|---|---|
| P1 | 2.1, faixa audível | TIRA | TIRA | **tirado** |
| P2 | 1, definição de FSK | ENCURTA | ENCURTA | **mesclado na 2.1** |
| P3 | aberturas das seções 3 e 4 | TIRA | TIRA | **tirado** |
| P4 | 3.3, contagem exata de $S$ | TIRA | ENCURTA | **meia frase** no parágrafo anterior (o erro de contagem foi real) |
| P5 | 3.3, qual protótipo usa a malha | TIRA | TIRA | **tirado** |
| P6 | 5, abertura dos resultados | ENCURTA* | ENCURTA* | **encurtado**, com a frase do canal de controle corrigida por P |
| P7 | 5, recapitulação do sincronismo | ENCURTA | ENCURTA* | **encurtado**, frase neutra de P (ver pendência 1) |
| P8 | 5, transferência de arquivo | ENCURTA | ENCURTA | **encurtado**, mantidas as três a 10 cm (A); saiu o caso de 128 bytes |
| P9 | 5, imagens no celular | ENCURTA | ENCURTA | **encurtado**, ponto no lugar do ponto e vírgula |
| P10 | Figura 1 (bancada) | TIRA | TIRA | **tirada** |
| P11 | seção 5 Interface e figura do visor | TIRA | TIRA | **tirada**; seções 6 e 7 viram 5 e 6 |
| P12 | figura do quadro codificado | TIRA | TIRA | **tirada** |
| P13 | figura da sequência negociada | TIRA | TIRA | **tirada** |
| P14 | figura do quadro sintético | ENCURTA | TIRA | **tirada**; definição de $n_1$, $n_2$ levada ao "Nela," de (4) |
| P15 | figura dos erros por tom | ENCURTA | ENCURTA | **figura tirada**, o número fica no texto |
| P16 | 4.1, repetição tripla | ENCURTA | ENCURTA | **mesclado** no parágrafo do convolucional |
| P17 | figura da decisão contra o piso | PERMANECE | PERMANECE | **permanece** |
| P18 | figura do espalhamento da janela | último caso | ENCURTA | **permanece** (não foi preciso) |

\* com ressalva factual.

**Compressão extra:** a abertura da 3.2 deixou de repetir a 2.2. As figuras foram renumeradas de 1 a 12.

## Pendências para o autor

1. **Composição das 24 gravações da Figura 10 (sincronismo).** O texto antigo dizia "blocos de 48 bytes em 16-FSK, num único computador". O comentário de fontes indica uma mistura: 4 gravações de 192 B entre máquinas (`12-13-SYNC`), 8 de 2-FSK com FEC entre máquinas (`H03-2FSK-FEC`) e o restante em 16-FSK numa máquina só. A frase atual é neutra. Conferir a composição e os números 15/24 e 23/24.
2. **Canal de controle.** Segundo P, `capture.py` e `recvfile.py` usam esse canal, e os ensaios com celular não. A frase atual foi escrita assim.
3. **Embaralhamento da carga.** Sem ele, a bandeira chegou com 26 de 30 pacotes; o texto não cita. Cabe uma oração, já que há espaço.
4. **Resumo:** "11,3 B/s, com 4 blocos íntegros de 4" não aparece nos resultados.
5. **2-FSK:** a 3.1 descreve Bell 202 a 1200 baud, mas os resultados usam as quatro formas a 100 baud. O comentário pendente continua no .md.
6. **Figura dos erros por tom devolvida** a pedido do autor (agora Figura 9; resultados renumerados de 10 a 13). O PDF fica com **10 páginas exatas**, e a página 10 tem só as duas últimas referências. Não há folga: qualquer acréscimo passa do limite.
