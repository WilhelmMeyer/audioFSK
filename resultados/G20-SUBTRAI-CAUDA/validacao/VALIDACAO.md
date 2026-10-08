# Validação fora da amostra: subtração da cauda (G20), variante congelada

Data 2026-10-08, código em `6f03e47`. Só leitura de `captures/`: nada foi gravado, transmitido ou alterado no repositório.

## O que foi congelado (de `resultados/G20-SUBTRAI-CAUDA/RESULTADO.md`, sem reajuste)

- **(d) variante congelada**: subtração cega k=1..3, piso corrente atualizado com a energia **crua**, a_k cego ×4 → `subtrai.receive(E, ifk, K=3, upd='raw', gscale=4)` com os padrões do script (beta=0.02, piso inferior 0.1×piso, a_k em [0, 0.5] antes do ×4). `subtrai.py` é cópia literal do G20 (só o `sys.path` mudou).
- (a) receptor atual (`receive(E, False)`); conferido contra o `MaryDemodulator` real no mesmo relógio: decisões idênticas (1,000) nas 26 gravações, inclusive (b) nas f06.
- (b) IFK atual (`exclude=True`), só nas f06.
- (c) referência: cega k=1, piso cru, sem ×4. Também listada k=1..3 ×1 (piso cru).
- (e) oráculo: tons anteriores verdadeiros, a_k por MQ × fator escolhido na própria gravação (grade 1–16, por bits), piso cru — como `ganho.py`. Teto otimista, não receptor.
- Relógio congelado no melhor (offset, período) por força bruta, como `subtrai.align`. Métricas no corpo após 120 símbolos de preâmbulo: % símbolos / % bits antes do FEC / bloco (`find_sync` + `decode`).

## Corpus (nenhuma gravação usada na escolha da variante)

B->A, 48 B, fecrep 1, caixa a ~10 cm, ganho 0.5 (g03: 0.25 e 1.0). 26 gravações, todas completas (amostras = `samples` do json):
- f00 (sem varreduras) r1–r8: 172516, 172925, 173308, 173510, 180602, 180723, 180848, 181001
- f04 (sync_chirp) r1–r8: 172827, 173137, 173422, 173612, 180544, 180656, 180819, 180940
- f06 (sync_chirp + ifk) r1–r8: 172852, 173217, 173441, 173631, 180524, 180625, 180752, 180922
- g03-burst-g0.25 (171753), g03-burst-g1.0 (172251) — grupo próprio, fora das médias f00/f04.

r1–r4 na ordem f00→f04→f06; r5–r8 na ordem f06→f04→f00 (f04/f06 r5–r8 também em `resultados/H01-IFK-ORDEM-INVERTIDA/`, f00 r5–r8 em `resultados/H02-16FSK-MALHA/`). Conferido no json de cada uma das 26: modo mary, ganho 0.5 (g03 à parte), fec_repeat 1, 48 B, sync_chirp/ifk conforme o grupo; seeds distintos.

**O canal ficou mais limpo do que o "moderado" do G20**: (a) lê 97,2 % dos bits aqui contra 89,2 % lá. Por isso todo bloco foi recuperado por todos os receptores (26/26): blocos não discriminam nada neste corpus; o veredito é sobre bits/símbolos pareados.

## Resumo

| grupo | n | (a) atual | (c) k=1 | k=1..3 ×1 | **(d) congelada** | (e) oráculo | (d) vs (a): melhor/igual/pior | pior Δ |
|---|---|---|---|---|---|---|---|---|
| f00 | 8 | 97,46 | 98,06 | 98,11 | **98,68** | 98,83 | 8/0/0 | +0,25 |
| f04 | 8 | 96,91 | 97,61 | 97,82 | **98,44** | 98,80 | 8/0/0 | +1,00 |
| f00+f04 | 16 | 97,18 | 97,84 | 97,97 | **98,56** | 98,82 | 16/0/0 | +0,25 |
| g03 | 2 | 98,04 | 98,25 | 98,54 | **98,50** | 98,92 | 2/0/0 | +0,25 |
| símbolos f00+f04 | 16 | 94,25 | 95,42 | 95,69 | **96,71** | 97,17 | | |

