# deteccao-tom.png -- como refazer

O vetor de energias que o demodulador de 16-FSK compara para decidir um
simbolo, medido em duas condicoes gravadas nesta bancada, sentido A->B: com o
tom de 1700 Hz no ar (as gravacoes desta campanha) e com o enlace parado (as
de `resultados/01-LVL-BASE-A2B/`). A leitura e a distancia entre as duas
curvas no tom transmitido, contra o que a regra de decisao exige.

- **Codigo:** commit `668b706`, gerada em 2026-09-07.
- **Programa:** `figura_deteccao.py`, nesta pasta.

O script mora aqui, junto da campanha que ele mede, e nao na pasta do artigo:
`artigo/figuras/` guarda apenas as figuras. Uma execucao grava nos dois
lugares, esta pasta e `artigo/figuras/`, entao nao ha copia a sincronizar a
mao. Ele acha a raiz do repositorio subindo ate encontrar `modem.py`, logo
roda de qualquer pasta.

```bash
./venv/bin/python resultados/02-LVL-TONE-A2B/figuras/figura_deteccao.py
```

Nada da janela e escolhido pela figura: ela instancia o `MaryDemodulator`
com os parametros de operacao e usa `probe`, `guard` e
`samples_per_tone` como estao no codigo. A gravacao usada e a terceira das
cinco, que e a mediana de nivel da tabela do `HEADER.md`.

## O que ele imprimiu nesta geracao

```
[detecção] /home/willj/audioFSK/resultados/02-LVL-TONE-A2B/figuras/deteccao-tom.png, /home/willj/audioFSK/artigo/figuras/deteccao-tom.png
    janela do detector: 408 amostras (8,5 ms, 117,6 Hz por bin), guarda de 72 amostras descartada de 480
    100 janelas no meio de 20260903-175101-lvl-tone-A2B.wav; sala: mediana de 4 gravações
    tom de 1700 Hz: com -20,0 dBFS, sem -67,4 dBFS, margem 47,4 dB
    segunda sonda mais alta com o tom no ar: 1862 Hz a -33,0 dBFS (13,0 dB abaixo do vencedor)
    (a segunda sonda é a saia do próprio tom na janela retangular de 408 amostras, não outro tom transmitido)
    decisão: contraste mínimo 0,15 = 1,3 dB entre vencedor e segundo
    seno puro simulado na mesma janela: reproduz a gravação dentro de 7,1 dB em todas as sondas (mediana 2,7 dB)
      maior desvio em 3325 Hz: gravação -54,6 dBFS contra -61,7 simulado
    por tom: com tom, seno simulado, sala, margem (com - sala), dB:
         888 Hz    -57,2    -57,2    -68,8    11,7
        1050 Hz    -46,7    -43,3    -70,1    23,5
        1212 Hz    -50,9    -47,5    -64,8    13,9
        1375 Hz    -42,5    -41,7    -63,6    21,1
        1538 Hz    -33,7    -33,0    -63,7    29,9
        1700 Hz    -20,0    -20,0    -67,4    47,4
        1862 Hz    -33,0    -33,7    -71,5    38,4
        2025 Hz    -41,2    -43,1    -75,1    33,9
        2188 Hz    -48,7    -49,6    -78,8    30,1
        2350 Hz    -43,5    -46,1    -80,6    37,1
        2512 Hz    -54,5    -60,2    -81,3    26,8
        2675 Hz    -49,0    -51,7    -82,4    33,4
        2838 Hz    -48,8    -53,4    -85,9    37,1
        3000 Hz    -68,1    -65,0    -84,6    16,5
        3162 Hz    -49,8    -54,2    -83,6    33,8
        3325 Hz    -54,6    -61,7    -83,8    29,2
```

Duas ressalvas para quem for citar estes numeros. A segunda sonda mais alta
com o tom no ar e a saia do proprio tom de 1700 Hz na janela retangular de
408 amostras, nao outro tom transmitido, entao os 13 dB nao sao margem contra
um simbolo concorrente e sim contra o vazamento do vencedor. E o detector
divide cada tom pelo seu proprio piso corrente antes de comparar, o que esta
figura nao aplica: ela mostra as energias cruas, que e o que a comparacao
entre "com tom" e "sem tom" precisa.

## A terceira serie, e por que ela esta na figura

Quando o tom entra no ar, todas as dezesseis sondas sobem, e a pergunta e se
isso e o microfone ficando mais sensivel, ruido novo na sala ou artefato da
medida. A serie do seno puro responde: um seno de 1700 Hz sintetizado na
amplitude que a gravacao mediu no proprio tom, sondado pela mesma janela, sem
sala, sem alto-falante e sem microfone, reproduz a gravacao dentro de 7,1 dB
em todas as sondas e 2,7 dB de mediana. As sondas altas sao o vazamento
espectral da janela retangular de 408 amostras, o sinc de um seno que nao cai
no centro de um bin, e nao energia nova no ar.

Tres efeitos separados aparecem ali, e vale distinguir. Nas sondas distantes,
vazamento: trocando a janela retangular por Hann sobre o mesmo audio, a sonda
de 2188 Hz cai de -49,1 para -73,7 dBFS e a de 2675 Hz de -49,2 para -85,8,
que e o piso da sala. Nas sondas vizinhas, 1538 e 1862 Hz, o lobo principal:
ficam em -32,6 dBFS com as duas janelas, porque 162 Hz sao 1,38 bins de
117,6 Hz e nenhuma janela resolve isso, so uma janela mais longa. E em
3325 Hz, distorcao de verdade: com Hann fica 17 dB acima do piso, porque o
segundo harmonico do tom, 3400 Hz, cai a 75 Hz dessa sonda. E o mesmo
harmonico que o espectrograma de `03-CH-CHIRP-A2B` mede 30 dB abaixo da
fundamental.
