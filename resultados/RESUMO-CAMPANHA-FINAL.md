# Resumo da campanha final (2026-10-08)

Bancada: B (Windows) toca pelo alto-falante Realtek no P2, aprimoramentos desligados, a 10 cm do microfone de A e apontado; A (Linux) grava pelo mic interno (Mic1), Dmic0 45 = -5 dB, Capture 39 = +12 dB. Controle por túnel SSH. Um sentido (B -> A), 48 B aleatórios, `fecrep 1`, ganho 0,5. Commit `213366c` na passada A (16:47) e `c57fc74` nas rodadas r1 a r4 (17:25 a 17:37). **Duas posições:** o PC foi movido levemente entre a passada A (posição 1) e as rodadas (posição 2); a cauda do tom um símbolo depois passou de -14,6 dB para cerca de -11 dB. Medianas por posição não devem ser misturadas. Uma gravação por método e posição (n = 1 na posição 1, n = 4 na posição 2).

## Tabela principal (bits antes do FEC, melhor deslizamento)

| método (nome do artigo) | bits/símbolo | taxa útil | posição 1 (passada A) | posição 2 (r1-r4): mediana [faixa] | blocos fechados |
|---|---|---|---|---|---|
| 2-FSK (Bell 202), sem FEC | 1 | 97,6 B/s nominal | 54,87 % | 54,66 % [54,37-55,04] | 0/5 |
| 5×2-FSK votada + FEC | 1 | 3,7 B/s | 100,00 % | 99,04 % [79,10-99,33] | 4/5 |
| 5×2-FSK multicanal + FEC | 5 | 13,8 B/s | 93,13 % | 90,91 % [90,26-91,85] | 5/5 |
| 16-FSK + FEC (F00, sem varreduras) | 4 | 11,2 B/s | 99,67 % | 95,42 % [92,92-98,33] | 3/5 |
| 16-FSK + FEC, duas varreduras (F04) | 4 | 10,7 B/s | 100,00 % | 95,38 % [94,59-97,09] | 5/5 |
| 16-FSK + IFK + FEC, duas varreduras (F06) | 4 | 10,7 B/s | 98,75 % | 98,09 % [96,75-99,08] | 5/5 |

Régua das varreduras (`align.py`), posição 2: F04 gate 95,35 [94,6-97,1], relógio travado 96,40 [95,6-97,3], duas varreduras 96,20 [94,6-96,8]; F06 gate 98,10, travado 98,65, varreduras 98,55 [98,2-99,4]. Todos 4/4 blocos. O 2-FSK sem FEC lê ~55 % dos bits (acaso é 50 %) e não entrega o bloco; só a taxa nominal é alta. As taxas vêm do código. O 5×2 multicanal fechou 5/5 lendo só 90 a 93 % dos bits. Pastas `F00..F06-*-10CM`.

## Arquivo inteiro (`testcard.bmp`, 1334 B, `cmp` idêntico nas três)

| corrida | pacote | retransmissões | tempo | taxa |
|---|---|---|---|---|
| 1ª (posição 1) | 64 B | 7 | 267 s | 5,0 B/s |
| bloco 3 (posição 2) | 64 B | 5 | 253 s | 5,3 B/s |
| bloco 3 (posição 2) | 128 B | 2 | 175 s | **7,6 B/s** (antes 7,2 em `15-PKT-ARQ`, sem retransmissões) |

## Caracterização, a 10 cm (`G00` a `G03`)