(bits % antes do FEC; melhor/igual/pior com limiar ±0,05 pp como `tabela.py`.)

Erros de bit f00+f04: 2,82 % → 1,44 % (−49 %); de símbolo: 5,75 % → 3,29 % (−43 %). A variante cobre ~84 % da distância do (a) ao oráculo (1,38 de 1,64 pp).
Previsão dentro da amostra (G20, regime moderado, n=2): 89,2 → 92,3 (+3,1 pp, erros −29 %). Fora da amostra: +1,38 pp absolutos, mas −49 % relativos; sinal e ordenação das variantes (a < c < k1..3 ×1 < d < e) iguais aos do G20.

f06 (IFK no fio), bits %, média de 8:

| (b) IFK atual | IFK + k=1..3 ×1 | IFK + (d) ×4 * | 17 tons sem exclusão | 17 tons + (c) | 17 tons + k=1..3 ×1 | 17 tons + (d) ×4 | oráculo 17 t |
|---|---|---|---|---|---|---|---|
| 98,49 | 98,61 (3/3/2 vs b) | 98,70 (4/2/2) | 97,47 (0/0/8) | 98,07 (0/0/8) | 98,18 (2/0/6) | 98,60 (3/2/3) | 98,81 |

\* IFK + ×4 nunca foi pontuado no G20: primeira medida, não validação. Pior Δ contra (b): −0,08 pp (IFK+subtração) e −0,25 pp (17 tons + ×4); nenhum bloco perdido.
Pares da mesma rodada (segundos de diferença, ordem invertida em r5–r8): f04 + (d) 98,44 vs f06 (b) 98,49 — empate (4 rodadas para cada lado). Ao contrário do G20, aqui o IFK atual superou o f04 atual (+1,6 pp); parte disso é gravação, não método.

Contra a sua própria linha de base nas f06 (17 tons sem exclusão → 17 tons + (d)): 97,47 → 98,60, melhor em 8 de 8. Somando, (d) melhora a linha de base sem exclusão em **26 de 26** gravações (16 f00/f04 + 8 f06 + 2 g03).

**Três afirmações secundárias do G20 não se repetiram fora da amostra:** (i) "o IFK nunca superou o simples atual" — aqui (b) superou o f04 (a) em 8 de 8 rodadas (+1,6 pp), também em r5–r8 com a ordem invertida; (ii) "simples + subtração supera o IFK" — aqui empatam (98,44 vs 98,49, 4 rodadas para cada lado); (iii) "IFK + subtração soma ~+1 pp" — aqui +0,1 a +0,2 pp. A subtração está validada contra o receptor sem exclusão; não há evidência fora da amostra de que substitua o IFK nem de que o melhore.

## Conclusão

1. Sim, a variante congelada se sustenta fora da amostra: melhorou bits em 26 de 26 gravações contra o receptor sem exclusão (16 f00/f04, 8 f06 a 17 tons, 2 g03), com a ordenação das variantes igual à do G20.
2. Rende +1,4 pp de bits antes do FEC (97,2 → 98,6; −49 % dos erros de bit, −43 % de símbolo), ~84 % do caminho até o oráculo; em blocos, nada mensurável (26/26 já íntegros a fecrep 1).
3. Regressão: nenhuma sem IFK (pior Δ +0,25 pp, nenhum ok→FALHA); com IFK a subtração é neutra (+0,1–0,2 pp, 2 de 8 piores por −0,08 pp), e 17 tons sem exclusão + ×4 apenas empata com o IFK atual; ao contrário do G20, não ganha do IFK.
4. Ressalvas: canal mais limpo que o do G20 (ganho absoluto menor, blocos sem poder discriminante); relógio no melhor offset por força bruta, não o gate; pares f04/f06 gravados em ordem alternada.

