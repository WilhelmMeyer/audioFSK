# 03-CH-CHIRP-A2B -- resposta de frequencia por varredura, sentido A->B

- **Codigo:** commit `d57b3a1` (main).
- **Quando:** gravacao `20260903-175426-ch-chirp-A2B`.
- **Camada:** nenhuma -- varredura linear (`chirp`), sem FEC, sem payload.
- **Direcao:** A -> B. A = Linux, console, caixa Bluetooth
  `41:42:2B:14:D4:2A`, indice PortAudio 20, `gain 1.0`. B = Windows, agent,
  microfone interno, grava e manda o par WAV+JSON de volta pelo cabo
  `/dev/ttyUSB0` a 115200 baud (int16).
- **Varredura:** 300-6000 Hz linear em 6,0 s, precedida de silencio.
- **Nivel bruto da gravacao:** rms 0,1288, pico 0,8895.
- **Trials:** 1 gravacao (`20260903-175426-ch-chirp-A2B`).

Analisada com `channel.py --bins 76` (saida completa em
`figuras/mapa-frequencia-bins76.txt`) e `spectro.py` para a figura. Sem
`resultado.py`: esta gravacao carrega uma varredura, nao um bloco codificado
(`baud=0` na metrica que o `resultado.py` espera; aqui `baud=100` mas
`payload_len=0` e a comparacao de bytes nao se aplica), e o comportamento
ja esta registrado em `resultados/03-CH-CHIRP/HEADER.md` -- a pasta foi
montada a mao, do mesmo jeito.

## Resultado

`./venv/bin/python channel.py captures-a2b/03-ch-chirp/20260903-175426-ch-chirp-A2B.json --bins 76`:

- **76 de 76 bins (100%) leram SNR positiva** contra o piso de sala medido
  na mesma gravacao. Nenhum bin negativo, em nenhuma parte de 300-6000 Hz.
- Na faixa 550-3500 Hz (onde vivem os tons M-arios e MFSK), os 40 bins
  dessa faixa tambem sao todos positivos: de 40,1 dB (2062 Hz) a 57,2 dB
  (2662 Hz).
- **Em 1688 Hz (bin mais proximo de 1700 Hz), a varredura leu SNR +48,6 dB.**

## Ressalva obrigatoria -- comparacao com o sentido B->A, e aqui a varredura NAO contradiz o tom pisado

`resultados/03-CH-CHIRP/HEADER.md` (sentido B->A, mesma ferramenta) leu SNR
**negativa** em 74 de 76 bins e um erro de mais de 76 dB entre a varredura em
1700 Hz (-19,4 dB) e o tom pisado na mesma frequencia (+57,3 dB, teste
`02-LVL-TONE`). **Isso nao se repete aqui.** Nesta gravacao A->B a varredura
lê +48,6 dB em 1688 Hz, e o teste `02-LVL-TONE-A2B` (tom pisado em 1700 Hz,
mesma cadeia) leu margem entre +50,3 e +54,4 dB ao longo de 5 trials. A
diferenca entre as duas reguas aqui e de 2 a 6 dB, nao de 76 -- dentro do que
se espera de duas medidas com metodos diferentes sobre o mesmo canal, e as
duas concordam sobre a mesma conclusao: 1700 Hz e forte nesta cadeia.

**Por que a diferenca entre os dois sentidos:** a varredura da B (a antiga,
`03-CH-CHIRP`) e mais curta e mais rapida (a nota do outro HEADER fala em
menos de 1 ms de energia por Hz), o suficiente para se perder no ruido e no
vazamento espectral da FFT. Esta varredura de A e 6,0 s contra 4,0 s da
antiga -- 50% mais devagar, logo mais energia por Hz -- e isso pode bastar
para tirar a medida da regiao onde ela se perde no ruido. Isso nao muda a
doutrina abaixo: mesmo aqui, onde a varredura concorda com o tom pisado, ela
so foi comparada num unico ponto (1688-1700 Hz); nao ha garantia de que
concordaria em outra frequencia sem medir com `tonef`/`meas` la tambem.

## Pico 0,8895 -- alto, mas sem sinal de compressao

Uma varredura e um tom continuo deslizando, entao ela nao carrega o fator de
crista de um burst M-ario (que chega a ~2,5x o pico de um tom continuo) --
mas 0,8895 ainda esta perto do teto de 1,0 e merece checagem antes de
confiar na forma do pente.

Contagem direta sobre as 384000 amostras (`recording.load`):

| limiar | fracao acima | amostras |
|---|---|---|
| \|x\| > 0,90 | 0 | 0 |
| \|x\| > 0,95 | 0 | 0 |
| \|x\| > 0,99 | 0 | 0 |

O maximo absoluto na gravacao e exatamente 0,8895 -- igual ao pico
registrado no JSON, sem nenhuma amostra mais alta em nenhum outro ponto da
varredura. Nao ha plato nem achatamento: o pico e um unico maximo isolado,
nao um teto que o sinal encosta repetidas vezes. **Sem evidencia de
compressao ou corte nesta gravacao**, apesar do valor absoluto ser alto.

## Leitura

**A forma relativa do pente** e o que esta varredura mede bem, doutrina do
`CLAUDE.md` e do `TESTES.md`: nao usar amplitude absoluta de um ponto da
varredura para julgar aquela frequencia isoladamente -- para isso, `tonef`/
`meas` (teste 02), ponto a ponto. Aqui a forma concorda com o que a bancada
ja sabia: pente, nao curva suave, com vizinhos de 50 Hz variando ate 17 dB
dentro da propria faixa util (40,1 a 57,2 dB entre 550-3500 Hz). A diferenca
para o sentido B->A e que, desta vez, a escala absoluta da varredura tambem
bate com o tom pisado -- o que nao autoriza usar a varredura como regua de
amplitude em geral (foi medido um unico ponto), so registra que, nesta
gravacao, ela nao errou do jeito que errou no outro sentido.

## Arquivos

- `gravacao/` -- a gravacao da varredura, WAV float32 mais JSON
- `figuras/20260903-175426-ch-chirp-A2B.png` -- espectrograma (`spectro.py`,
  300-6000 Hz)
- `figuras/mapa-frequencia-bins76.txt` -- saida completa de
  `channel.py --bins 76`, nivel relativo e SNR por bin
