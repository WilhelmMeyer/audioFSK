# sincronismo-varreduras.png -- como refazer

Sintético: o `MaryModulator` e o `modem.chirp` do sistema geram varredura, 30 ms de silêncio, 12 bytes de 16-FSK, silêncio e varredura (S = 30 símbolos), sem ar. n1 e n2 por `modem.find_chirp_pair`, fronteiras em n1 + k (n2 - n1) / S. Formato e cores do visor. Gerada em 2026-10-29.

```bash
./venv/bin/python resultados/FIG-SINCRONISMO/figura_sincronismo.py
```