## Arquivos

`valida.py` (pontua uma gravação → `out-<stem>.json`, cache `cache-<stem>.pkl`), `../subtrai.py` (G20), `resumo.py` → `resumo.txt` (abaixo). Refazer: `for s in $(cat stems2.txt); do ./venv/bin/python valida.py $s; done; ./venv/bin/python resumo.py`.

## Tabelas por gravação (símb % / bits % / bloco)

checks {'171753-g03-burst-g0.25': 1.0, '172251-g03-burst-g1.0': 1.0, '172516-f00-nivel-10cm-r1': 1.0, '172827-f04-16fsk-10cm-r1': 1.0, '172852-f06-16fsk-ifk-10cm-r1': 1.0, '172925-f00-nivel-10cm-r2': 1.0, '173137-f04-16fsk-10cm-r2': 1.0, '173217-f06-16fsk-ifk-10cm-r2': 1.0, '173308-f00-nivel-10cm-r3': 1.0, '173422-f04-16fsk-10cm-r3': 1.0, '173441-f06-16fsk-ifk-10cm-r3': 1.0, '173510-f00-nivel-10cm-r4': 1.0, '173612-f04-16fsk-10cm-r4': 1.0, '173631-f06-16fsk-ifk-10cm-r4': 1.0, '180524-f06-16fsk-ifk-10cm-r5': 1.0, '180544-f04-16fsk-10cm-r5': 1.0, '180602-f00-nivel-10cm-r5': 1.0, '180625-f06-16fsk-ifk-10cm-r6': 1.0, '180656-f04-16fsk-10cm-r6': 1.0, '180723-f00-nivel-10cm-r6': 1.0, '180752-f06-16fsk-ifk-10cm-r7': 1.0, '180819-f04-16fsk-10cm-r7': 1.0, '180848-f00-nivel-10cm-r7': 1.0, '180922-f06-16fsk-ifk-10cm-r8': 1.0, '180940-f04-16fsk-10cm-r8': 1.0, '181001-f00-nivel-10cm-r8': 1.0}

