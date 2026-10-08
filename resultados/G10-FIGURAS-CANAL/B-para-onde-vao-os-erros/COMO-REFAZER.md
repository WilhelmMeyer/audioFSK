# F-B: para onde vao os simbolos errados

Comando (raiz do repositorio, ~10 min; precisa de `captures/`):

    ./venv/bin/python -u resultados/G10-FIGURAS-CANAL/B-para-onde-vao-os-erros/figura.py

Gera `fig-b-destino-dos-erros.png` e `destino-dos-erros.csv`.

Para cada gravacao: busca de periodo/offset por argmax bruto (como o `ifk.py` do diagnostico), depois `MaryDemodulator(steer=False, skip, period, ifk)`;
corpo = simbolos 120.. (300 simbolos). Cada simbolo errado vai para uma classe, nesta precedencia: tom de n-1, tom de n-2, vizinho +-1 do transmitido,
tom de repeticao (17o tom, so IFK), outro. As barras sao a fracao dos ERROS (nao dos simbolos); o total de erros vai sob cada grupo.
Posicao antiga: sem IFK (162232-b) 87 de 300 simbolos errados (29%), 58.6% deles no tom de n-1, 14.9% em n-2, 2.3% vizinho, 24.1% outro;
com IFK (162241) tambem 87 de 300 (29%): n-1 cai para 21.8%, mas n-2 sobe para 34.5%, vizinho 5.7%, outro 37.9%, repeticao 0% — o total nao mexe.
A 10 cm: sem IFK 0 erros; com IFK 3 erros (2 em n-2, 1 outro) — as barras ali sao 3 simbolos, nao estatistica.
