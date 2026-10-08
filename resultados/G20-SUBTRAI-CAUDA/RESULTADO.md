# Subtração da cauda dos símbolos anteriores vs IFK (16-FSK, B->A, 48 B, fecrep 1)

Gerado em 2026-10-08 por `subtrai.py` (+ `tabela.py`) nesta pasta. Nada gravado; só leitura de `captures/`.

## Método
- Relógio congelado no melhor (offset, período) por força bruta (período 479.5–480.5, offset ±27 amostras) contra os tons transmitidos reconstruídos (`spectro.tx_tone_indices`, IFK incluso: tom 16 = 3487.5 Hz). Mesma matriz de energias (janela 408 amostras após guarda de 72) para todas as variantes.
- Receptor reimplementado sobre essa matriz: piso corrente igual ao `MaryDemodulator` (floor_top=1, alpha=0.02), LLR max-log igual ao `demodulate_soft` (IFK: max(tom próprio, tom 17 se v == valor anterior)). Conferência: decisões **idênticas (1.000)** ao `MaryDemodulator` real nas 13 gravações, para (a) e para (b).
- Subtração: `e[t] -= a_k * E[n-k, d(n-k)]` só no tom decidido em n-k, k=1..K; piso inferior 0.1×piso. `a_k` **cego e online**: razão de duas EMAs (beta=0.02) — numerador `E[n,t]-piso[t]` **com sinal** (ruído puro dá ~0, sem retificação), denominador `E[n-k,t]` — nos símbolos em que t=d(n-k) não venceu em n nem foi decidido em lag menor; usado com clamp [0, 0.5].
- "piso cru": a subtração só muda a decisão/LLR; o piso corrente continua atualizado com a energia crua (como hoje). Sem o sufixo, o piso é atualizado com a energia já corrigida.
- (e) oráculo: tons anteriores VERDADEIROS, `a_k` por mínimos quadrados com piso genie × fator escolhido na própria gravação. Na tabela completa abaixo o oráculo usa piso corrigido e grade 0.5–3 (desfavorecido); o resumo usa a versão refeita com piso cru e grade 1–16 (`oraculo_cru.py`, `ganho.py`).
- Métricas no corpo (após 120 símbolos de preâmbulo): % símbolos (tom), % bits antes do FEC (valor decidido vs valor transmitido = sinal do LLR), bloco = `fec.find_sync` + `fec.decode` sobre o LLR do quadro todo.
- Sem IFK em gravações f06 o receptor (a) não lê o tom 17; ali "a IFK sem exclusão" = 17 tons, tom 17 → valor anterior, sem excluir ninguém; "c/d" nas f06 = isso + subtração; "IFK + cega" = IFK atual + subtração.

## Resumo por regime (média de bits % antes do FEC; blocos íntegros entre parênteses)

Todas as subtrações abaixo com piso corrente atualizado pela energia **crua** (melhor que a corrigida em todos os regimes; ver tabela completa). "×4" = a_k cego multiplicado por 4 (sobre-subtração; ver nota). Oráculo = tons anteriores verdadeiros, a_k por MQ × fator escolhido na própria gravação (grade 1–16), piso cru.

| regime (sem IFK) | n | (a) atual | (c) cega k=1 | (d) cega k=1..3 | (d) k=1..3 ×4 | (e) oráculo k=1..3 | pior Δ (d) vs (a) |
|---|---|---|---|---|---|---|---|
| eco | 6 | 85.8 (3/6) | 87.9 (4/6) | 89.0 (5/6) | **90.4 (5/6)** | 90.4 (5/6) | +1.9 pp |
| moderado | 2 | 89.2 (1/2) | 90.7 (1/2) | 91.4 (1/2) | **92.3 (1/2)** | 93.4 (2/2) | +1.7 pp |
| limpo | 2 | 99.9 (2/2) | 99.9 (2/2) | 100.0 (2/2) | 100.0 (2/2) | 100.0 (2/2) | 0.0 pp |

Contagem (d) vs (a), bits: eco 6 melhores/0 iguais/0 piores, moderado 2/0/0, limpo 1/1/0 → **9 melhores, 1 igual, 0 piores**.