## Plain
| gravacao | pico | (a) atual | (c) k=1 cega | k=1..3 ×1 | **(d) k=1..3 ×4** | (e) oraculo (fator) | Δbits d-a | a_k final |
|---|---|---|---|---|---|---|---|---|
| 172516-f00-nivel-10cm-r1 | 0.17 | 94.3 / 97.58 / ok | 95.3 / 98.17 / ok | 95.3 / 98.17 / ok | **96.3 / 98.67 / ok** | 96.7 / 98.75 / ok (×6) | +1.08 | [0.0565, 0.014, 0.0016] |
| 172925-f00-nivel-10cm-r2 | 0.19 | 95.3 / 97.92 / ok | 96.0 / 97.92 / ok | 96.3 / 98.17 / ok | **96.7 / 98.17 / ok** | 96.7 / 98.50 / ok (×2) | +0.25 | [0.0498, 0.0202, 0.0] |
| 173308-f00-nivel-10cm-r3 | 0.17 | 97.3 / 98.92 / ok | 97.7 / 99.17 / ok | 97.7 / 99.08 / ok | **98.7 / 99.50 / ok** | 98.7 / 99.50 / ok (×8) | +0.58 | [0.0556, 0.011, 0.0019] |
| 173510-f00-nivel-10cm-r4 | 0.18 | 93.0 / 96.50 / ok | 94.0 / 97.08 / ok | 94.3 / 97.17 / ok | **95.0 / 97.92 / ok** | 95.7 / 98.17 / ok (×4) | +1.42 | [0.039, 0.0107, 0.009] |
| 180602-f00-nivel-10cm-r5 | 0.18 | 95.3 / 98.17 / ok | 95.7 / 98.42 / ok | 96.3 / 98.67 / ok | **97.3 / 99.00 / ok** | 97.7 / 99.08 / ok (×6) | +0.83 | [0.0453, 0.0258, 0.0] |
| 180723-f00-nivel-10cm-r6 | 0.18 | 92.3 / 96.75 / ok | 94.7 / 97.83 / ok | 95.3 / 98.00 / ok | **96.7 / 98.75 / ok** | 97.3 / 99.08 / ok (×12) | +2.00 | [0.0421, 0.0207, 0.0076] |
| 180848-f00-nivel-10cm-r7 | 0.18 | 95.7 / 97.17 / ok | 97.3 / 98.33 / ok | 97.0 / 98.08 / ok | **97.3 / 98.42 / ok** | 97.7 / 98.75 / ok (×2) | +1.25 | [0.0586, 0.0367, 0.0087] |
| 181001-f00-nivel-10cm-r8 | 0.18 | 93.3 / 96.67 / ok | 94.7 / 97.58 / ok | 94.7 / 97.58 / ok | **97.3 / 99.00 / ok** | 97.0 / 98.83 / ok (×6) | +2.33 | [0.0522, 0.0092, 0.0014] |
| 172827-f04-16fsk-10cm-r1 | 0.18 | 93.3 / 96.67 / ok | 95.0 / 97.42 / ok | 95.0 / 97.42 / ok | **96.7 / 98.25 / ok** | 96.7 / 98.58 / ok (×12) | +1.58 | [0.05, 0.0156, 0.0134] |
| 173137-f04-16fsk-10cm-r2 | 0.20 | 93.7 / 96.75 / ok | 95.0 / 97.67 / ok | 95.0 / 97.67 / ok | **96.7 / 98.67 / ok** | 97.0 / 98.75 / ok (×6) | +1.92 | [0.0492, 0.0253, 0.0045] |
| 173422-f04-16fsk-10cm-r3 | 0.17 | 92.3 / 95.75 / ok | 93.3 / 96.50 / ok | 93.7 / 96.92 / ok | **95.0 / 97.58 / ok** | 96.3 / 98.25 / ok (×8) | +1.83 | [0.0434, 0.0176, 0.0058] |
| 173612-f04-16fsk-10cm-r4 | 0.17 | 95.0 / 97.42 / ok | 96.7 / 98.33 / ok | 97.0 / 98.50 / ok | **97.3 / 98.83 / ok** | 97.7 / 99.00 / ok (×6) | +1.42 | [0.0475, 0.017, 0.0037] |
| 180544-f04-16fsk-10cm-r5 | 0.17 | 93.3 / 96.67 / ok | 94.0 / 97.00 / ok | 94.7 / 97.33 / ok | **96.0 / 98.25 / ok** | 97.0 / 98.58 / ok (×6) | +1.58 | [0.0516, 0.0205, 0.0051] |
| 180656-f04-16fsk-10cm-r6 | 0.18 | 93.0 / 96.58 / ok | 94.7 / 97.42 / ok | 94.7 / 97.42 / ok | **96.0 / 98.17 / ok** | 97.7 / 99.25 / ok (×16) | +1.58 | [0.0451, 0.0148, 0.0058] |
| 180819-f04-16fsk-10cm-r7 | 0.18 | 95.0 / 97.67 / ok | 96.0 / 98.42 / ok | 96.7 / 98.75 / ok | **96.3 / 98.67 / ok** | 96.7 / 98.75 / ok (×8) | +1.00 | [0.0535, 0.0134, 0.0] |
| 180940-f04-16fsk-10cm-r8 | 0.20 | 95.7 / 97.75 / ok | 96.7 / 98.17 / ok | 97.3 / 98.58 / ok | **98.0 / 99.08 / ok** | 98.3 / 99.25 / ok (×8) | +1.33 | [0.0482, 0.015, 0.0] |
| 171753-g03-burst-g0.25 | 0.10 | 95.0 / 98.00 / ok | 95.0 / 97.83 / ok | 95.7 / 98.33 / ok | **95.3 / 98.25 / ok** | 96.0 / 98.67 / ok (×2) | +0.25 | [0.053, 0.029, 0.0015] |
| 172251-g03-burst-g1.0 | 0.36 | 95.7 / 98.08 / ok | 96.7 / 98.67 / ok | 96.7 / 98.75 / ok | **96.7 / 98.75 / ok** | 98.0 / 99.17 / ok (×6) | +0.67 | [0.0444, 0.028, 0.0012] |

