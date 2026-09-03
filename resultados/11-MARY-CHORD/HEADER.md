# 11-MARY-CHORD

- **Codigo:** commit `02be235-dirty`
- **Quando:** 2026-09-03 17:23:28
- **Bancada:** B->A. B (Windows): caixa Bluetooth AL-667 ~60% volume. A (Linux): mic interno Mic1/Dmic0, dev PortAudio 26, Dmic0 45 (-5 dB), Capture 39 (+12 dB). Serial /dev/ttyUSB0 so controle.
- **Camada:** mary, FEC rate 1/3 x2
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 1.0
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Direcao:** B -> A (B transmite, A grava)
- **Entrada / saida:** entrada `26` (Mic1 de A) / saida: caixa Bluetooth de B
- **Payload:** 48 bytes aleatorios do alfabeto imprimivel, 3 trials por ponto
- **Trials:** 6 gravacoes

Teste 11 da campanha: nibble como 3 tons (marychord on) contra o padrao de 1 tom, gravado no mesmo par de minutos para o controle e o tratamento.

## Resultado

| gravacao | ganho | rep | bytes | bits | bloco | pico | rms |
|---|---|---|---|---|---|---|---|
| `20260903-172116-chord-off-B2A` | 1.0 | 2 | 48 | 95.78% | OK | 0.20 | 0.034 |
| `20260903-172127-chord-off-B2A` | 1.0 | 2 | 48 | 96.42% | OK | 0.21 | 0.036 |
| `20260903-172137-chord-off-B2A` | 1.0 | 2 | 48 | 95.95% | OK | 0.23 | 0.038 |
| `20260903-172213-chord-on-B2A` | 1.0 | 2 | 48 | 96.71% | OK | 0.11 | 0.023 |
| `20260903-172224-chord-on-B2A` | 1.0 | 2 | 48 | 93.50% | OK | 0.10 | 0.022 |
| `20260903-172234-chord-on-B2A` | 1.0 | 2 | 48 | 84.23% | nao | 0.11 | 0.024 |

Media de bits certos: 93.76%. Blocos inteiros: 5 de 6.

## Leitura principal

**O acorde nao se paga, e a razao esta no nivel recebido.** Com o mesmo ganho
digital (1.0) e a mesma caixa, o nibble em 3 tons chegou a rms 0,022-0,024 e
pico 0,10-0,11, contra rms 0,034-0,039 e pico 0,20-0,23 do tom unico -- uma
queda de cerca de 4,3 dB, coerente com dividir a amplitude por tres. E
exatamente a potencia que a camada M-aria existe para nao dividir.

Nos bits, no relogio travado no melhor offset (regua do `align.py`):

| condicao | bits certos (relogio travado) | blocos inteiros |
|---|---|---|
| `marychord off` (1 tom, padrao) | 96,6% | 3 de 3 |
| `marychord on` (3 tons) | 95,4% | 2 de 3 |

E pelo gate early/late, como o link roda hoje:

| condicao | bits certos (gate) | blocos inteiros |
|---|---|---|
| `marychord off` | 96,1% | 3 de 3 |
| `marychord on` | 91,5% | 2 de 3 |

A distorcao medida pelo `bench.py` acompanha: energia entre os tons a -4,9/-5,1 dB
com um tom, e -8,5/-9,0 dB com tres. Em termos absolutos o acorde suja menos --
mas so porque tudo desceu junto; o excesso sobre o esperado cai de +3,3 dB para
-0,5 dB, ou seja, o acorde nao introduziu intermodulacao nova nesta cadeia. O que
ele custou foi nivel.

**Veredito: pior, como previsto, e por pouco.** Um ponto de bits no relogio
travado, quatro pontos e meio no gate, um bloco a menos em tres. Nao ha motivo
para ligar `marychord` nesta bancada. O numero existe agora para que a decisao
seja medida e nao suposta.

## Ressalvas

- **Tres gravacoes por ponto nao resolvem um bloco.** 3/3 contra 2/3 esta dentro
  do ruido; o numero que sustenta o veredito e o de bits, nao o de blocos. Ver a
  gravacao `172234`, que leu 94,6% dos bits com o relogio travado e 84,2% com o
  gate -- o bloco que se perdeu foi um colapso de sincronismo, nao canal.
- **`acerto_bits` no `resultado.csv` e a regua do gate**, isto e, o LLR sai do
  demodulador com a correcao early/late ligada e so o *deslizamento de bit* e
  forcado. Os numeros de "relogio travado" acima vem do `align.py`, que
  re-demodula com `steer=False` em cada offset de amostra. As duas reguas nao
  sao intercambiaveis; cada tabela acima diz qual usou.
- **Controle e tratamento foram gravados com 1 minuto de diferenca**, de
  proposito: e a comparacao pareada mais proxima que esta bancada permite sem
  intercalar trial a trial.
- Commit anotado como `02be235-dirty`: a arvore tinha as pastas de resultado nao
  commitadas e uma correcao no `capture.py` (ver abaixo). O codigo de DSP
  (`modem.py`, `fec.py`) esta em `02be235` intacto.
- **Correcao feita antes deste teste:** o `capture.py` so *ligava*
  `marychord`/`mfskgroup` e nunca desligava, entao o ajuste ficava grudado no
  agent e o teste seguinte gravaria com acorde ligado enquanto o proprio JSON
  diria `chord: false`. Agora ele manda `marygap`, `maryband`, `marychord` e
  `mfskgroup` explicitos em toda rodada. As gravacoes `chord-off` deste teste
  foram feitas antes da correcao, mas o agent estava em `off` de fabrica -- nenhum
  teste com acorde tinha rodado ainda nesta sessao.


## Como ler

`acerto_bits` e medido no melhor deslizamento por forca bruta, sempre,
e nunca na posicao que o `find_sync` escolheu -- misturar as duas reguas
faz as falhas pontuarem mais alto que os acertos. `bloco_ok` e o numero
honesto separado: passa pelo caminho FEC de verdade (sync por correlacao,
Viterbi soft, comparacao dos bytes) e e o que o enlace de fato entregou.
Com poucas gravacoes ele e ruidoso; nao ajuste parametro por ele.

`llr/*.csv` tem uma linha por simbolo. Em M-aria sao quatro colunas,
porque sao quatro bits por simbolo: o tamanho do vetor soft nao e uma
contagem de simbolos.

## Arquivos

- `gravacao/` -- wav 32-bit float + json, formato de `recording.py`
- `llr/` -- saida soft do demodulador, uma linha por simbolo
- `bits/` -- bits lidos contra bits transmitidos, alinhados
- `figuras/` -- espectrograma por gravacao
- `resultado.csv` -- uma linha por gravacao
