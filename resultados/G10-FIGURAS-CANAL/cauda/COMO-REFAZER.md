# Cauda do tom por atraso (decay.py)

Comando, a partir da raiz do repositorio (precisa dos .wav de `captures/`; ~1 min por gravacao por causa de `sym.run`):

    ./venv/bin/python resultados/G10-FIGURAS-CANAL/cauda/decay.py captures/20261008-164718-f00-nivel-10cm

Imprime, por gravacao: queda em dB do tom anterior por atraso (1, 2, 3, 4, 6 simbolos), acerto com e sem repeticao, e a cauda depois do ultimo simbolo.
Usa `../sym.py` (relogio congelado e matriz de energias por simbolo). Copiado de `scratchpad/diag/decay.py` com os caminhos tornados relativos.
Conferido em 2026-10-08: posicao a 10 cm da passada A da -14,6 / -15,2 / -18,6 / -17,9 / -19,7 dB nos atrasos 1, 2, 3, 4, 6, igual ao de `A-eco-por-posicao`.
