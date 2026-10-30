# erros-por-tom.png

Fração dos erros de símbolo da 16-FSK em cada tom transmitido, em três sessões do mesmo sentido (B->A, 2026-09-03), nomeadas na figura como sessão 1 (`14-FEC-REP`, 12 gravações, 1210 erros), sessão 2 (`12-13-SYNC`, 4 gravações, 784 erros) e sessão 3 (`08-MARY-GAIN`, 12 gravações, 451 erros). Marcador cheio: os três piores tons da sessão.

    ./venv/bin/python resultados/H05-ERROS-POR-TOM/figuras/figura_tons.py

Escreve aqui e em `artigo/figuras/erros-por-tom.png`. Lê só `../simbolos.json` (enviado/detectado por símbolo, gerado por `erros_por_tom.py` com o mapeamento Gray antigo das gravações); não demodula nada.

Três piores por sessão: 1538/1700/1862 Hz com 90,2% dos erros; 2025/2675/2512 Hz com 76,0%; 2675/2838/2188 Hz com 47,5%. A frase "metade dos erros em três dos dezesseis tons" é o número da direção inteira com as três sessões somadas (49,1% B->A, 48,9% A->B, `HEADER.md`); por sessão a concentração é maior, exceto na 3, em que o ganho variou quatro vezes.
