# Compreensão do programa (leitor do programa)

Fontes: `CLAUDE.md` da raiz, `modem.py`, `fec.py`, `xfer.py`, `recvfile.py`, `console.py`, `enlace2.py`, `enlace_manual.py` (por cima) e cabeçalhos de `resultados/`. O artigo não foi lido.

## O que o sistema faz

Um modem acústico: transmite bytes como som pela caixa e os recupera pelo microfone de outra máquina (ou de um celular). Há quatro modulações (2-FSK, 5×2-FSK votada, 5×2-FSK multicanal, 16-FSK), todas a 100 baud exceto o 2-FSK Bell 202 legado a 1200 baud, com um FEC convolucional por cima e um protocolo de pacotes com CRC e pare-e-espere. O enlace pode ser configurado à mão (`enlace_manual`) ou negociado só pelo som (`enlace`/`enlace2`), sem cabo.

## Mecanismos que carregam o resultado

1. **FEC convolucional K=7, taxa 1/3, Viterbi com decisão suave, entrelaçamento.** Sem ele nada fecha: o 2-FSK Bell 202 sem FEC lê ~55% dos bits e entrega 0/5 blocos; com FEC, o 16-FSK lê 89-96% dos bits e entrega o bloco inteiro (`RESUMO-CAMPANHA-FINAL.md`, `F00`-`F06-*-10CM`; 5×2 multicanal fecha 5/5 lendo só 90-93%). A decisão suave sozinha leva a tolerância de 8% para 13% de bits errados (`18-FEC-SIM`, **simulação**).
2. **Palavra de sincronismo de 31 bits achada por correlação** (`fec.find_sync`). Sem ela o caminho rígido do 16-FSK acerta a fase de nibble 4 em 16 vezes (sintético). Todo número confiável vem do caminho com FEC.
3. **Cadeia analógica linear (nível da caixa e do microfone).** A maior alavanca medida, sem mudar o DSP: 16-FSK `fecrep 1` foi de 0/6 para 12/12 blocos (`14-FEC-REP`), arquivo de 1/21 para 21/21 pacotes (`15-PKT-ARQ`); A→B de 0/12 para 8/9 só baixando o volume da caixa (`17-SPK-LEVEL-A2B`).
4. **16-FSK, um tom por vez** (potência total num tom, contra 1/5 no acorde): é a forma mais rápida e confiável no ar, ~11,3 B/s, 12/12 (`14-FEC-REP`).
5. **Piso por tom no 16-FSK** (energia sobre o piso de ruído daquele tom): ligado sempre; o oráculo de piso perfeito empata (88,4 vs 88,3%), ou seja, já está no teto.
6. **Pacotes com CRC + pare-e-espere** (`xfer.py`, `recvfile.py`, `enlace_manual`): arquivo inteiro idêntico — `testcard.bmp` 1334 B, 21/21 sem retransmissão, 6,8 B/s (`15-PKT-ARQ`); 7,6 B/s com 128 B (`F05`); logo 1270 B e bandeira 934 B para o celular (`H08-ARQUIVO-CELULAR`).
7. **Embaralhamento da carga** (`enlace_manual.embaralha`): bandeira sem ele 26/30 pacotes e 4 abandonados; com ele 30/30, 0 retransmissões (`H08`). Uma sessão de cada.
8. **Voto na 5×2-FSK** (não soma de energia): somar dava 27% de bytes certos num enlace real; o voto torna o ganho irrelevante. Polaridade alternada nos pares e teste de presença (`MFSK_PRESENCE_MIN`) evitam viés e decodificação do silêncio.

## Secundários, descartados ou não medidos no ar

- **Duas varreduras (chirps) de sincronismo**: medidas, ganho modesto na média e real nas caudas — 5/8 → 8/8 blocos em `12-13-SYNC`; 16-FSK 5/8 (malha) → 7/8 (`H02`). Seguro contra colapso do portão adiantado/atrasado, não melhora média. Nas 5×2, só sintético.
- **IFK (tom de repetição)**: +1 a +2 pontos de bits em 8/8 pares, sem diferença de blocos (`F06`, `H01`). Secundário.
- **Repetição (`fecrep` 2, 4)**: só compra cauda; no canal linear `fecrep 1` já fecha tudo (`14-FEC-REP`).
- **Descartados por medida**: acorde de 3 tons no 16-FSK (−4,3 dB, pior, `11-MARY-CHORD`); silêncio entre símbolos (`09-MARY-GAP`); banda do detector (`10-MARY-BAND`); piloto por tom (80,9% contra 88,4%); equalizador por tom na 5×2; normalização por símbolo; ultrassom (transdutores não alcançam, a distância).
- **Correção do piso (floor_clip)**: medida só em gravações, piora em nível baixo; padrão não mudou.
- **Subtração da cauda (`G20`)**: offline, empata com IFK; não está no caminho ao vivo.
- **Enlace negociado (`enlace`/`enlace2`)**: medido no ar em poucas sessões — `H06` (sessão 3 completa, 207/207 e 44/44), `H07` (uma sessão por modo, 113-270 s), celular (fechou em 369 s). Muitos de seus detalhes (varredura de tons VERSAO 16, tempos de `LER_CEDO`, `_e_fechamento`, recuperação de lacunas, sonda de 100 baud) são **só simulação**.
- **Quatro formas pelo celular (`H09`)**: 10 cm e 30 cm entregam 10/10 nas quatro, uma sessão cada, rep 3 com folga (taxas 0,8-2,7 B/s não medem limite); a 1 m nenhuma entregou.
- **Distância**: 5×2 multicanal 89% a 30 cm, 81% a 1 m e 69% a 2 m, blocos 1/1, 0/1, 0/1 (`H04`, uma gravação cada).
- Bell 202 a 1200 baud: nunca entregou mensagem; fica como referência.

## Contribuição do trabalho × conceito de terceiros

**Terceiros (padrão):** FSK e tons do Bell 202; MFSK; codificação de Gray; código convolucional K=7 e Viterbi suave; entrelaçamento; CRC; ARQ pare-e-espere; chirp/filtro casado para sincronismo; IFK como ideia; UART 8N1; embaralhamento por XOR.

**Do trabalho:** a montagem e a medição comparativa das quatro formas no mesmo canal acústico real, com gravações reaproveitáveis (`study.py`, `align.py`, réguas separadas: bits no melhor deslizamento × bloco honesto); o diagnóstico de que linearidade analógica pesa mais que DSP; o voto com polaridade alternada e escolha de tons contra harmônicos cruzados na 5×2; o piso por tom com exclusão do vencedor no 16-FSK; o mapeamento de repetição por pares (`pair_map`); as duas varreduras medindo o período de símbolo; o tom de repetição como variante de IFK; o enlace negociado só por som e a porta para Android.

## Critério para votar

Peso alto: FEC suave + sincronismo por correlação, linearidade da cadeia, 16-FSK um-tom, voto na 5×2, pacotes/ARQ com arquivo idêntico, embaralhamento (com ressalva de n=1). Peso baixo: IFK, varreduras (ganho de cauda), variantes descartadas, detalhes de temporização e protocolo do `enlace2` não medidos no ar.
