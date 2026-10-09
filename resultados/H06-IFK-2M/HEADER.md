# H06-IFK-2M

- **Codigo:** commit `4dc7e4e-dirty`
- **Quando:** 2026-10-08 22:28:24
- **Bancada:** B Windows alto-falante Realtek P2 sem aprimoramentos, 200 cm do mic e apontado -> A mic interno (dispositivo padrao, Mic1) Dmic0 45 Capture 39, tunel SSH, commit 4dc7e4e
- **Camada:** mary, FEC rate 1/3 x1
- **Amostragem:** 48000 Hz, 100 baud
- **Ganho de transmissao:** 0.5
- **Bloco:** 48 bytes de payload
- **Canal:** duas maquinas
- **Entrada / saida:** `?` / `?`
- **Trials:** 1 gravacoes

## Resultado

| gravacao | ganho | rep | bytes | sincronismo | bits | bloco | bits gate | bloco gate | pico | rms |
|---|---|---|---|---|---|---|---|---|---|---|
| `20261008-222821-h06-ifk-r4` | 0.5 | 1 | 48 | duas varreduras | 81.52% | nao | 82.01% | nao | 0.11 | 0.016 |

Media de bits certos: 81.52%. Blocos inteiros: 0 de 1.
So o gate, nas 1 gravacoes com varredura: 82.01% de bits, 0 de 1 blocos.

## Como ler

`acerto_bits` e medido no melhor deslizamento por forca bruta, sempre,
e nunca na posicao que o `find_sync` escolheu -- misturar as duas reguas
faz as falhas pontuarem mais alto que os acertos. `bloco_ok` e o numero
honesto separado: passa pelo caminho FEC de verdade (sync por correlacao,
Viterbi soft, comparacao dos bytes) e e o que o enlace de fato entregou.
Com poucas gravacoes ele e ruidoso; nao ajuste parametro por ele.

**Duas reguas de sincronismo.** Nas gravacoes com `sync_chirp`,
`acerto_bits` e `bloco_ok` saem do audio relido como o receptor ao
vivo o rele (`modem.sweep_soft`, o mesmo de `console.py`): relogio
congelado, inicio na varredura de abertura e periodo medido entre as
duas (`sincronismo` = duas varreduras). Se o par nao serve, so a de
abertura com relogio nominal (uma varredura); se nenhuma aparece, o
gate, e a coluna diz. `acerto_bits_gate` e `bloco_ok_gate` sao a
leitura pelo gate early/late, como esta ferramenta fazia antes --
pessimista nessas gravacoes, porque o gate toma a varredura pelos
primeiros simbolos do preambulo. Gravacoes sem varredura so tem a
regua do gate, nas colunas sem sufixo. `span_simbolos` e o vao entre
as varreduras calculado como o receptor calcula (`fec.sweep_span`);
`span_json` e o que o gravador carimbou, so para conferencia.
`llr/` e `bits/` saem da regua principal.

`llr/*.csv` tem uma linha por simbolo. Em M-aria sao quatro colunas,
porque sao quatro bits por simbolo: o tamanho do vetor soft nao e uma
contagem de simbolos.

## Arquivos

- `gravacao/` -- wav 32-bit float + json, formato de `recording.py`
- `llr/` -- saida soft do demodulador, uma linha por simbolo
- `bits/` -- bits lidos contra bits transmitidos, alinhados
- `figuras/` -- espectrograma por gravacao
- `resultado.csv` -- uma linha por gravacao

## Leitura (2026-10-08)

IFK pareado, 16-FSK com varreduras, ~2 m, 4 pares em ordem alternada. Bits com IFK / sem: 84,35/77,60 (+6,8), 82,93/80,60 (+2,3), 81,43/81,52 (-0,1), 81,52/81,10 (+0,4). IFK a favor em 3 de 4, media +2,4 pontos; nenhum bloco fecha em nenhum dos dois. O canal estava pior que nas gravacoes de 2 m de H04-4MODOS-200CM uma hora antes (pico 0,09-0,11 contra 0,14-0,15; 16-FSK sem IFK 77,6-81,5% contra 87-90%): posicao ou sala mudou, verificar com o usuario.
