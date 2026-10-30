
# varreduras-sincronismo.png -- como refazer

Espectrograma no formato do visor (frequência na horizontal, tempo na vertical com o mais recente no alto, rampa de cores do `visor/index.html`) do quadro inteiro de 16-FSK da gravação `20261008-172827-f04-16fsk-10cm-r1`, com as duas varreduras de sincronismo, n1 e n2 de `modem.find_chirp_pair` e a contagem de símbolos pela grade T = (n2 - n1) / S, S = 433 do JSON. Gerada em 2026-10-29.

```bash
./venv/bin/python resultados/F04-16FSK-10CM/figuras/figura_varreduras.py
```

Impresso: `n1 20003, n2 227841, S 433 símbolos, período 479,995 amostras`.
