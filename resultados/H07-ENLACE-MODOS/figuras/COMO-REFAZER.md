# Contratos do enlace negociado (figura do artigo)

`./venv/bin/python resultados/H07-ENLACE-MODOS/figuras/figura_contratos.py` grava `enlace-contratos.png` aqui e em `artigo/figuras/`.

Sessão 2 do H07 (2026-10-22, 16:11, modo de dados `auto`, ~2 m): 207/207 e 44/44 bytes, tudo confirmado em 302,5 s. Lê só os dois `.diario.txt` da sessão: a última linha "sondagem lida" de cada receptor (margem dos 25 tons da grade, 562,5 a 4462,5 Hz, passo 162,5 Hz) e a última linha "contrato para o que me chega".

- Chamador → ouvinte (medido pelo ouvinte, sondagem de 212,5 s): tons 1537,5–4462,5 Hz menos 1862, 2025 e 2188 Hz (margens 13, 13 e 21 dB), ganho 0,2, 16-FSK rep1, 100 baud. O primeiro contrato dessa sessão (1538–4300, sombras 1862 e 2025) falhou e foi refeito.
- Ouvinte → chamador (medido pelo chamador, sondagem de 229,5 s): 887,5–3325 Hz, sem exclusão, ganho 0,12, 16-FSK rep1, 100 baud.

"Ganho" é o ganho digital do contrato (protocolo 1, `enlace.py`); não é volume da caixa. Gray anterior à correção de 2026-10-29.
