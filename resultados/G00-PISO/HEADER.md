# G00-PISO: piso da sala, antes e depois da campanha

Data 2026-10-08. Código `c57fc74`. Gravado por `ruido.py` em A (Linux), mic interno (dispositivo padrão, Mic1), Dmic0 45 (-5 dB), Capture 39 (+12 dB), 8 s cada, sem nada tocando.

| gravação | quando | rms total | pico | observação |
|---|---|---|---|---|
| `g00-piso-ini` | 17:08 | -43,5 dBFS | -17,6 dBFS | eventos passageiros (o 6.º segundo chega a -36,7 dBFS; os demais ficam em -45 a -50) |
| `g00-piso-fim` | 17:44 | -64,6 dBFS | -50,8 dBFS | sala parada; 1 s de rms entre -61 e -67 dBFS |

Por faixa (`piso-por-faixa.csv`, as faixas do `ruido.py`): no início -46,3 a -72,4 dBFS, no fim -69,6 a -91,7 dBFS. A faixa dos 16 tons (550-3500 Hz) fica entre -49,1 e -64,5 dBFS no início e entre -83,8 e -91,7 no fim.

## Leitura

- O piso não é uma constante da bancada: variou 21 dB de rms total em 36 minutos. O `-43,5` é um piso com ruído transitório, não a sala parada; o valor da sala parada é o `-64,6`.
- A medida da `G10-FIGURAS-CANAL/C-piso-da-sala` (ar-condicionado ligado, -48,0 dBFS, e em silêncio, -59,1 dBFS) é de outra sessão e outra posição; o `-64,6` daqui é 5,5 dB mais quieto que aquele silêncio.
- Para uso em campanha, o piso na faixa dos tons é o que importa; entre as duas gravações ele mudou de 12 a 35 dB conforme a faixa.

## Refazer

    ./venv/bin/python ruido.py --device <índice do mic> --secs 8 --label g00-piso-ini

`gravacao/` tem o wav e o json. `piso-por-faixa.csv` vem de `ruido.band_rms` sobre cada wav (mesma conta do `ruido.py`).
