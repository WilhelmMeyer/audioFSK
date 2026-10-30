# Figuras do capítulo 4 (camada de enlace)

Esquemas, não gravações. Cada script grava aqui e em `artigo/figuras/`, na largura de uma coluna (3,4 in).

    ./venv/bin/python resultados/FIG-ENLACE/figura_quadro.py        # quadro-codificado.png
    ./venv/bin/python resultados/FIG-ENLACE/figura_codificador.py   # codificador.png

- `quadro-codificado.png`: fila no tempo, em escala, de um bloco de 48 bytes em 16-FSK sem repetição, com varreduras. Preâmbulo de 120 símbolos, palavra de referência de 31 bits, 1170 bits codificados (384 de dados + 6 de cauda, vezes 3), final ocioso de 6 símbolos (`fec.frame_symbols` = 427), varreduras de 80 ms (`modem.SYNC_CHIRP`) e silêncios de 30 ms (`console.SYNC_HUSH`). Total 4490 ms.
- `codificador.png`: exemplo numérico com b, b-1..b-6 = 1 0 0 1 0 0 1. Ligações de 171, 133 e 165 (octal) como `fec._tables` as aplica (bit 6 do polinômio no bit que entra, bit 0 no mais antigo). Saída 1 1 0, conferida pelo script contra a tabela do codificador (`assert`).