## IFK
| gravacao | (b) IFK atual | IFK + k=1..3 ×1 | IFK + k=1..3 ×4 | 17 tons s/ exclusao | 17 tons + (c) k=1 | 17 tons + k=1..3 ×1 | 17 tons + (d) ×4 | oraculo (17 t) |
|---|---|---|---|---|---|---|---|---|
| 172852-f06-16fsk-ifk-10cm-r1 | 95.0 / 97.75 / ok | 95.7 / 98.33 / ok | 96.3 / 98.58 / ok | 94.0 / 97.00 / ok | 95.0 / 97.67 / ok | 95.3 / 97.92 / ok | 96.7 / 98.50 / ok | 97.3 / 98.67 / ok (×4) |
| 173217-f06-16fsk-ifk-10cm-r2 | 99.3 / 99.58 / ok | 99.3 / 99.50 / ok | 99.3 / 99.50 / ok | 98.0 / 98.92 / ok | 98.3 / 99.08 / ok | 98.3 / 99.08 / ok | 99.0 / 99.33 / ok | 99.3 / 99.50 / ok (×12) |
| 173441-f06-16fsk-ifk-10cm-r3 | 96.7 / 98.25 / ok | 96.7 / 98.25 / ok | 96.7 / 98.25 / ok | 94.7 / 96.67 / ok | 96.3 / 98.08 / ok | 96.3 / 98.08 / ok | 96.7 / 98.25 / ok | 97.3 / 98.75 / ok (×6) |
| 173631-f06-16fsk-ifk-10cm-r4 | 98.3 / 99.08 / ok | 98.7 / 99.42 / ok | 99.0 / 99.58 / ok | 97.0 / 98.42 / ok | 97.3 / 98.50 / ok | 97.7 / 98.83 / ok | 98.7 / 99.42 / ok | 99.0 / 99.58 / ok (×16) |
| 180524-f06-16fsk-ifk-10cm-r5 | 94.7 / 97.17 / ok | 94.7 / 97.17 / ok | 95.0 / 97.33 / ok | 92.0 / 96.33 / ok | 92.7 / 96.33 / ok | 92.7 / 96.33 / ok | 94.3 / 97.00 / ok | 95.0 / 97.25 / ok (×12) |
| 180625-f06-16fsk-ifk-10cm-r6 | 96.7 / 98.83 / ok | 96.7 / 98.83 / ok | 96.7 / 98.83 / ok | 93.0 / 96.75 / ok | 95.0 / 98.17 / ok | 95.0 / 98.17 / ok | 96.3 / 98.83 / ok | 96.3 / 98.75 / ok (×6) |
| 180752-f06-16fsk-ifk-10cm-r7 | 96.7 / 98.58 / ok | 97.0 / 98.83 / ok | 97.3 / 98.92 / ok | 94.3 / 98.17 / ok | 94.7 / 98.33 / ok | 95.3 / 98.67 / ok | 97.0 / 98.92 / ok | 97.7 / 99.08 / ok (×6) |
| 180922-f06-16fsk-ifk-10cm-r8 | 97.3 / 98.67 / ok | 97.3 / 98.58 / ok | 97.3 / 98.58 / ok | 95.0 / 97.50 / ok | 96.3 / 98.42 / ok | 96.3 / 98.33 / ok | 97.3 / 98.58 / ok | 97.7 / 98.92 / ok (×12) |

