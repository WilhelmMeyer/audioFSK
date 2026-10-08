# F-A: eco por posicao da caixa

Comando (a partir da raiz do repositorio, ~6 min por causa de `sym.run`; precisa de `captures/` com os .wav):

    ./venv/bin/python -u resultados/G10-FIGURAS-CANAL/A-eco-por-posicao/figura.py

Gera `fig-a1-resposta-impulso.png` + `resposta-impulso.csv` e `fig-a2-queda-por-atraso.png` + `queda-por-atraso.csv`.
Depende de `../plota.py` e `../sym.py` (copia de `scratchpad/diag/sym.py` com o caminho da raiz tornado relativo).

**a1.** Filtro casado com `modem.chirp()` (700-3400 Hz, 80 ms) sobre as varreduras de sincronismo; envoltoria de Hilbert
ao quadrado, media de 1 ms, normalizada ao pico, varredura lider. Posicao 1 (161939, 162232-b), 2 (162926-v4), 3 (164832-10cm).
Na posicao 1 o nivel fica em torno de -13 a -15 dB de +10 a +40 ms (161939: -7.6/-14.2/-13.2 dB em +10/+20/+40 ms;
162232-b: -13.0/-13.1/-15.3); na posicao 2 cai para -23 a -25 dB e na 3 para -24 a -33 dB (-26.2/-23.8/-33.2).
A cauda de ~60 ms da posicao 1 e 10 a 15 dB mais alta que a da 3: ha energia espalhada logo depois do pico, nao so um eco discreto.
Cuidado: a media de 1 ms borra o lobo principal e a escala e relativa ao pico de cada gravacao (picos/mediana: 220, 237, 585, 1072).

**a2.** Mediana de E[k+L,t]/E[k,t] (energia no tom t, L simbolos apos t parar, excluindo vizinhos +-1 e repeticao), nas gravacoes
`f00-nivel` (161343, 162722-v3, 164718-10cm), corpo a partir do simbolo 120. Atraso 1..6 simbolos:
posicao 1: -4.7 -6.9 -9.2 -8.9 -12.9 -11.1 dB; posicao 2: -8.0 -12.1 -12.8 -12.8 -12.0 -15.1; posicao 3: -14.6 -15.2 -18.6 -17.9 -19.4 -19.7.
O tom anterior um simbolo depois cai so -4.7 dB na posicao 1 e -14.6 dB a 10 cm (o -13.4 citado vem de outra medida/gravacao).
