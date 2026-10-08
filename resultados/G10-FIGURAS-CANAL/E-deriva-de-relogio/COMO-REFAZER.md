# F-E: deriva de relogio

    ./venv/bin/python -u resultados/G10-FIGURAS-CANAL/E-deriva-de-relogio/figura.py     # ~5 min

Copia cada par .wav/.json de 20261008 com `sync_chirp` (9 gravacoes) para uma pasta temporaria, roda `align.py` nela
(saida completa em `align-saida.txt`) e le o periodo por gravacao com `align.probe`. Gera `periodo-medido.csv` e `fig-e-periodo-medido.png`.
Periodo medido entre as duas varreduras: 479.995 a 479.998 amostras/simbolo em 8 das 9 gravacoes (media 479.997, desvio 0.001; -5 a -10 ppm do nominal 480),
em todas as tres posicoes. A resolucao e ~0.002 amostra/simbolo (1 amostra em 433 x 480); a gravacao 162232-b nao teve o par de varreduras achado.
Os relogios da caixa e do microfone praticamente nao derivam: a deriva nao explica os erros. No resumo do align.py:
gate 88.0% (4/9 blocos), relogio travado 89.8% (6/9), duas varreduras 89.2% (4/8).
