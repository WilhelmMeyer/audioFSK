# Arquivo do computador para o celular (2026-10-30)

Sessão de 13:19: computador como chamador, celular (app Android) como ouvinte, configuração manual 16-FSK, 100 símbolos por segundo, repetição 2, caixa a 40%. O arquivo é `if-logo-enviado.bmp`, o logo do IF desenhado em 48×48 pixels e 16 cores (`gera_logo.py`), com 1270 bytes.

- 40 pacotes (seq 0 a 39), um com retransmissão (seq 0, 2ª tentativa); o último confirmado aos 491,95 s, ou 2,6 B/s.
- O `.bin` do celular tem 1293 bytes: os 1270 do BMP, idênticos (CRC-32 29cfeaa7 nos dois), e 23 bytes de texto digitados depois na mesma sessão (seq 40).
- Diário, estado e JSON do computador em `arquivo/`; o `.bin` e o JSON do celular, tirados por `adb pull` de `/sdcard/Android/data/com.audiofsk.enlace/files/sessoes/`. Os WAV ficaram fora (163 MB no celular, `sessoes-enlace-celular/` no computador).
- Gray: código corrigido de 2026-10-29 nas duas pontas.

Figura: `./venv/bin/python resultados/H08-ARQUIVO-CELULAR/figuras/figura_arquivo.py`, que confere a igualdade antes de desenhar.

## Bandeira (15:43, `bandeira-embaralhada/`)

`figurinhas/bandeira-br-48.bmp`, 934 bytes, mesma configuração (16-FSK, 100 baud, rep 2), caixa a 30%, com os pacotes embaralhados (`enlace_manual.embaralha`). 30 pacotes, todos na 1ª tentativa, último confirmado aos 323,67 s (2,9 B/s). No JSON do celular, 3180 de 58680 bits lidos errados (5,4%), todos corrigidos; o `.bin` é idêntico ao BMP (CRC-32 ca8b9cf3). A tentativa anterior, sem embaralhar (`bandeira/`, 15:14), errava os pacotes só de zeros e ficou fora do artigo.

A Figura 17 mostra as duas imagens recebidas, uma vez cada; o script confere as duas contra as enviadas antes de desenhar.
