# 01-LVL-BASE-A2B -- piso de ruido do microfone de B, nada tocando

- **Codigo:** commit `68412e1`, mesmo commit nas duas maquinas.
- **Quando:** 2026-09-03, entre 17:39 e 17:50.
- **Bancada:** A (Linux, console, transmite) caixa Bluetooth
  `41:42:2B:14:D4:2A`, indice PortAudio 20 -- **desligada/muda durante esta
  medida**, nada tocando. B (Windows, agent, grava) microfone interno do
  notebook. O par WAV+JSON volta de B para A pelo cabo `/dev/ttyUSB0` a
  115200 baud, em int16.
- **Ferramenta:** `capture_a2b.py --silence`, que manda `grave` para B e traz
  o par de volta. Primeira vez que o piso de B e medido por uma gravacao
  guardada em disco -- ate aqui so existia o `level` do agent (ver
  `resultados/01-LVL-BASE/HEADER.md`, secao "Lado B").
- **Trials:** 4 gravacoes de 8 s cada.

Mede o que o microfone de B entrega com o link inteiramente parado -- a
metade da cadeia A->B que faltava depois de `01-LVL-BASE` medir o piso de A.

## Resultado

| gravacao | rms | dBFS | pico | pico dBFS | banda util 550-3600 Hz (rms) | banda util dBFS |
|---|---|---|---|---|---|---|
| 173919 | 0,002562 | -51,8 | 0,012421 | -38,1 | 0,001882 | -54,5 |
| 174102 | 0,002125 | -53,5 | 0,009308 | -40,6 | 0,001271 | -57,9 |
| 174729 | 0,002295 | -52,8 | 0,011719 | -38,6 | 0,001678 | -55,5 |
| 174912 | 0,002609 | -51,7 | 0,012421 | -38,1 | 0,001895 | -54,4 |

Mediana das quatro: banda inteira **-52,3 dBFS**, banda util **-55,0 dBFS**.
Piso no tom de 1700 Hz (+-25 Hz), usado no teste 02: entre -75,8 e -71,2 dBFS
pelas quatro gravacoes, mediana **-73,3 dBFS** -- esse numero e a rade do
teste 02.

## Leitura

**O microfone de B fica cerca de 1 dB acima do piso de A pela mesma banda
larga** (-52,3 aqui contra -52,5 dBFS em `01-LVL-BASE`), e cerca de 2 dB
acima na banda util (-55,0 contra -62,6). Sao dois microfones, dois ganhos de
captura e duas salas de fundo diferentes -- a proximidade nao autoriza tratar
os dois pisos como o mesmo numero, so diz que nenhuma das duas cadeias
comeca com desvantagem grande de piso.

**As quatro gravacoes concordam entre si.** Banda larga varia so 1,8 dB
(-53,5 a -51,7) e banda util 3,5 dB (-57,9 a -54,4) -- nada como a
contaminacao por fala que forcou descartar a primeira tentativa de
`01-LVL-BASE`. A caixa Bluetooth de A estava desligada durante toda a medida,
entao nao ha vazamento do lado transmissor nesta captura.

## Ressalva

**Duas das quatro gravacoes (173919 e 174102) foram feitas antes de eu
consertar o `capture_a2b.py`.** O conserto (commit `d7e170e`) mudou codigo de
saida do processo, deteccao de recusa do agent e as tentativas de reabrir a
caixa Bluetooth apos um sink recem-liberado anunciar zero canais -- nada
disso altera o audio que chega ao microfone de B numa medida de piso, onde a
caixa de A nem esta tocando. As duas gravacoes de antes (174729, 174912) leem
dentro do mesmo espalhamento das duas de depois, o que e consistente com essa
leitura: nenhuma diferenca visivel de instrumento.

## Arquivos

- `gravacao/` -- os quatro pares WAV float32 + JSON
- `figuras/` -- espectro cru em cima, contraste embaixo, por gravacao
- `resultado.csv` -- uma linha por gravacao, mesmas colunas de
  `resultados/01-LVL-BASE/resultado.csv`
