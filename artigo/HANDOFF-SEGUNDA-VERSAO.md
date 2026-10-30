# Handoff: segunda versão do artigo (2026-10-30)

Estado para retomar depois da compactação da sessão. O texto vive em `artigo_modem.md`; a primeira versão e os pareceres, em `primeiro-envio/` (`PARECERES.md`). Regras de forma em `CLAUDE.md` desta pasta e na memória `artigo-estilo-objetivo`.

## Estado do texto

- Resumo (246 palavras, quatro formas descritas pelo que fazem, nome entre parênteses), introdução (6 parágrafos, LOPES; AGUIAR 2003 e GERGANOV 2021 acrescentadas), capítulos 2, 3, 4, 5 e 6 redigidos. Capítulo 7 vazio.
- PDF: 10 páginas, 11 figuras, 0 tabelas. Alvo: 7 laudas. **Corte pendente**, nos capítulos 2 a 4 (candidatos: fundir Figuras 3 e 4; tirar Figura 2 ou 7; encurtar 3.1 e capítulo 4).
- Montagem passa 18 de 18 (`./artigo/monta.sh`).

## Decisões do autor nesta sessão

- Voz impessoal (revisor 1). "Deslocamento de frequência", não "chaveamento". Sem "M-ária" nem "MFSK". "Intervalo de descarte", nunca "guarda".
- Equações só como consideração de implementação: (1) Δf = fs/N, (2) vazamento sinc, (3) argmax E/P, (4) T = (n2 − n1)/S.
- Dado medido fora dos resultados só para sustentar fundamento, marcado "no sistema implementado".
- Resultados: condição em uma linha, figura, uma ou duas considerações. Nada de texto em tabela.
- Títulos curtos que caibam numa linha da coluna (o conversor justifica títulos).
- Figuras pedidas pelo autor: espalhamento do tom pela janela (Fig. 3), pontos medidos sobre a curva prevista vazamento + piso (Fig. 4), esquema das quatro formas (Fig. 6), sincronismo no formato do visor, tempo na vertical, quadro curto num painel só (Fig. 8, sintético, gerado pelo modulador).
- Explicação do código convolucional: três bits emitidos por bit de entrada, não são cópias, cada um ou-exclusivo de um grupo dos sete últimos bits. Não usar "quinze" nem "seis anteriores".

## Pendências

1. Corte para 7 laudas.
2. Porta serial virtual no resumo e na introdução: só existe em `app.py --pty` sobre a Bell 202 sem correção; o enlace negociado não expõe porta serial. Autor ainda não decidiu (tirar, ou manter se o terminal da outra sessão ligar o enlace a uma PTY).
3. Capítulo 5: chat e terminal (em implementação pela outra sessão); figura do visor em modo projeção com as fases, para o 5 ou o 6.5 (precisa do painel livre).
4. Capítulo 7 por redigir.
5. Gray: código corrigido em 2026-10-29 (valor = gray(tom), `GRAY_TOM` em `modem.py`, mudança não commitada da outra sessão). Todas as gravações dos resultados e as Figuras 7 usam o mapeamento antigo; regravar quando o áudio estiver livre, se possível.
6. Conferir antes de submeter: LOPES; AGUIAR (2003) não lida (IEEE Xplore 1228528, Periódicos CAPES); taxas do ggwave (8 a 16 B/s) no repositório.
7. Tópico da janela no roteiro (artefato "Roteiro do artigo acústico"): o autor confirmou que é o espalhamento do tom e os harmônicos, já no capítulo 2.
8. Nada commitado ainda nesta sessão (mudanças em `artigo/` e scripts novos em `resultados/FIG-*`, `resultados/*/figuras/`).

## Números usados e de onde vêm

- Cap. 2: piso 27 dB, −67,6 a −94,8 dBFS (01-LVL-BASE-A2B, 4 gravações de 8 s, A→B); tom 47,4 dB sobre o silêncio, vizinho −13,0 dB contra −13,4 previsto, medido − previsto 0,9 dB até 2,5 kHz e 4,5 dB acima (02-LVL-TONE-A2B); harmônicos 30,5 e 42,2 dB (03-CH-CHIRP-A2B).
- Cap. 3: período 479,90 a 480,07 amostras em 4 quadros de 2453 símbolos (12-13-SYNC, duas máquinas); 8,0 dB vencedor sobre segundo (Fig. 7, primeira versão); picos 2,5 vezes no burst (CLAUDE.md da raiz).
- Cap. 4: metade dos erros em 3 de 16 tons, que mudam entre sessões (H05-ERROS-POR-TOM); CRC-16 por pacote, 4 tentativas, CRC-32 no arquivo (xfer.py, recvfile.py).
- Cap. 6: Fig. 9 de F01, H03, F02, F03, F00, F04 (10 cm, 2026-10-08); 11,3 B/s e 5,9 a 9,5% de bits trocados (14-FEC-REP); Fig. 10 de 12-13-SYNC (4/4 e 4/4), H03 (6/8 e 7/8), studies/20260903-111105-ganho-mary (15/24 e 23/24, uma máquina); arquivo 21/21 a 6,8 B/s e 11/11 com 3 retransmissões a 7,2 B/s (15-PKT-ARQ), a 10 cm de 5,0 a 7,6 B/s (F05); enlace 207/207 e 44/44, 302 s (H07-ENLACE-MODOS), 405 s com outro notebook (sessão de 2026-10-27).
- Fora por falta de lastro: resíduo de 5,3 a 6,6 dB dos símbolos anteriores; descarte 15% contra 35%; "479,96 em oito gravações".