| gravações IFK (n=1 cada) | (b) IFK atual | 17 tons sem exclusão | 17 tons + cega k=1..3 | 17 tons + cega ×4 | IFK + cega k=1..3 | oráculo k=1..3 |
|---|---|---|---|---|---|---|
| eco 162241 | 85.3 (falha) | 82.6 | 85.1 | 87.5 | 86.3 (ok) | 89.6 |
| moderado 162936 | 88.3 (falha) | 86.8 | 87.7 | 89.0 | 89.9 (ok) | 91.0 |
| limpo 164852 | 99.4 (ok) | 99.5 | 99.5 | 100.0 | 99.4 (ok) | 100.0 |

Pares gravados com segundos de diferença (f04 transmissor simples vs f06 transmissor IFK), bits:
- receptor atual nos dois: eco 85.2 vs 85.3 (−0.1), moderado 90.6 vs 88.3 (+2.3) → parte da diferença é a gravação/transmissor, não a subtração.
- ganho próprio da subtração sobre o f04: eco +3.2 (k=1..3) / +5.0 (×4) pp; moderado +2.6 / +2.9 pp.
- blocos: só o do eco (162232) foi fechado pela subtração; 162926 já decodificava sem ela.

Nota sobre a_k: o estimador cego subestima (eco a_1 ≈ 0.10–0.23 vs MQ-oráculo 0.25–0.66) porque descarta os símbolos em que o eco venceu, e o ótimo por bits fica 2–6× acima do MQ (sobre-subtrair = exclusão parcial e suave). Por isso o ×4 cego empata com o oráculo no eco. ×8 começa a piorar (eco 88.9) e no limpo custa 1 símbolo (164832 99.92). a_k cego finais: eco 0.10–0.24/0.05–0.13/0.02–0.08; moderado ≈0.04/0.01–0.02/0.01–0.02; limpo ≈0.03/0.03–0.06/0.00–0.01. Dados: `oraculo_cru.txt`, `ganho.txt`.

## Conclusão
1. Vale implementar, só no receptor e sem mudar o fio: subtração cega k=1..3 com piso cru melhorou bits em 9 de 10 gravações sem IFK (1 igual, 0 pior): eco +3.1 pp, moderado +2.1 pp; com ganho ×4 sobre o a_k cego, +4.6 e +3.1 pp, empatando com o oráculo no eco (90.4) e 1 pp abaixo dele no moderado.
2. Contra o IFK: transmissor simples + subtração ganha 3–5 pp de bits sobre o próprio receptor atual; o IFK (b) nunca superou o simples atual nos pares (−0.1 e −2.3 pp). IFK + subtração soma ~+1 pp ao IFK, mas não alcança o simples + subtração.
3. k: k=1..3 (k=1 sozinho dá ~2/3 do ganho); atualizar o piso com energia crua; a_k cego com fator de escala 2–4 (o cego subestima sistematicamente).
4. Canal limpo: sem regressão em nenhuma variante até ×4 (99.9→100.0; IFK 99.4→100.0); ×8 começa a custar símbolo.
5. Ressalvas: n pequeno (6/2/2 + 3 IFK) e variante vencedora (piso cru, k=3, ×4) escolhida nos mesmos dados em que é pontuada — validar num corpus novo; relógio congelado no melhor offset por força bruta, não o gate; blocos a fecrep 1 são ruidosos.