### f00
n=8 | variante | simb % | bits % | blocos | Δbits vs a media | melhor/igual/pior | pior Δ | ok->FALHA
| a | 94.58 | 97.46 | 8/8 | +0.00 | 0/8/0 | +0.00 | [] |
| c | 95.67 | 98.06 | 8/8 | +0.60 | 7/1/0 | +0.00 | [] |
| d1 | 95.88 | 98.11 | 8/8 | +0.66 | 8/0/0 | +0.17 | [] |
| d | 96.92 | 98.68 | 8/8 | +1.22 | 8/0/0 | +0.25 | [] |
| e | 97.17 | 98.83 | 8/8 | +1.38 | 8/0/0 | +0.58 | [] |

### f04
n=8 | variante | simb % | bits % | blocos | Δbits vs a media | melhor/igual/pior | pior Δ | ok->FALHA
| a | 93.92 | 96.91 | 8/8 | +0.00 | 0/8/0 | +0.00 | [] |
| c | 95.17 | 97.61 | 8/8 | +0.71 | 8/0/0 | +0.33 | [] |
| d1 | 95.50 | 97.82 | 8/8 | +0.92 | 8/0/0 | +0.67 | [] |
| d | 96.50 | 98.44 | 8/8 | +1.53 | 8/0/0 | +1.00 | [] |
| e | 97.17 | 98.80 | 8/8 | +1.90 | 8/0/0 | +1.08 | [] |

### g03
n=2 | variante | simb % | bits % | blocos | Δbits vs a media | melhor/igual/pior | pior Δ | ok->FALHA
| a | 95.33 | 98.04 | 2/2 | +0.00 | 0/2/0 | +0.00 | [] |
| c | 95.83 | 98.25 | 2/2 | +0.21 | 1/0/1 | -0.17 | [] |
| d1 | 96.17 | 98.54 | 2/2 | +0.50 | 2/0/0 | +0.33 | [] |
| d | 96.00 | 98.50 | 2/2 | +0.46 | 2/0/0 | +0.25 | [] |
| e | 97.00 | 98.92 | 2/2 | +0.88 | 2/0/0 | +0.67 | [] |

### f00+f04
n=16 | variante | simb % | bits % | blocos | Δbits vs a media | melhor/igual/pior | pior Δ | ok->FALHA
| a | 94.25 | 97.18 | 16/16 | +0.00 | 0/16/0 | +0.00 | [] |
| c | 95.42 | 97.84 | 16/16 | +0.66 | 15/1/0 | +0.00 | [] |
| d1 | 95.69 | 97.97 | 16/16 | +0.79 | 16/0/0 | +0.17 | [] |
| d | 96.71 | 98.56 | 16/16 | +1.38 | 16/0/0 | +0.25 | [] |
| e | 97.17 | 98.82 | 16/16 | +1.64 | 16/0/0 | +0.58 | [] |

### f06
n=8 | variante | simb % | bits % | blocos | Δbits vs b media | melhor/igual/pior | pior Δ | ok->FALHA
| b | 96.83 | 98.49 | 8/8 | +0.00 | 0/8/0 | +0.00 | [] |
| b+d1 | 97.00 | 98.61 | 8/8 | +0.12 | 3/3/2 | -0.08 | [] |
| b+d | 97.21 | 98.70 | 8/8 | +0.21 | 4/2/2 | -0.08 | [] |
| a | 94.75 | 97.47 | 8/8 | -1.02 | 0/0/8 | -2.08 | [] |
| c | 95.71 | 98.07 | 8/8 | -0.42 | 0/0/8 | -0.83 | [] |
| d1 | 95.88 | 98.18 | 8/8 | -0.31 | 2/0/6 | -0.83 | [] |
| d | 97.00 | 98.60 | 8/8 | +0.11 | 3/2/3 | -0.25 | [] |
| e | 97.46 | 98.81 | 8/8 | +0.32 | 6/0/2 | -0.08 | [] |
