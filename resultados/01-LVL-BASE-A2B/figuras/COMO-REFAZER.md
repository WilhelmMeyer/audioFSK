# piso-ruido.png -- como refazer

Figura de artigo (300 dpi, largura de coluna, segura em escala de cinza),
feita das gravacoes desta pasta, sem numero transcrito a mao. Nao confundir
com as quatro PNGs de diagnostico ao lado, que sao saida do `resultado.py`.

- **Codigo:** commit `668b706`, gerada em 2026-09-07.
- **Programa:** `figura_piso.py`, nesta pasta.

O script mora aqui, junto da campanha que ele mede, e nao na pasta do artigo:
`artigo/figuras/` guarda apenas as figuras. Uma execucao grava nos dois
lugares, esta pasta e `artigo/figuras/`, entao nao ha copia a sincronizar a
mao. Ele acha a raiz do repositorio subindo ate encontrar `modem.py`, logo
roda de qualquer pasta.

```bash
./venv/bin/python resultados/01-LVL-BASE-A2B/figuras/figura_piso.py
```

Ele le `recording.py`, `ruido.py` (o mesmo
`band_rms` que produziu os numeros do `HEADER.md`) e `modem.MARY_TONES`.

## O que ele imprimiu nesta geracao

```
[piso] /home/willj/audioFSK/resultados/01-LVL-BASE-A2B/figuras/piso-ruido.png, /home/willj/audioFSK/artigo/figuras/piso-ruido.png
    4 gravações de 8,0 s, pasta /home/willj/audioFSK/resultados/01-LVL-BASE-A2B/gravacao
    banda inteira: mediana -52,3 dBFS (-53,5 a -51,7)
    faixa útil 550–3500 Hz: mediana -55,0 dBFS (-57,9 a -54,4)
    tom 1700 Hz ±25 Hz: mediana -73,3 dBFS (-75,8 a -71,2); na curva média -73,1 dBFS
    janela de decisão 408 amostras, 117,6 Hz por sonda
    16 de 16 tons do 16-FSK dentro da faixa útil; piso sob eles de -94,8 a -67,6 dBFS
    curva média: -94,8 a -62,4 dBFS; na faixa útil -94,8 a -62,4 dBFS
```

Faixa util desenhada como 550-3500 Hz, a mesma do `CLAUDE.md` da raiz, e nao
os 550-3600 Hz que o `HEADER.md` desta campanha rotula: entre 3500 e 3600 Hz
nao ha nada acima de -90 dBFS e as duas medianas coincidem em 0,1 dB.

Os dezesseis tons da 16-FSK aparecem como tracos no rodape, lidos de
`modem.MARY_TONES`, e o tom de referencia de 1700 Hz desce pontilhado ate a
base para ser lido junto do traco do tom que ele mede. Quanto o piso sob eles
separa um tom de um nao tom esta em `resultados/02-LVL-TONE-A2B/figuras/`.
