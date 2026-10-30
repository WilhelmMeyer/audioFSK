# Figura do quadro codificado (capítulo 4)

    ./venv/bin/python resultados/FIG-ENLACE/figura_quadro.py

Esquema, não gravação. Grava `quadro-codificado.png` aqui e em `artigo/figuras/`.

- Fila no tempo, em escala: bloco de 48 bytes em 16-FSK sem repetição, com varreduras. Preâmbulo de 120 símbolos, palavra de referência de 31 bits, 1170 bits codificados (384 de dados + 6 de cauda, vezes 3), final ocioso de 6 símbolos (`fec.frame_symbols` = 427), varreduras de 80 ms (`modem.SYNC_CHIRP`) e silêncios de 30 ms (`console.SYNC_HUSH`). Total 4490 ms.
- Codificador: ligações de 171, 133 e 165 (octal) como `fec._tables` as aplica, o bit 6 do polinômio no bit que entra e o bit 0 no mais antigo.

## negociacao.png (enlace negociado no tempo)

    ./venv/bin/python resultados/FIG-ENLACE/figura_negociacao.py

Escala real. Sessão 3 do `resultados/H07-ENLACE-MODOS/` (2026-10-22, modo de dados 16-FSK, ~2 m, 207/207 e 44/44 em 113 s), reconstruída dos diários `sessoes/20261022-163530-enlace-chamador.diario.txt` e `20261022-163524-enlace-ouvinte.diario.txt`. Os instantes de leitura de cada turno estão copiados no script (`TURNOS`); cada seta vai do instante em que o transmissor leu o turno anterior ao instante em que o receptor leu este, então inclui o tempo de processamento e é aproximada. O relógio do ouvinte foi trazido ao do chamador por 7,8 s, da chamada (emitida em 0,90 s, ouvida em 8,92 s) e conferido pela saudação (lida em 15,40 s). O quadro ilegível é o real da sessão (ouvinte, 107,95 s); não houve recuo de taxa nessa sessão, por isso a figura não o mostra. Grava em `negociacao.png` aqui e em `artigo/figuras/`.