- **C0 piso (`G00-PISO`):** -43,5 dBFS no início (eventos passageiros) e -64,6 dBFS no fim; faixa dos tons de -49 a -64 contra -84 a -92 dBFS.
- **C1 tons (`G01-TONS`):** margem sobre o piso de +38,5 a +76,5 dB, espalhamento <= 0,5 dB. 16 tons do 16-FSK +56,3 a +76,5; **tom R do IFK (3487,5 Hz) +56,3 dB**; **4000/4500/5000 Hz +59,5/+61,0/+60,1 dB, sem colapso acima de 4 kHz**. Nesta bancada isso qualifica o CLAUDE.md (SNR 12/8/0 dB nesses pontos a distância; ultrassom "não viável"); a 10 cm o corte não aparece. Não vale para o enlace a metros.
- **C2 varredura (`G02-VARREDURA`):** SNR de 43,5 a 61,3 dB (mediana 55,1) em 400-4200 Hz; nível relativo 0 a -19,5 dB; vizinhos de 50 Hz diferem 2,1 dB na mediana (10,4 no máximo): pente raso.
- **C3 linearidade (`G03-LINEARIDADE`):** tom de 1000 Hz sobe 5,9/6,0/6,0 dB por dobra de ganho (0,125 a 1,0); H2 -37 a -45 dBc, H3 -54 a -60 dBc, sem crescer com o ganho. Burst 16-FSK: ganho 0,25 -> 95,9 % bits, bloco não; 1,0 -> 97,0 %, bloco sim, pico 0,36. **O ganho não muda o resultado.**

## IFK (tom de repetição): pares F06 menos F04

Posição 2, r1 a r4: o IFK ganhou 4/4 em todas as réguas, de +0,9 a +4,1 pt (malha +0,9, +2,0, +3,7, +3,0; duas varreduras +2,1, +2,6, +4,1, +2,1). Passada A (posição 1): -1,2 pt (F04 já em 100 %). Ressalva: o F06 foi sempre gravado logo depois do F04, sem ordem alternada.

## Subtração da cauda (offline, `G20-SUBTRAI-CAUDA`)

Bits antes do FEC, atual -> subtração cega k=1..3 piso cru -> com ganho ×4: eco 85,8 -> 89,0 -> 90,4 %; moderado 89,2 -> 91,4 -> 92,3 %; limpo 99,9 -> 100,0 %. 9 melhores, 1 igual, 0 piores em 10 gravações sem IFK; blocos no eco 3/6 -> 5/6. Só receptor, sem mudar o fio. **Variante escolhida nos mesmos dados; precisa de validação**, em especial nas rodadas r1 a r4.

## O achado da bancada

Os blocos que fecham ou não dependem da **queda do tom um símbolo depois**, não do ganho: -5 dB não fecha, -8 dB fecha metade, -11 e -15 dB fecham (`G10-FIGURAS-CANAL/A-eco-por-posicao`, `cauda/`). Mover levemente o PC levou o F04 de 100 % (passada A) para mediana 95,4 % e o F00 de 1/1 para 2/4 blocos. A caixa a 10 cm resolveu o que o ganho digital e o volume do Windows não resolviam (`F00-NIVEL`, `F00-AJUSTE`, `G03`).

## A -> B

Sentido pior, como já registrado em `INVESTIGACAO-A2B.md`: cerca de 72 % de bits no melhor microfone (WDM-KS), com o processamento de áudio do Windows no caminho. Não foi refeito nesta campanha.

## Pastas

Novas (sufixo `-10CM` = esta bancada): `F00-NIVEL-10CM`, `F01-2FSK-10CM`, `F02-5X2-VOTADA-10CM`, `F03-5X2-MULTICANAL-10CM`, `F04-16FSK-10CM`, `F05-ARQUIVO-10CM`, `F06-16FSK-IFK-10CM`, `G00-PISO`, `G01-TONS`, `G02-VARREDURA`, `G03-LINEARIDADE`, `G20-SUBTRAI-CAUDA`, `G10-FIGURAS-CANAL` (figuras; `cauda/` acrescentada). Bancada anterior, não alterada: `F00-NIVEL`, `F00-AJUSTE`, `F00-NIVEL-A2B`, `F01-2FSK`, `F02-5X2-VOTADA`, `F03-5X2-MULTICANAL`, `F04-16FSK`, `F05-ARQUIVO`, `F06-16FSK-IFK`. Planos: `PLANO-FINAL.md`, `PLANO-AFK.md`.
