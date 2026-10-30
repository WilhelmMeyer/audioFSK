# Arquivo do computador para o celular (2026-10-30)

Sessão de 13:19: computador como chamador, celular (app Android) como ouvinte, configuração manual 16-FSK, 100 símbolos por segundo, repetição 2, caixa a 40%. O arquivo é `if-logo-enviado.bmp`, o logo do IF desenhado em 48×48 pixels e 16 cores (`gera_logo.py`), com 1270 bytes.

- 40 pacotes (seq 0 a 39), um com retransmissão (seq 0, 2ª tentativa); o último confirmado aos 491,95 s, ou 2,6 B/s.
- O `.bin` do celular tem 1293 bytes: os 1270 do BMP, idênticos (CRC-32 29cfeaa7 nos dois), e 23 bytes de texto digitados depois na mesma sessão (seq 40).
- Diário, estado e JSON do computador em `arquivo/`; o `.bin` e o JSON do celular, tirados por `adb pull` de `/sdcard/Android/data/com.audiofsk.enlace/files/sessoes/`. Os WAV ficaram fora (163 MB no celular, `sessoes-enlace-celular/` no computador).
- Gray: código corrigido de 2026-10-29 nas duas pontas.

Figura: `./venv/bin/python resultados/H08-ARQUIVO-CELULAR/figuras/figura_arquivo.py`, que confere a igualdade antes de desenhar.
