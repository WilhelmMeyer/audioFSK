# 03-CH-CHIRP -- resposta de frequencia por varredura

- **Codigo:** commit `02be235` (main).
- **Quando:** 2026-09-03, 15:46.
- **Camada:** nenhuma -- varredura linear (`--chirp`), sem FEC, sem payload.
- **Direcao:** B -> A. B = Windows, caixa Bluetooth AL-667 a ~60% de volume.
  A = Linux, microfone interno Mic1/Dmic0 indice PortAudio 26, ganho de
  captura Dmic0 45 (-5 dB), Capture 39 (+12 dB). Cabo serial /dev/ttyUSB0 so
  controle.
- **Varredura:** 300-6000 Hz linear em 4,0 s, precedida de silencio.
- **Trials:** 1 gravacao (`20260903-154600-ch-chirp-B2A`).

Analisada com `channel.py --bins 76` (mapa de bins abaixo) e com `spectro.py`
para a figura. Sem `resultado.py`: essa gravacao carrega uma varredura, nao
um bloco codificado (`baud=0`, `payload_len=0`), e a ferramenta que pontua
blocos M-arios/MFSK divide por `baud` e trava com `ZeroDivisionError` nesse
caso -- confirmado tentando rodar `resultado.py` nesta captura antes de
montar a pasta a mao.

## Resultado

`./venv/bin/python channel.py captures/20260903-154600-ch-chirp-B2A.json --bins 76`
(saida completa em `figuras/mapa-frequencia-bins76.txt`):

- **74 dos 76 bins (97%) leram SNR negativa** contra o piso de sala medido na
  mesma gravacao. So dois bins ficaram positivos: 338 Hz (+10,6 dB) e 712 Hz
  (+4,5 dB) -- os dois fora, ou na borda, da banda de 550-3500 Hz onde as
  camadas M-aria e MFSK moram.
- Na faixa 550-3500 Hz (onde vivem os tons das camadas com FEC), todos os
  bins leram SNR negativa, de -4,2 dB (1012 Hz) a -24,8 dB (2662 Hz).
- **Em 1688 Hz (bin mais proximo de 1700 Hz), a varredura leu SNR -19,4 dB.**

## Ressalva obrigatoria -- a varredura contradiz o tom pisado, e ja errou nesta bancada

**Este numero e falso, e ha como provar isso na mesma bancada.** O teste
`02-LVL-TONE` (`resultados/02-LVL-TONE/HEADER.md`) mediu 1700 Hz mandando
1700 Hz -- um tom puro, 3 trials, mediana -- e leu **+57,3 dB de margem sobre
o piso** no sentido B->A, com espalhamento de 7,1 dB entre trials. A mesma
frequencia, na mesma bancada, no mesmo sentido: a varredura diz -19,4 dB e o
tom pisado diz +57,3 dB. **A diferenca e maior que 76 dB**, e nao ha
ambiguidade sobre qual dos dois esta certo -- o tom pisado enviou aquela
frequencia de verdade e mediu o que voltou; a varredura passa 300-6000 Hz em
4 s, o que da menos de 1 ms de energia por Hz, e essa energia insuficiente
soma-se ao ruido de fundo e ao vazamento espectral da propria FFT em vez de
revelar o canal.

**Conclusao, e ja registrada assim no `channel.py` e no `TESTES.md` deste
projeto:** medir uma frequencia manda-se aquela frequencia (`tonef`/`meas`,
teste 02), nunca por varredura. A varredura responde outra pergunta -- onde
ficam as covas grosseiras do pente, a dezenas de Hz de resolucao -- e mesmo
essa resposta e so confiavel comparada bin a bin dentro da propria varredura,
nunca contra um numero absoluto de dB medido de outra forma. Usar o valor
absoluto desta varredura para decidir se uma frequencia especifica presta
teria descartado 1700 Hz, que na verdade e um dos pontos mais fortes do link
medido nesta bancada.

## Leitura

A varredura ainda serve para o que ela mede bem: **forma relativa da banda**,
nao amplitude absoluta em nenhum ponto. Vista assim, ela concorda com o que
o projeto ja sabia -- a resposta e um pente, nao uma curva suave, com
vizinhos a 50 Hz diferindo por muitos dB (aqui, ate a faixa inteira de -4 a
-25 dB dentro de 550-3500 Hz) -- e nao contradiz a existencia de covas. O que
ela erra e a escala: toda a varredura leu abaixo do piso de ruido onde o tom
pisado no mesmo ponto lia dezenas de dB acima dele. Nao usar este mapa para
decidir se uma frequencia individual presta ou nao; usar `tonef`/`meas`
(teste 02) para isso, ponto a ponto.

## Arquivos

- `gravacao/` -- a gravacao da varredura, WAV float32 mais JSON
- `figuras/20260903-154600-ch-chirp-B2A.png` -- espectrograma (`spectro.py`,
  300-6000 Hz)
- `figuras/mapa-frequencia-bins76.txt` -- saida completa de
  `channel.py --bins 76`, nivel relativo e SNR por bin