## Tabela completa por gravação
| gravacao | regime | variante | simb % | bits % | bloco |
|---|---|---|---|---|---|
| 161343-f00-nivel | eco | a atual | 69.7 | 84.6 | FALHA |
| 161343-f00-nivel | eco | c/d cega k=1..1 | 76.7 | 88.4 | FALHA |
| 161343-f00-nivel | eco | cega k=1..1 piso cru | 77.0 | 88.8 | FALHA |
| 161343-f00-nivel | eco | c/d cega k=1..2 | 77.0 | 88.9 | FALHA |
| 161343-f00-nivel | eco | cega k=1..2 piso cru | 78.7 | 89.7 | FALHA |
| 161343-f00-nivel | eco | c/d cega k=1..3 | 77.3 | 88.8 | FALHA |
| 161343-f00-nivel | eco | cega k=1..3 piso cru | 78.7 | 89.7 | FALHA |
| 161343-f00-nivel | eco | e oraculo k=1..1 | 78.0 | 89.3 | FALHA |
| 161343-f00-nivel | eco | e oraculo k=1..3 | 80.3 | 90.6 | FALHA |
| 161721-f00-nivel-g025 | eco | a atual | 70.7 | 85.3 | ok |
| 161721-f00-nivel-g025 | eco | c/d cega k=1..1 | 72.0 | 86.3 | ok |
| 161721-f00-nivel-g025 | eco | cega k=1..1 piso cru | 72.3 | 86.8 | ok |
| 161721-f00-nivel-g025 | eco | c/d cega k=1..2 | 71.7 | 87.0 | ok |
| 161721-f00-nivel-g025 | eco | cega k=1..2 piso cru | 72.3 | 87.4 | ok |
| 161721-f00-nivel-g025 | eco | c/d cega k=1..3 | 72.0 | 86.8 | ok |
| 161721-f00-nivel-g025 | eco | cega k=1..3 piso cru | 72.3 | 87.2 | ok |
| 161721-f00-nivel-g025 | eco | e oraculo k=1..1 | 73.7 | 87.4 | ok |
| 161721-f00-nivel-g025 | eco | e oraculo k=1..3 | 73.7 | 87.7 | ok |
| 161734-f00-nivel-g100 | eco | a atual | 73.0 | 86.6 | ok |
| 161734-f00-nivel-g100 | eco | c/d cega k=1..1 | 73.7 | 86.8 | ok |
| 161734-f00-nivel-g100 | eco | cega k=1..1 piso cru | 74.3 | 87.1 | ok |
| 161734-f00-nivel-g100 | eco | c/d cega k=1..2 | 73.3 | 87.1 | ok |
| 161734-f00-nivel-g100 | eco | cega k=1..2 piso cru | 75.3 | 88.1 | ok |
| 161734-f00-nivel-g100 | eco | c/d cega k=1..3 | 74.0 | 87.5 | ok |
| 161734-f00-nivel-g100 | eco | cega k=1..3 piso cru | 76.0 | 88.7 | ok |
| 161734-f00-nivel-g100 | eco | e oraculo k=1..1 | 73.7 | 86.6 | ok |
| 161734-f00-nivel-g100 | eco | e oraculo k=1..3 | 75.7 | 87.7 | ok |
| 161939-f04-16fsk | eco | a atual | 79.7 | 88.7 | ok |
| 161939-f04-16fsk | eco | c/d cega k=1..1 | 83.0 | 91.2 | ok |
| 161939-f04-16fsk | eco | cega k=1..1 piso cru | 83.0 | 91.2 | ok |
| 161939-f04-16fsk | eco | c/d cega k=1..2 | 83.0 | 91.0 | ok |
| 161939-f04-16fsk | eco | cega k=1..2 piso cru | 84.0 | 91.7 | ok |
| 161939-f04-16fsk | eco | c/d cega k=1..3 | 83.7 | 91.4 | ok |
| 161939-f04-16fsk | eco | cega k=1..3 piso cru | 84.7 | 91.8 | ok |
| 161939-f04-16fsk | eco | e oraculo k=1..1 | 84.7 | 91.8 | ok |
| 161939-f04-16fsk | eco | e oraculo k=1..3 | 86.0 | 92.7 | ok |
| 162218-f00-nivel-pos-restart | eco | a atual | 70.0 | 84.7 | FALHA |
| 162218-f00-nivel-pos-restart | eco | c/d cega k=1..1 | 74.0 | 87.1 | ok |
| 162218-f00-nivel-pos-restart | eco | cega k=1..1 piso cru | 73.3 | 87.0 | ok |
| 162218-f00-nivel-pos-restart | eco | c/d cega k=1..2 | 74.3 | 87.2 | FALHA |
| 162218-f00-nivel-pos-restart | eco | cega k=1..2 piso cru | 74.3 | 87.8 | ok |
| 162218-f00-nivel-pos-restart | eco | c/d cega k=1..3 | 74.3 | 87.4 | FALHA |
| 162218-f00-nivel-pos-restart | eco | cega k=1..3 piso cru | 75.3 | 88.0 | ok |
| 162218-f00-nivel-pos-restart | eco | e oraculo k=1..1 | 75.0 | 87.8 | FALHA |
| 162218-f00-nivel-pos-restart | eco | e oraculo k=1..3 | 75.7 | 88.4 | FALHA |
| 162232-f04-16fsk-b | eco | a atual | 71.0 | 85.2 | FALHA |
| 162232-f04-16fsk-b | eco | c/d cega k=1..1 | 73.3 | 86.1 | FALHA |
| 162232-f04-16fsk-b | eco | cega k=1..1 piso cru | 73.7 | 86.5 | FALHA |
| 162232-f04-16fsk-b | eco | c/d cega k=1..2 | 73.7 | 86.2 | FALHA |
| 162232-f04-16fsk-b | eco | cega k=1..2 piso cru | 75.3 | 87.9 | FALHA |
| 162232-f04-16fsk-b | eco | c/d cega k=1..3 | 72.3 | 85.8 | FALHA |
| 162232-f04-16fsk-b | eco | cega k=1..3 piso cru | 76.0 | 88.4 | ok |
| 162232-f04-16fsk-b | eco | e oraculo k=1..1 | 76.3 | 87.3 | FALHA |
| 162232-f04-16fsk-b | eco | e oraculo k=1..3 | 78.7 | 88.8 | FALHA |
| 162241-f06-16fsk-ifk | eco | b IFK atual | 71.0 | 85.3 | FALHA |
| 162241-f06-16fsk-ifk | eco | a IFK sem exclusao | 66.0 | 82.6 | FALHA |
| 162241-f06-16fsk-ifk | eco | c/d cega k=1..1 | 67.0 | 83.2 | FALHA |
| 162241-f06-16fsk-ifk | eco | cega k=1..1 piso cru | 68.3 | 83.9 | FALHA |
| 162241-f06-16fsk-ifk | eco | IFK + cega k=1..1 | 71.0 | 85.7 | ok |
| 162241-f06-16fsk-ifk | eco | c/d cega k=1..2 | 69.3 | 84.2 | FALHA |
| 162241-f06-16fsk-ifk | eco | cega k=1..2 piso cru | 70.7 | 85.2 | FALHA |
| 162241-f06-16fsk-ifk | eco | IFK + cega k=1..2 | 71.7 | 85.3 | ok |
| 162241-f06-16fsk-ifk | eco | c/d cega k=1..3 | 70.3 | 84.8 | FALHA |
| 162241-f06-16fsk-ifk | eco | cega k=1..3 piso cru | 70.3 | 85.1 | FALHA |
| 162241-f06-16fsk-ifk | eco | IFK + cega k=1..3 | 72.7 | 86.2 | ok |
| 162241-f06-16fsk-ifk | eco | e oraculo k=1..1 | 70.7 | 85.8 | FALHA |
| 162241-f06-16fsk-ifk | eco | e oraculo k=1..3 | 73.3 | 86.5 | FALHA |
| 162722-f00-nivel-v3 | moderado | a atual | 76.7 | 87.9 | FALHA |
| 162722-f00-nivel-v3 | moderado | c/d cega k=1..1 | 75.7 | 87.9 | FALHA |
| 162722-f00-nivel-v3 | moderado | cega k=1..1 piso cru | 77.0 | 89.0 | FALHA |
| 162722-f00-nivel-v3 | moderado | c/d cega k=1..2 | 75.3 | 87.9 | FALHA |
| 162722-f00-nivel-v3 | moderado | cega k=1..2 piso cru | 77.0 | 89.0 | FALHA |
| 162722-f00-nivel-v3 | moderado | c/d cega k=1..3 | 76.0 | 88.3 | FALHA |
| 162722-f00-nivel-v3 | moderado | cega k=1..3 piso cru | 78.0 | 89.6 | FALHA |
| 162722-f00-nivel-v3 | moderado | e oraculo k=1..1 | 76.3 | 88.2 | FALHA |
| 162722-f00-nivel-v3 | moderado | e oraculo k=1..3 | 77.0 | 89.0 | FALHA |
| 162926-f04-16fsk-v4 | moderado | a atual | 83.0 | 90.6 | ok |
| 162926-f04-16fsk-v4 | moderado | c/d cega k=1..1 | 85.0 | 91.9 | ok |
| 162926-f04-16fsk-v4 | moderado | cega k=1..1 piso cru | 85.7 | 92.3 | ok |
| 162926-f04-16fsk-v4 | moderado | c/d cega k=1..2 | 85.7 | 92.7 | ok |
| 162926-f04-16fsk-v4 | moderado | cega k=1..2 piso cru | 86.3 | 93.0 | ok |
| 162926-f04-16fsk-v4 | moderado | c/d cega k=1..3 | 86.0 | 93.2 | ok |
| 162926-f04-16fsk-v4 | moderado | cega k=1..3 piso cru | 86.3 | 93.2 | ok |
| 162926-f04-16fsk-v4 | moderado | e oraculo k=1..1 | 85.7 | 92.4 | ok |
| 162926-f04-16fsk-v4 | moderado | e oraculo k=1..3 | 85.7 | 92.8 | ok |
| 162936-f06-16fsk-ifk-v4 | moderado | b IFK atual | 80.0 | 88.3 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | a IFK sem exclusao | 77.7 | 86.8 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | c/d cega k=1..1 | 78.0 | 86.9 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | cega k=1..1 piso cru | 78.7 | 87.2 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | IFK + cega k=1..1 | 80.3 | 88.0 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | c/d cega k=1..2 | 78.0 | 86.8 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | cega k=1..2 piso cru | 79.0 | 87.4 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | IFK + cega k=1..2 | 80.7 | 88.3 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | c/d cega k=1..3 | 79.3 | 87.4 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | cega k=1..3 piso cru | 79.7 | 87.7 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | IFK + cega k=1..3 | 82.0 | 89.2 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | e oraculo k=1..1 | 80.0 | 87.8 | FALHA |
| 162936-f06-16fsk-ifk-v4 | moderado | e oraculo k=1..3 | 81.3 | 88.6 | FALHA |
| 164718-f00-nivel-10cm | limpo | a atual | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | c/d cega k=1..1 | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | cega k=1..1 piso cru | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | c/d cega k=1..2 | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | cega k=1..2 piso cru | 100.0 | 100.0 | ok |
| 164718-f00-nivel-10cm | limpo | c/d cega k=1..3 | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | cega k=1..3 piso cru | 100.0 | 100.0 | ok |
| 164718-f00-nivel-10cm | limpo | e oraculo k=1..1 | 99.7 | 99.8 | ok |
| 164718-f00-nivel-10cm | limpo | e oraculo k=1..3 | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | a atual | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | c/d cega k=1..1 | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | cega k=1..1 piso cru | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | c/d cega k=1..2 | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | cega k=1..2 piso cru | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | c/d cega k=1..3 | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | cega k=1..3 piso cru | 100.0 | 100.0 | ok |
| 164832-f04-16fsk-10cm | limpo | e oraculo k=1..1 | 99.7 | 99.8 | ok |
| 164832-f04-16fsk-10cm | limpo | e oraculo k=1..3 | 100.0 | 100.0 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | b IFK atual | 99.0 | 99.4 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | a IFK sem exclusao | 98.7 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | c/d cega k=1..1 | 98.3 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | cega k=1..1 piso cru | 99.0 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | IFK + cega k=1..1 | 99.0 | 99.4 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | c/d cega k=1..2 | 98.3 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | cega k=1..2 piso cru | 99.0 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | IFK + cega k=1..2 | 99.0 | 99.4 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | c/d cega k=1..3 | 98.3 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | cega k=1..3 piso cru | 99.0 | 99.5 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | IFK + cega k=1..3 | 99.0 | 99.4 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | e oraculo k=1..1 | 98.7 | 99.3 | ok |
| 164852-f06-16fsk-ifk-10cm | limpo | e oraculo k=1..3 | 99.7 | 100.0 | ok |

