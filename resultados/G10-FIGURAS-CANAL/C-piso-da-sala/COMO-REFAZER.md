# F-C: piso da sala

    ./venv/bin/python resultados/G10-FIGURAS-CANAL/C-piso-da-sala/figura.py

Gera `fig-c-piso-da-sala.png` e `piso-por-tom.csv` (densidade media em +-40 Hz de cada um dos 16 tons).
Welch (Hann, 8192 amostras, 5.9 Hz/bin) de 160944-f00-piso (ar-condicionado ligado) e 161258-f00-piso (silencio); faixas dos 16 tons em cinza.
Rms total: -48.0 dBFS ligado contra -59.1 dBFS em silencio. A media nas faixas dos tons e -94.5 contra -109.8 dB (densidade, fs=1):
o ar-condicionado levanta o piso de 11.5 a 20.6 dB conforme o tom (mais nos tons graves: 18.6, 20.6, 18.3, 16.9 dB nos quatro primeiros, ~12-16 dB nos demais).
O piso com ar ligado e uma curva suave que desce com a frequencia; no silencio ha picos estreitos (ex.: ~550 Hz) que nao coincidem com os tons.
