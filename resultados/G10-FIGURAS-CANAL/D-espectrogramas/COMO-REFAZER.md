# F-D: espectrogramas

    ./venv/bin/python resultados/G10-FIGURAS-CANAL/D-espectrogramas/figura.py

Gera `fig-d-espectrogramas.png` e `nivel-nos-tons.csv` (nivel em dB re pico do painel, nos 16 tons, por coluna de 2 ms).
0.5 s centrados no meio da rajada (janela a partir de 2.24 s e 2.23 s), janela Hann de 408 amostras, passo de 96, banda 700-3600 Hz,
cada painel normalizado ao seu proprio pico, escala de 40 dB; coluna alargada 3x so para leitura. Usa `spectro.spectrogram` e `spectro.colourise`.
Em cima, posicao 1 (161343-f00-nivel): cada tom deixa uma faixa horizontal que atravessa varios simbolos (cada simbolo = 10 ms; ex.: faixa em ~2700 Hz por dezenas de ms)
e o fundo entre tons fica alto. Embaixo, 10 cm (164718-f00-nivel-10cm): blocos de um simbolo, separados, com fundo escuro entre eles.
Uma barra de 100 ms (10 simbolos) esta sob cada painel. Qualitativo: a escala relativa ao pico de cada painel nao compara niveis absolutos entre eles.
